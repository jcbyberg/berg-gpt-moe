"""
LanceDB cold memory management with IVF-PQ and reranking.

Serves as long-term archival storage.
"""

import lancedb
from lancedb.rerankers import CrossEncoderReranker
from orchestrator.config import get_settings
from orchestrator.utils.logging import logger
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class ColdMemoryManager:
    """
    Manages LanceDB cold memory with IVF-PQ and CrossEncoder reranking.
    
    Archives high-value findings from hot memory for long-term storage.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db: Optional[lancedb.DBConnection] = None
        self.table: Optional[lancedb.table] = None
        self.reranker: Optional[CrossEncoderReranker] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize LanceDB with IVF-PQ index and reranker."""
        logger.info("Initializing Cold Memory (LanceDB)...")
        
        self.db = await lancedb.connect_async(self.settings.lancedb_path)
        
        # Check if table exists, create if not
        existing_tables = await self.db.table_names()
        
        if "archived_knowledge" not in existing_tables:
            logger.info("Creating new archived_knowledge table...")
            
            # Create table with schema
            import pyarrow as pa
            
            # Define schema
            schema = pa.schema([
                pa.field("agent_id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("timestamp", pa.int64()),
                pa.field("data_type", pa.string()),
                pa.field("metadata", pa.string()),
                pa.field("embedding", pa.list_(pa.float32(), list_size=768)),
            ])
            
            self.table = await self.db.create_table("archived_knowledge", schema=schema)
            
            # Create IVF-PQ vector index for compressed storage
            await self.table.create_index(
                "embedding",
                config=lancedb.index.IvfPq(
                    num_partitions=self.settings.lancedb_num_partitions,
                    num_sub_vectors=self.settings.lancedb_num_sub_vectors,
                    distance_type="cosine"
                )
            )
            
            # Create BTree index for timestamp-based queries
            await self.table.create_index("timestamp", config=lancedb.index.BTree())
            
            # Initialize Cross-Encoder reranker
            try:
                self.reranker = lancedb.rerankers.cross_encoder.CrossEncoderReranker(
                    model=self.settings.lancedb_reranker_model
                )
                logger.info("Cross-Encoder reranker initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Cross-Encoder reranker: {e}")
                self.reranker = None
            
            logger.info("Cold Memory initialized successfully (new table)")
        else:
            logger.info("Opening existing archived_knowledge table...")
            self.table = await self.db.open_table("archived_knowledge")
            
            # Check if indices exist
            indices = await self.table.list_indices()
            logger.info(f"Existing indices: {[i['name'] for i in indices]}")
            
            # Try to initialize reranker if not already done
            if not self.reranker:
                try:
                    self.reranker = lancedb.rerankers.cross_encoder.CrossEncoderReranker(
                        model=self.settings.lancedb_reranker_model
                    )
                    logger.info("Cross-Encoder reranker initialized (existing table)")
                except Exception as e:
                    logger.warning(f"Could not initialize Cross-Encoder reranker: {e}")
                    self.reranker = None
    
    async def archive(
        self,
        entries: List[Dict[str, Any]]
    ) -> int:
        """Archive entries from hot memory to cold storage."""
        if not entries:
            return 0
        
        # Prepare data for LanceDB
        import pyarrow as pa
        
        # Parse metadata from JSON string to dict
        for entry in entries:
            if isinstance(entry.get("metadata"), str):
                try:
                    entry["metadata"] = json.loads(entry["metadata"])
                except json.JSONDecodeError:
                    entry["metadata"] = {}
        
        data = {
            "agent_id": pa.array([e["agent_id"] for e in entries]),
            "content": pa.array([e["content"] for e in entries]),
            "timestamp": pa.array([e["timestamp"] for e in entries]),
            "data_type": pa.array([e.get("data_type", "thought") for e in entries]),
            "metadata": pa.array([json.dumps(e.get("metadata", {}), ensure_ascii=False) for e in entries]),
            "embedding": pa.array([e["embedding"] for e in entries]),
        }
        
        async with self._lock:
            await self.table.add(data)
        
        logger.info(f"Archived {len(entries)} entries to cold memory")
        return len(entries)
    
    async def search(
        self,
        query_vector: List[float],
        num_results: int = 10,
        agent_filter: Optional[str] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """Perform semantic search in cold memory with optional reranking."""
        # Build query
        query = self.table.search(query_vector)
        
        # Apply filters
        if agent_filter:
            query = query.where(f"agent_id == '{agent_filter}'")
        
        # Fetch more results for reranking
        limit = num_results * 2 if rerank else num_results
        query = query.limit(limit)
        
        # Execute search
        results = await query.to_pandas()
        
        if rerank and self.reranker and len(results) > 0:
            # Apply cross-encoder reranking
            # Create a pseudo-query from content
            query_text = " ".join(results["content"].tolist()[:5])
            reranked_results = query.rerank(self.reranker, query=query_text)
            results = reranked_results.to_pandas()
        
        # Convert to dict format
        return results.to_dict("records")[:num_results]
    
    async def get_by_agent(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve archived entries for a specific agent."""
        results = (
            await self.table.search([0.0] * 768)  # Dummy vector
            .where(f"agent_id == '{agent_id}'")
            .limit(limit)
            .to_pandas()
        )
        
        entries = []
        for _, row in results.iterrows():
            entry = {
                "agent_id": row["agent_id"],
                "content": row["content"],
                "timestamp": int(row["timestamp"]),
                "data_type": row["data_type"],
                "metadata": row.get("metadata", "{}"),
            }
            try:
                entry["metadata"] = json.loads(entry["metadata"])
            except json.JSONDecodeError:
                pass
            
            entries.append(entry)
        
        return entries
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cold memory statistics."""
        if not self.table:
            return {}
        
        return {
            "total_rows": len(await self.table.to_pandas()),
            "indices": await self.table.list_indices(),
            "index_stats": await self.table.index_stats("embedding") if self.table else {}
        }
    
    async def optimize_indices(self) -> None:
        """Optimize vector indices for better performance."""
        if not self.table:
            return
        
        logger.info("Optimizing LanceDB indices...")
        
        indices = await self.table.list_indices()
        for idx in indices:
            if idx["name"] == "embedding_idx":
                logger.info(f"Prewarming index: {idx['name']}")
                await self.table.prewarm_index(idx["name"])
        
        logger.info("Index optimization complete")

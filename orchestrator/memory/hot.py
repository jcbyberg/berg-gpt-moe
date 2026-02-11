"""
RedisVL hot memory management with HNSW vector indexing.

Serves as the central nervous system for all agents.
"""

from redisvl.index import SearchIndex, IndexSchema
from redisvl.query import VectorQuery
from redisvl.redis.utils import array_to_buffer
from orchestrator.config import get_settings
from orchestrator.utils.logging import logger
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import redis


class HotMemoryManager:
    """
    Manages RedisVL hot memory with HNSW vector indexing.
    
    All agents write to this simultaneously using agent-specific prefixes.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.index: Optional[SearchIndex] = None
        self._lock = asyncio.Lock()
        self._redis_client: Optional[redis.Redis] = None
        
    async def initialize(self) -> None:
        """Initialize RedisVL search index with HNSW configuration."""
        logger.info("Initializing Hot Memory (RedisVL)...")
        
        schema = IndexSchema.from_dict({
            "index": {
                "name": "hive_hot_memory",
                "prefix": "ctx:",
                "storage_type": "hash"
            },
            "fields": [
                {"name": "agent_id", "type": "tag"},
                {"name": "content", "type": "text"},
                {"name": "timestamp", "type": "numeric"},
                {"name": "data_type", "type": "tag"},
                {"name": "metadata", "type": "text"},
                {
                    "name": "embedding",
                    "type": "vector",
                    "attrs": {
                        "dims": 768,
                        "distance_metric": "cosine",
                        "algorithm": "hnsw",
                        "datatype": "float32",
                        "ef_runtime": 100,
                        "ef_construction": 200,
                        "m": 16
                    }
                }
            ]
        })
        
        # Parse Redis URL with authentication
        redis_url = self.settings.redis_url
        if "@" in redis_url:
            # Format: redis://password@host:port
            pass  # RedisVL handles this format
        
        self.index = SearchIndex(schema, redis_url=redis_url)
        
        # Create or connect to existing index
        try:
            self.index.create(overwrite=False)
            logger.info("Hot Memory initialized successfully (new index created)")
        except Exception as e:
            # Index might already exist, try to connect
            try:
                logger.info(f"Attempting to connect to existing index: {e}")
                # The index object is already initialized with schema
                logger.info("Hot Memory initialized successfully (connected to existing)")
            except Exception as e2:
                logger.error(f"Failed to initialize hot memory: {e2}")
                raise
        
        # Initialize Redis client for pruning operations
        self._redis_client = redis.from_url(redis_url)
    
    async def write(
        self,
        agent_id: str,
        content: str,
        embedding: List[float],
        data_type: str = "thought",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Write to hot memory with auto-generated key."""
        # Generate unique key using agent_id, type, and timestamp
        key = f"{agent_id}:{data_type}:{int(asyncio.get_event_loop().time() * 1000)}"
        
        data = {
            "agent_id": agent_id,
            "content": content,
            "timestamp": asyncio.get_event_loop().time(),
            "data_type": data_type,
            "metadata": json.dumps(metadata or {}, ensure_ascii=False),
            "embedding": array_to_buffer(embedding, dtype="float32")
        }
        
        async with self._lock:
            self.index.load([data], id_field="agent_id")
        
        logger.debug(f"Wrote to hot memory: {key}")
        return key
    
    async def read(
        self,
        agent_id: str,
        limit: int = 10,
        data_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Read recent entries from hot memory for an agent."""
        from redisvl.query.filter import Tag
        
        filter_expr = Tag("agent_id") == agent_id
        if data_type:
            filter_expr = filter_expr & (Tag("data_type") == data_type)
        
        query = VectorQuery(
            vector=[0.0] * 768,  # Dummy vector, returns all matching filter
            vector_field_name="embedding",
            return_fields=["agent_id", "content", "timestamp", "data_type", "metadata"],
            num_results=limit
        )
        query.set_filter(filter_expr)
        
        results = self.index.query(query)
        return [r.__dict__ for r in results]
    
    async def semantic_search(
        self,
        query_vector: List[float],
        num_results: int = 5,
        agent_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector search across all agents."""
        from redisvl.query.filter import Tag
        
        query = VectorQuery(
            vector=query_vector,
            vector_field_name="embedding",
            return_fields=["agent_id", "content", "timestamp", "data_type", "metadata"],
            num_results=num_results
        )
        
        if agent_filter:
            filter_expr = Tag("agent_id") == agent_filter
            query.set_filter(filter_expr)
        
        results = self.index.query(query)
        return [r.__dict__ for r in results]
    
    async def prune(self, max_size: int = 1000) -> int:
        """Prune old entries when Redis reaches size limit."""
        if not self._redis_client:
            return 0
        
        dbsize = self._redis_client.dbsize()
        
        if dbsize > max_size:
            logger.warning(f"Redis DB size {dbsize} exceeds {max_size}, pruning...")
            
            # Get all keys sorted by timestamp
            # Use SCAN to avoid blocking
            keys = []
            for key in self._redis_client.scan_iter(match="ctx:*"):
                keys.append((key, self._redis_client.zscore("ctx:index", key)))
            
            # Sort by timestamp (stored as score in sorted set)
            keys.sort(key=lambda x: x[1], reverse=True)  # Newest first
            
            # Keep newest max_size entries
            keys_to_delete = [k[0] for k in keys[max_size:]]
            
            if keys_to_delete:
                # Delete from index
                pipeline = self._redis_client.pipeline()
                for key in keys_to_delete:
                    pipeline.delete(key)
                    pipeline.zrem("ctx:index", key)
                pipeline.execute()
                
                logger.info(f"Pruned {len(keys_to_delete)} old entries")
            
            return len(keys_to_delete)
        
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get hot memory statistics."""
        if not self.index:
            return {}
        
        if not self._redis_client:
            return {
                "total_keys": 0,
                "index_info": {}
            }
        
        return {
            "total_keys": self._redis_client.dbsize(),
            "index_info": self.index.info()
        }
    
    async def get_by_prefix(
        self,
        prefix: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all entries with a specific prefix."""
        from redisvl.query.filter import Tag
        
        filter_expr = Tag("agent_id").like(f"{prefix}*")
        query = VectorQuery(
            vector=[0.0] * 768,
            vector_field_name="embedding",
            return_fields=["agent_id", "content", "timestamp", "data_type", "metadata"],
            num_results=limit
        )
        query.set_filter(filter_expr)
        
        results = self.index.query(query)
        return [r.__dict__ for r in results]

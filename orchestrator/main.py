"""Main FastAPI application for Hive Mind orchestrator."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from contextvars import ContextVar
from orchestrator.config import get_settings
from orchestrator.memory.hot import HotMemoryManager
from orchestrator.memory.cold import ColdMemoryManager
from orchestrator.agents.registry import AgentRegistry
from orchestrator.agents.gardener import GardenerAgent
from orchestrator.utils.logging import configure_logging
from orchestrator.utils.metrics import MetricsTracker
from orchestrator.ai import gemini_client
from orchestrator.api import openai_router
from typing import Dict, Any, List
import asyncio
import structlog
import json

# Configure logging
logger = configure_logging()
settings = get_settings()

# Initialize FastAPI
app = FastAPI(
    title="Hive Mind Orchestrator",
    description="High-Frequency MoE Architecture for Massively Parallel Agent Orchestration",
    version="2.1.0"
)

app.include_router(openai_router)

# Request-scoped context
request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context")

# Global managers
hot_memory: HotMemoryManager = None
cold_memory: ColdMemoryManager = None
agent_registry: AgentRegistry = None
metrics_tracker: MetricsTracker = None
gardener: GardenerAgent = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Hive Mind Orchestrator",
        "version": "2.1.0",
        "status": "online",
        "ai_enabled": gemini_client._configured
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "hot_memory": hot_memory is not None,
            "cold_memory": cold_memory is not None,
            "agents": agent_registry is not None,
            "ai": gemini_client._configured
        }
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    return {
        "hot_memory": await hot_memory.get_stats() if hot_memory else {},
        "cold_memory": await cold_memory.get_stats() if cold_memory else {},
        "metrics": metrics_tracker.to_dict() if metrics_tracker else {}
    }


@app.get("/agents")
async def list_agents():
    """List all available agents."""
    if not agent_registry:
        return {"agents": []}
    
    return {
        "agents": [
            {
                "id": agent.config.id,
                "name": agent.config.name,
                "role": agent.config.role,
                "tools": agent.config.tools
            }
            for agent in agent_registry.get_all_agents()
        ]
    }


@app.post("/query")
async def dispatch_mission(query_request: Dict[str, Any]):
    """
    Execute mission: Plan -> Dispatch -> Synthesize.
    """
    query = query_request.get("query", "")
    force_agents = query_request.get("agents", None)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    logger.info(f"Received query: {query}")
    start_time = asyncio.get_event_loop().time()
    
    # 1. PLANNING PHASE
    selected_agents = []
    if force_agents:
        # User explicitly selected agents
        selected_agents = [
            agent_registry.get_agent(aid) for aid in force_agents 
            if agent_registry.get_agent(aid)
        ]
    else:
        # AI Planning
        try:
            available_agents = [
                {
                    "id": a.config.id, 
                    "role": a.config.role, 
                    "tools": a.config.tools
                } 
                for a in agent_registry.get_all_agents()
            ]
            
            planned_ids = await gemini_client.plan_mission(query, available_agents)
            logger.info(f"AI selected agents: {planned_ids}")
            
            selected_agents = [
                agent_registry.get_agent(aid) for aid in planned_ids
                if agent_registry.get_agent(aid)
            ]
        except Exception as e:
            logger.error(f"Planning failed: {e}. Falling back to Web Scout.")
            selected_agents = [agent_registry.get_agent("res_01_web")]

    if not selected_agents:
        raise HTTPException(status_code=500, detail="No agents selected or available")

    # 2. EXECUTION PHASE (Parallel)
    logger.info(f"Dispatching to {len(selected_agents)} agents...")
    tasks = [agent.process_task(query) for agent in selected_agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_results = []
    failed_results = []
    
    for i, result in enumerate(results):
        agent = selected_agents[i]
        if isinstance(result, Exception):
            logger.error(f"Agent {agent.config.name} failed: {result}")
            failed_results.append({"agent": agent.config.name, "error": str(result)})
        else:
            successful_results.append(result)
            # Async write to hot memory (fire and forget)
            asyncio.create_task(hot_memory.write(
                agent_id=agent.config.id,
                content=result.get("summary", ""),
                embedding=[0.0] * 768,
                data_type="agent_result",
                metadata=result
            ))

    # 3. SYNTHESIS PHASE
    final_answer = ""
    if successful_results:
        try:
            final_answer = await gemini_client.synthesize_results(query, successful_results)
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            final_answer = "Failed to synthesize results. See individual agent reports."
    else:
        final_answer = "All agents failed to retrieve information."

    total_duration = (asyncio.get_event_loop().time() - start_time) * 1000
    
    # Record metrics
    metrics_tracker.record_agent_execution(
        agent_id="orchestrator",
        task=query,
        duration_ms=total_duration,
        success=bool(successful_results)
    )

    return {
        "query": query,
        "plan": [a.config.id for a in selected_agents],
        "answer": final_answer,
        "duration_ms": total_duration,
        "agent_reports": successful_results,
        "failures": failed_results
    }


@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup."""
    global hot_memory, cold_memory, agent_registry, metrics_tracker, gardener
    
    logger.info("Starting Hive Mind Orchestrator (v2.1.0)...")
    
    try:
        metrics_tracker = MetricsTracker()
        
        # Initialize Memories
        hot_memory = HotMemoryManager()
        await hot_memory.initialize()
        
        cold_memory = ColdMemoryManager()
        await cold_memory.initialize()
        
        # Initialize Agents
        agent_registry = AgentRegistry(hot_memory)
        await agent_registry.initialize_all()
        
        # Initialize AI
        gemini_client.configure()
        
        # Start the Gardener
        gardener = GardenerAgent(hot_memory, cold_memory)
        await gardener.start()
        
        logger.info("Hive Mind is ONLINE")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Don't raise here to allow API to start for debugging, 
        # but health check will fail


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Hive Mind Orchestrator...")
    
    if gardener:
        await gardener.stop()
    
    if hot_memory:
        # Prune hot memory before shutdown
        pruned = await hot_memory.prune(max_size=settings.hot_memory_prune_size)
        logger.info(f"Pruned {pruned} entries from hot memory")
    
    if cold_memory:
        # Optimize indices before shutdown
        await cold_memory.optimize_indices()
        logger.info("Optimized cold memory indices")
    
    logger.info("Hive Mind Orchestrator shutdown complete")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level,
        reload=False  # Disable reload in production
    )

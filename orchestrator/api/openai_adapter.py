"""OpenAI-compatible API Adapter for Hive Mind."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from orchestrator.ai import gemini_client
from orchestrator.agents.registry import AgentRegistry
from orchestrator.memory.hot import HotMemoryManager
from orchestrator.config import get_settings
from orchestrator.utils.logging import logger
import asyncio
import json
import time
import uuid

router = APIRouter(prefix="/v1")

# --- OpenAI Schemas ---

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "hive-mind-v1"
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Dict[str, int]

# --- Adapter Implementation ---

async def get_hive_mind_components(request: Request):
    """Dependency to access global singletons from app state."""
    app = request.app
    # In a real app, use dependency injection properly. 
    # For now, accessing globals via imports in main is circular, so we access via app.state if we attached them,
    # or just import the singletons if they are truly global.
    # Since we defined them as globals in main.py, let's grab them from there safely.
    from orchestrator.main import agent_registry, hot_memory
    return agent_registry, hot_memory

@router.post("/chat/completions")
async def chat_completions(
    req: ChatCompletionRequest,
    request: Request
):
    """
    OpenAI-compatible endpoint that routes to Hive Mind.
    """
    # 1. Extract Query from Messages
    # We take the last user message as the active query
    query = next((m.content for m in reversed(req.messages) if m.role == "user"), None)
    
    if not query:
        raise HTTPException(status_code=400, detail="No user message found")

    # Extract system prompt for context
    system_prompt = next((m.content for m in req.messages if m.role == "system"), "")
    
    # 2. Setup Context
    request_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())
    
    # Get globals
    # Note: accessing protected/globals is a hack, usually we'd use app.state
    # We'll assume the registry is initialized.
    from orchestrator.main import agent_registry, hot_memory, metrics_tracker
    
    if not agent_registry:
        raise HTTPException(status_code=503, detail="Hive Mind initializing")

    logger.info(f"OpenAI Adapter received query: {query}")

    # 3. Handle Streaming Request
    if req.stream:
        return StreamingResponse(
            stream_hive_mind_response(query, system_prompt, agent_registry, hot_memory, request_id, created_time),
            media_type="text/event-stream"
        )

    # 4. Handle Standard Request
    try:
        # A. Planning
        available_agents = [
            {"id": a.config.id, "role": a.config.role, "tools": a.config.tools} 
            for a in agent_registry.get_all_agents()
        ]
        
        # Inject system prompt into planning query context
        planning_context = f"{system_prompt}\n\nTask: {query}" if system_prompt else query
        
        planned_ids = await gemini_client.plan_mission(planning_context, available_agents)
        selected_agents = [
            agent_registry.get_agent(aid) for aid in planned_ids
            if agent_registry.get_agent(aid)
        ]
        
        if not selected_agents:
            selected_agents = [agent_registry.get_agent("res_01_web")]

        # B. Execution
        tasks = [agent.process_task(query) for agent in selected_agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = []
        for i, res in enumerate(results):
            if not isinstance(res, Exception):
                successful_results.append(res)
                # Async write to hot memory
                asyncio.create_task(hot_memory.write(
                    agent_id=selected_agents[i].config.id,
                    content=res.get("summary", ""),
                    embedding=[0.0] * 768,
                    data_type="agent_result"
                ))

        # C. Synthesis
        if successful_results:
            final_answer = await gemini_client.synthesize_results(query, successful_results)
        else:
            final_answer = "I apologize, but my agent swarm failed to retrieve the necessary information."

        # D. Response
        return ChatCompletionResponse(
            id=request_id,
            created=created_time,
            model=req.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=final_answer),
                    finish_reason="stop"
                )
            ],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )

    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_hive_mind_response(
    query: str, 
    system_prompt: str,
    agent_registry: AgentRegistry,
    hot_memory: HotMemoryManager,
    request_id: str,
    created_time: int
):
    """Generator for OpenAI-compatible SSE stream."""
    
    model_name = "hive-mind-v1"
    
    def create_chunk(content: str, finish_reason: Optional[str] = None):
        return json.dumps({
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": model_name,
            "choices": [{
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason
            }]
        })

    try:
        # 1. Planning
        # Send a "thought" as content to let user know we are working
        yield f"data: {create_chunk('🐝 **Hive Mind Activated**\n\n')}\n\n"
        
        available_agents = [
            {"id": a.config.id, "role": a.config.role, "tools": a.config.tools} 
            for a in agent_registry.get_all_agents()
        ]
        
        yield f"data: {create_chunk('🧠 *Planning mission...* ')}\n\n"
        
        planning_context = f"{system_prompt}\n\nTask: {query}" if system_prompt else query
        planned_ids = await gemini_client.plan_mission(planning_context, available_agents)
        
        selected_agents = [
            agent_registry.get_agent(aid) for aid in planned_ids
            if agent_registry.get_agent(aid)
        ]
        
        agent_names = ", ".join([a.config.name for a in selected_agents])
        yield f"data: {create_chunk(f'Recruited: **{agent_names}**\n\n')}\n\n"

        # 2. Execution
        tasks = {}
        for agent in selected_agents:
            tasks[agent.config.id] = asyncio.create_task(agent.process_task(query))
            
        completed_count = 0
        results = []
        
        # We need to wait for all, but we can report progress
        # Since we can't easily stream partial progress from inside the gather without a callback,
        # we'll wait for them individually or in a group.
        # Ideally, we'd use asyncio.as_completed, but we need to map back to agent IDs.
        
        pending = list(tasks.values())
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                # Find which agent this was
                for aid, t in tasks.items():
                    if t == task:
                        try:
                            res = await task
                            if isinstance(res, Exception):
                                yield f"data: {create_chunk(f'❌ *{aid} failed*\n')}\n\n"
                            else:
                                results.append(res)
                                yield f"data: {create_chunk(f'✅ *{aid} returned results*\n')}\n\n"
                                
                                # Write to memory
                                asyncio.create_task(hot_memory.write(
                                    agent_id=aid,
                                    content=res.get("summary", ""),
                                    embedding=[0.0] * 768,
                                    data_type="agent_result"
                                ))
                        except Exception as e:
                            yield f"data: {create_chunk(f'❌ *{aid} error: {str(e)}*\n')}\n\n"
        
        # 3. Synthesis
        yield f"data: {create_chunk('\nAvailable data collected. 🧪 *Synthesizing final answer...*\n\n---\n\n')}\n\n"
        
        if results:
            final_answer = await gemini_client.synthesize_results(query, results)
            # Gemini returns full text, but we should stream it if we could. 
            # Our current Gemini wrapper returns string. 
            # For a better experience, we'd make synthesize_results return a stream.
            # For now, we simulate streaming the block to avoid a huge burst.
            
            chunk_size = 50
            for i in range(0, len(final_answer), chunk_size):
                chunk = final_answer[i:i+chunk_size]
                yield f"data: {create_chunk(chunk)}\n\n"
                await asyncio.sleep(0.02) # Slight delay for effect
                
        else:
            yield f"data: {create_chunk('Mission failed. No data retrieved.')}\n\n"

        yield f"data: {create_chunk('', finish_reason='stop')}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {create_chunk(f'Error: {str(e)}')}\n\n"
        yield "data: [DONE]\n\n"
"""Web Scout Agent."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
from orchestrator.config import get_settings
from tavily import TavilyClient
import asyncio

logger = structlog.get_logger(__name__)


class WebScoutAgent(MCPAgent):
    """
    Web Scout - Uses Tavily API for web search.
    Tools: tavily_search
    """
    
    def __init__(self, config, hot_memory):
        super().__init__(config, hot_memory)
        settings = get_settings()
        # Initialize Tavily client if key is present
        self.tavily = None
        if settings.tavily_api_key:
             self.tavily = TavilyClient(api_key=settings.tavily_api_key)
        else:
            logger.warning("Tavily API key not found. Web Scout will fail.")

    async def process_task(self, task: str) -> Dict[str, Any]:
        """Process a web search task."""
        logger.info(f"Web Scout searching: {task}")
        
        if not self.tavily:
             return {
                "agent": self.config.name,
                "task": task,
                "error": "Tavily API key missing",
                "summary": "Could not search web (config error)"
            }

        # Wrap in generic call_tool to handle retries/memory
        # We pass the actual implementation as a lambda/function if using real client
        # But here MCPAgent.call_tool expects a tool name.
        
        # We override the _execute_tool method (see below) or just call generic method
        # For now, let's use the pattern of "call_tool" executing the logic.
        
        try:
            # We bypass call_tool's simulation and call directly, 
            # then write to memory manually to keep it clean.
            # OR we update base.py to allow registering real tool handlers.
            
            # Let's execute directly for now to prove integration
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.tavily.search(
                    query=task,
                    search_depth="advanced",
                    max_results=5,
                    include_raw_content=True
                )
            )
            
            summary = "\n".join([f"- {r['title']}: {r['content'][:200]}..." for r in response.get('results', [])])
            
            # Write to memory
            await self._write_to_memory(
                tool_name="tavily_search",
                args={"query": task},
                result=response
            )
            
            return {
                "agent": self.config.name,
                "task": task,
                "result": response,
                "summary": f"Found {len(response.get('results', []))} web results:\n{summary}"
            }
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Search failed: {e}"
            }

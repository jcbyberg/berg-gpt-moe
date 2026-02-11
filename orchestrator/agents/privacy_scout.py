"""Privacy Scout Agent (DuckDuckGo)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
from duckduckgo_search import DDGS
import asyncio

logger = structlog.get_logger(__name__)

class PrivacyScoutAgent(MCPAgent):
    """
    Privacy Scout - Uses DuckDuckGo for private/alternative search.
    Tools: ddg_search
    """
    
    async def process_task(self, task: str) -> Dict[str, Any]:
        """Search privately using DuckDuckGo."""
        logger.info(f"Privacy Scout searching: {task}")
        
        try:
            loop = asyncio.get_event_loop()
            
            def execute_search():
                with DDGS() as ddgs:
                    return list(ddgs.text(task, max_results=10))
            
            results = await loop.run_in_executor(None, execute_search)
            
            summary_text = "\n".join([f"- {r['title']}: {r['body'][:150]}..." for r in results[:5]])
            
            # Write to memory
            await self._write_to_memory(
                tool_name="ddg_search",
                args={"query": task},
                result=results
            )
            
            return {
                "agent": self.config.name,
                "task": task,
                "result": results,
                "summary": f"Found {len(results)} private results:\n{summary_text}"
            }
            
        except Exception as e:
            logger.error(f"DDG search failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Private search failed: {e}"
            }

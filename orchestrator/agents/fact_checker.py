"""The Fact Checker Agent (Wikipedia)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
import wikipedia
import asyncio

logger = structlog.get_logger(__name__)

class TheFactCheckerAgent(MCPAgent):
    """
    The Fact Checker - Uses Wikipedia API for verification.
    Tools: wikipedia_search, wikipedia_summary
    """
    
    async def process_task(self, task: str) -> Dict[str, Any]:
        """Verify facts using Wikipedia."""
        logger.info(f"Fact Checker verifying: {task}")
        
        try:
            # 1. Search for pages
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None, lambda: wikipedia.search(task, results=3)
            )
            
            if not search_results:
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": [],
                    "summary": "No Wikipedia pages found."
                }
            
            # 2. Get summary of best match
            page_title = search_results[0]
            try:
                summary = await loop.run_in_executor(
                    None, lambda: wikipedia.summary(page_title, sentences=5)
                )
                url = await loop.run_in_executor(
                    None, lambda: wikipedia.page(page_title).url
                )
            except wikipedia.DisambiguationError as e:
                # Handle disambiguation by picking first option
                page_title = e.options[0]
                summary = await loop.run_in_executor(
                    None, lambda: wikipedia.summary(page_title, sentences=5)
                )
                url = f"https://en.wikipedia.org/wiki/{page_title}"
            
            result_data = {
                "title": page_title,
                "url": url,
                "summary": summary,
                "related": search_results[1:]
            }
            
            # Write to memory
            await self._write_to_memory(
                tool_name="wikipedia",
                args={"query": task},
                result=result_data
            )
            
            return {
                "agent": self.config.name,
                "task": task,
                "result": result_data,
                "summary": f"Wikipedia ({page_title}): {summary}"
            }
            
        except Exception as e:
            logger.error(f"Wikipedia check failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Fact check failed: {e}"
            }

"""The Fixer Agent (StackExchange)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
import httpx
import html

logger = structlog.get_logger(__name__)

class TheFixerAgent(MCPAgent):
    """
    The Fixer - Searches StackOverflow for debugging help.
    Tools: stackoverflow_search
    """
    
    async def process_task(self, task: str) -> Dict[str, Any]:
        """Find solutions on StackOverflow."""
        logger.info(f"The Fixer debugging: {task}")
        
        try:
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                "order": "desc",
                "sort": "relevance",
                "q": task,
                "site": "stackoverflow",
                "filter": "withbody",  # Get body content
                "pagesize": 5
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()
                
                items = data.get("items", [])
                
                solutions = []
                for item in items:
                    title = html.unescape(item.get("title", ""))
                    link = item.get("link")
                    is_answered = item.get("is_answered")
                    solutions.append({
                        "title": title,
                        "link": link,
                        "is_answered": is_answered,
                        "tags": item.get("tags", [])
                    })
                
                summary_text = "\n".join([
                    f"- [{'SOLVED' if s['is_answered'] else 'OPEN'}] {s['title']}: {s['link']}" 
                    for s in solutions
                ])
                
                await self._write_to_memory(
                    tool_name="stackoverflow_search",
                    args={"query": task},
                    result=solutions
                )
                
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": solutions,
                    "summary": f"Found {len(solutions)} StackOverflow discussions:\n{summary_text}"
                }
                
        except Exception as e:
            logger.error(f"Fixer failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Debugging failed: {e}"
            }

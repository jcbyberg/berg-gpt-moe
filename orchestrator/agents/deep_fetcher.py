"""Deep Fetcher Agent (HTTP + BS4)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import asyncio

logger = structlog.get_logger(__name__)

class DeepFetcherAgent(MCPAgent):
    """
    Deep Fetcher - Scrapes and extracts content from websites.
    Tools: fetch_url, deep_search
    """
    
    async def process_task(self, task: str) -> Dict[str, Any]:
        """Deep dive into web content."""
        logger.info(f"Deep Fetcher processing: {task}")
        
        try:
            # 1. Find a target URL (if task is a query) or use URL directly
            target_url = task if task.startswith("http") else None
            
            if not target_url:
                # Search for a good candidate
                loop = asyncio.get_event_loop()
                def find_url():
                    with DDGS() as ddgs:
                        results = list(ddgs.text(task, max_results=1))
                        return results[0]['href'] if results else None
                target_url = await loop.run_in_executor(None, find_url)
            
            if not target_url:
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": [],
                    "summary": "No target URL found."
                }
            
            # 2. Fetch and Parse
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                response = await client.get(target_url)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script/style
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                
                # Clean lines
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                
                summary_text = clean_text[:1000] + "..."
                
                result_data = {
                    "url": target_url,
                    "title": soup.title.string if soup.title else "No Title",
                    "content": clean_text
                }
                
                await self._write_to_memory(
                    tool_name="fetch_url",
                    args={"url": target_url},
                    result=result_data
                )
                
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": result_data,
                    "summary": f"Extracted content from {target_url}:\n{summary_text}"
                }
                
        except Exception as e:
            logger.error(f"Deep fetch failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Deep fetch failed: {e}"
            }

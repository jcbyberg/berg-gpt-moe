"""The Scholar Agent (ArXiv)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
import arxiv
import asyncio

logger = structlog.get_logger(__name__)

class TheScholarAgent(MCPAgent):
    """
    The Scholar - Uses ArXiv API for academic research.
    Tools: arxiv_search
    """
    
    async def process_task(self, task: str) -> Dict[str, Any]:
        """Search academic papers."""
        logger.info(f"The Scholar researching: {task}")
        
        try:
            # Construct client
            client = arxiv.Client()
            
            search = arxiv.Search(
                query=task,
                max_results=5,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            # Execute search (generator)
            loop = asyncio.get_event_loop()
            
            def execute_search():
                return list(client.results(search))
            
            results = await loop.run_in_executor(None, execute_search)
            
            papers = []
            for r in results:
                papers.append({
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "summary": r.summary,
                    "url": r.pdf_url,
                    "published": str(r.published)
                })
            
            summary_text = "\n".join([f"- {p['title']} ({p['published'][:4]}): {p['summary'][:150]}..." for p in papers])
            
            # Write to memory
            await self._write_to_memory(
                tool_name="arxiv_search",
                args={"query": task},
                result=papers
            )
            
            return {
                "agent": self.config.name,
                "task": task,
                "result": papers,
                "summary": f"Found {len(papers)} papers:\n{summary_text}"
            }
            
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Research failed: {e}"
            }

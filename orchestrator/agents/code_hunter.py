"""Code Hunter Agent."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
from orchestrator.config import get_settings
import httpx
import structlog

logger = structlog.get_logger(__name__)


class CodeHunterAgent(MCPAgent):
    """
    Code Hunter - Uses GitHub API for code search.
    Tools: github_search_code, github_search_repos
    """
    
    def __init__(self, config, hot_memory):
        super().__init__(config, hot_memory)
        self.token = get_settings().github_token

    async def process_task(self, task: str) -> Dict[str, Any]:
        """Process a code search task."""
        logger.info(f"Code Hunter searching: {task}")
        
        if not self.token:
             return {
                "agent": self.config.name,
                "task": task,
                "error": "GitHub Token missing",
                "summary": "Could not search code (config error)"
            }
            
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Determine if searching for code or repos
        is_repo_search = "repository" in task.lower() or "repo" in task.lower()
        endpoint = "https://api.github.com/search/repositories" if is_repo_search else "https://api.github.com/search/code"
        
        # Construct query (ensure 'q=' param)
        # GitHub code search requires a user, org, or repo qualifier, or global search might fail/be limited
        # For this example, we'll just send the raw task as q
        params = {"q": task, "per_page": 5}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=headers, params=params)
                
                if response.status_code != 200:
                    raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
                
                data = response.json()
                items = data.get("items", [])
                
                summary_lines = []
                for item in items:
                    name = item.get("full_name") or item.get("name")
                    url = item.get("html_url")
                    desc = item.get("description", "") or "No description"
                    summary_lines.append(f"- [{name}]({url}): {desc}")
                
                summary = "\n".join(summary_lines)
                
                # Write to memory
                await self._write_to_memory(
                    tool_name="github_search",
                    args={"query": task},
                    result=data
                )
                
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": data,
                    "summary": f"Found {len(items)} GitHub results:\n{summary}"
                }
                
        except Exception as e:
            logger.error(f"GitHub search failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Search failed: {e}"
            }

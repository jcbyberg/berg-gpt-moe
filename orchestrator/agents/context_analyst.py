"""Context Analyst Agent (Filesystem)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
import os
import glob

logger = structlog.get_logger(__name__)

class ContextAnalystAgent(MCPAgent):
    """
    Context Analyst - Reads local project files securely.
    Tools: list_files, read_file
    """
    
    def __init__(self, config, hot_memory):
        super().__init__(config, hot_memory)
        # Restrict access to /data volume
        self.root_dir = "/data" 

    async def process_task(self, task: str) -> Dict[str, Any]:
        """Analyze local context files."""
        logger.info(f"Context Analyst checking: {task}")
        
        try:
            # Simple heuristic: if task mentions a file extension, list files
            # In a real system, we'd use LLM to parse intent (read vs list)
            
            found_files = []
            
            # Walk directory (safe mode)
            # In production, this needs robust path validation to prevent traversal attacks
            for root, dirs, files in os.walk(self.root_dir):
                for file in files:
                    if task.lower() in file.lower() or any(ext in task for ext in [".py", ".json", ".md", ".txt"]):
                        found_files.append(os.path.join(root, file))
            
            # Read first match if specific
            content_preview = ""
            if len(found_files) == 1:
                try:
                    with open(found_files[0], 'r') as f:
                        content = f.read(2000) # Read first 2KB
                        content_preview = f"\nContent of {found_files[0]}:\n{content}..."
                except Exception:
                    content_preview = " (Binary or unreadable)"
            
            result_data = {
                "files_found": found_files,
                "root": self.root_dir
            }
            
            await self._write_to_memory(
                tool_name="filesystem_search",
                args={"query": task},
                result=result_data
            )
            
            return {
                "agent": self.config.name,
                "task": task,
                "result": result_data,
                "summary": f"Found {len(found_files)} local files matching context.{content_preview}"
            }
            
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Context analysis failed: {e}"
            }

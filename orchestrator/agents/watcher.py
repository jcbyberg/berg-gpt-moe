"""The Watcher Agent (YouTube)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
from youtube_transcript_api import YouTubeTranscriptApi
from duckduckgo_search import DDGS
import asyncio
import re

logger = structlog.get_logger(__name__)

class TheWatcherAgent(MCPAgent):
    """
    The Watcher - Finds YouTube videos and extracts transcripts.
    Tools: youtube_search, youtube_transcript
    """
    
    async def process_task(self, task: str) -> Dict[str, Any]:
        """Find video content and analyze it."""
        logger.info(f"The Watcher watching: {task}")
        
        try:
            # 1. Search for video ID using DDG (avoiding YouTube API key complexity)
            loop = asyncio.get_event_loop()
            
            def find_video_id():
                with DDGS() as ddgs:
                    # Specific site search
                    results = list(ddgs.text(f"site:youtube.com {task}", max_results=5))
                    for res in results:
                        # Extract ID from URL
                        match = re.search(r"v=([a-zA-Z0-9_-]{11})", res['href'])
                        if match:
                            return match.group(1), res['title']
                return None, None
            
            video_id, title = await loop.run_in_executor(None, find_video_id)
            
            if not video_id:
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": [],
                    "summary": "No relevant videos found."
                }
            
            # 2. Get Transcript
            try:
                transcript_list = await loop.run_in_executor(
                    None, lambda: YouTubeTranscriptApi.get_transcript(video_id)
                )
                
                # Combine text
                full_text = " ".join([t['text'] for t in transcript_list])
                # Truncate for summary
                summary_text = full_text[:500] + "..."
                
                result_data = {
                    "video_id": video_id,
                    "title": title,
                    "transcript_preview": summary_text,
                    "full_transcript_length": len(full_text)
                }
                
                await self._write_to_memory(
                    tool_name="youtube_transcript",
                    args={"video_id": video_id},
                    result=result_data
                )
                
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": result_data,
                    "summary": f"Video '{title}' Analysis:\n{summary_text}"
                }
                
            except Exception as e:
                return {
                    "agent": self.config.name,
                    "task": task,
                    "result": {"video_id": video_id, "title": title},
                    "summary": f"Found video '{title}' but couldn't get transcript: {e}"
                }
            
        except Exception as e:
            logger.error(f"Watcher failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Video analysis failed: {e}"
            }

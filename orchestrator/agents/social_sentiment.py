"""Social Sentiment Agent (Reddit)."""

from .base import MCPAgent
from typing import Dict, Any
from orchestrator.utils.logging import logger
from orchestrator.config import get_settings
import praw
import asyncio

logger = structlog.get_logger(__name__)

class SocialSentimentAgent(MCPAgent):
    """
    Social Sentiment - Uses Reddit API for sentiment analysis.
    Tools: reddit_search
    """
    
    def __init__(self, config, hot_memory):
        super().__init__(config, hot_memory)
        settings = get_settings()
        self.reddit = None
        if settings.reddit_client_id and settings.reddit_client_secret:
            self.reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent
            )
        else:
            logger.warning("Reddit credentials missing. Social Sentiment will fail.")

    async def process_task(self, task: str) -> Dict[str, Any]:
        """Analyze social sentiment on Reddit."""
        logger.info(f"Social Sentiment analyzing: {task}")
        
        if not self.reddit:
            return {
                "agent": self.config.name,
                "task": task,
                "error": "Reddit credentials missing",
                "summary": "Social analysis unavailable."
            }
        
        try:
            loop = asyncio.get_event_loop()
            
            def scan_reddit():
                submissions = []
                # Search all subreddits
                for submission in self.reddit.subreddit("all").search(task, limit=10):
                    submissions.append({
                        "title": submission.title,
                        "score": submission.score,
                        "url": submission.url,
                        "num_comments": submission.num_comments,
                        "selftext": submission.selftext[:500]
                    })
                return submissions
            
            results = await loop.run_in_executor(None, scan_reddit)
            
            summary_text = "\n".join([f"- {r['title']} (Score: {r['score']})" for r in results[:5]])
            
            await self._write_to_memory(
                tool_name="reddit_search",
                args={"query": task},
                result=results
            )
            
            return {
                "agent": self.config.name,
                "task": task,
                "result": results,
                "summary": f"Found {len(results)} discussions:\n{summary_text}"
            }
            
        except Exception as e:
            logger.error(f"Reddit scan failed: {e}")
            return {
                "agent": self.config.name,
                "task": task,
                "error": str(e),
                "summary": f"Social analysis failed: {e}"
            }

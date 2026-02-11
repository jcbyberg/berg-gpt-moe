"""Agents initialization."""

from .base import MCPAgent
from .web_scout import WebScoutAgent
from .code_hunter import CodeHunterAgent
from .fact_checker import TheFactCheckerAgent
from .scholar import TheScholarAgent
from .privacy_scout import PrivacyScoutAgent
from .watcher import TheWatcherAgent
from .social_sentiment import SocialSentimentAgent
from .deep_fetcher import DeepFetcherAgent
from .fixer import TheFixerAgent
from .context_analyst import ContextAnalystAgent
from orchestrator.config import get_settings, AgentConfig
from orchestrator.memory.hot import HotMemoryManager
from orchestrator.utils.logging import logger
from typing import Dict, List

logger = structlog.get_logger(__name__)

AGENT_REGISTRY: Dict[str, Dict] = {
    "res_01_web": {
        "class": WebScoutAgent,
        "config": {
            "id": "res_01_web",
            "name": "Web Scout",
            "role": "Web Search Specialist",
            "model": "gemini-2.5-flash",
            "tools": ["tavily_search"],
            "hot_memory_prefix": "ctx:web:",
            "max_retries": 3,
            "timeout": 30
        }
    },
    "res_02_code": {
        "class": CodeHunterAgent,
        "config": {
            "id": "res_02_code",
            "name": "Code Hunter",
            "role": "Code Search Specialist",
            "model": "gemini-2.5-flash",
            "tools": ["github_search_code", "github_search_repos"],
            "hot_memory_prefix": "ctx:code:",
            "max_retries": 3,
            "timeout": 30
        }
    },
    "res_03_debug": { "class": TheFixerAgent, "config": { "id": "res_03_debug", "name": "The Fixer", "role": "Debugging Specialist", "model": "gemini-2.5-flash", "tools": ["stack_overflow_search"], "hot_memory_prefix": "ctx:debug:", "max_retries": 3, "timeout": 30 } },
    "res_04_video": { "class": TheWatcherAgent, "config": { "id": "res_04_video", "name": "The Watcher", "role": "Video Analysis Specialist", "model": "gemini-2.5-flash", "tools": ["youtube_transcript"], "hot_memory_prefix": "ctx:video:", "max_retries": 3, "timeout": 30 } },
    "res_05_academic": { "class": TheScholarAgent, "config": { "id": "res_05_academic", "name": "The Scholar", "role": "Academic Research Specialist", "model": "gemini-2.5-flash", "tools": ["arxiv_search"], "hot_memory_prefix": "ctx:scholar:", "max_retries": 3, "timeout": 30 } },
    "res_06_wiki": { "class": TheFactCheckerAgent, "config": { "id": "res_06_wiki", "name": "The Fact Checker", "role": "Fact Verification Specialist", "model": "gemini-2.5-flash", "tools": ["wikipedia_search"], "hot_memory_prefix": "ctx:wiki:", "max_retries": 3, "timeout": 30 } },
    "res_07_privacy": { "class": PrivacyScoutAgent, "config": { "id": "res_07_privacy", "name": "Privacy Scout", "role": "Privacy Research Specialist", "model": "gemini-2.5-flash", "tools": ["ddg_search"], "hot_memory_prefix": "ctx:ddg:", "max_retries": 3, "timeout": 30 } },
    "res_08_fetch": { "class": DeepFetcherAgent, "config": { "id": "res_08_fetch", "name": "Deep Fetcher", "role": "Deep Web Fetching Specialist", "model": "gemini-2.5-flash", "tools": ["puppeteer_navigate", "puppeteer_extract"], "hot_memory_prefix": "ctx:fetch:", "max_retries": 3, "timeout": 60 } },
    "res_09_social": { "class": SocialSentimentAgent, "config": { "id": "res_09_social", "name": "Social Sentiment", "role": "Social Media Analysis Specialist", "model": "gemini-2.5-flash", "tools": ["reddit_search"], "hot_memory_prefix": "ctx:social:", "max_retries": 3, "timeout": 30 } },
    "res_10_files": { "class": ContextAnalystAgent, "config": { "id": "res_10_files", "name": "Context Analyst", "role": "File Analysis Specialist", "model": "gemini-2.5-flash", "tools": ["filesystem_search"], "hot_memory_prefix": "ctx:files:", "max_retries": 3, "timeout": 30 } },
}


class AgentRegistry:
    """Manages agent lifecycle and initialization."""
    
    def __init__(self, hot_memory: HotMemoryManager):
        self.hot_memory = hot_memory
        self._agents: Dict[str, MCPAgent] = {}
        
    async def initialize_all(self) -> None:
        """Initialize all registered agents."""
        logger.info(f"Initializing {len(AGENT_REGISTRY)} agents...")
        
        for agent_id, agent_info in AGENT_REGISTRY.items():
            agent_class = agent_info["class"]
            # Create AgentConfig object
            config = AgentConfig(
                id=agent_info["config"]["id"],
                name=agent_info["config"]["name"],
                role=agent_info["config"]["role"],
                model=agent_info["config"]["model"],
                tools=agent_info["config"]["tools"],
                hot_memory_prefix=agent_info["config"]["hot_memory_prefix"],
                max_retries=agent_info["config"]["max_retries"],
                timeout=agent_info["config"]["timeout"]
            )
            
            agent = agent_class(config, self.hot_memory)
            await agent.initialize()
            self._agents[agent_id] = agent
        
        logger.info("All agents initialized")
    
    def get_agent(self, agent_id: str) -> MCPAgent:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> List[MCPAgent]:
        """Get all initialized agents."""
        return list(self._agents.values())
    
    def get_active_agent_ids(self) -> List[str]:
        """Get list of all active agent IDs."""
        return list(AGENT_REGISTRY.keys())

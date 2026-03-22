"""ZAI GLM-5 integration."""

import asyncio
from typing import List, Any
import zai_sdk as zai_sdk
from orchestrator.utils.logging import logger


class ZaiClientError(Exception):
    """Custom exception for ZaiClient errors."""

    pass


class ZaiClient:
    """Wrapper for ZAI GLM-5 models."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ZaiClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._configured = False
        self._client = None

    def configure(self, api_key: str):
        """Configure ZAI API."""
        if self._configured:
            return

        if not api_key or api_key == "dummy_key_replace_me":
            logger.warning("ZAI API Key not set. AI features will fail.")
            return

        try:
            self._client = zai_sdk.ZaiClient(api_key=api_key)
            self._configured = True
            logger.info("ZAI initialized.")
        except Exception as e:
            logger.error(f"Failed to configure ZAI client: {e}")
            raise ZaiClientError("Failed to configure ZAI client") from e

    async def _run_sync_in_executor(self, func, *args, **kwargs) -> Any:
        """Wrap synchronous SDK call in executor to avoid blocking async loop."""
        if not self._configured:
            raise ZaiClientError("ZAI client is not configured")

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, func, *args, **kwargs)
        except Exception as e:
            logger.error(f"ZAI SDK error: {e}")
            raise ZaiClientError("ZAI SDK error") from e

    async def generate_response(self, prompt: str) -> str:
        """Generate a response from ZAI GLM-5."""
        return await self._run_sync_in_executor(self._client.generate, prompt)

    async def plan_mission(self, mission: str) -> List[str]:
        """
        Decide which agents to recruit for a task.
        Returns a list of agent IDs.
        """
        return await self._run_sync_in_executor(self._client.plan, mission)

    async def synthesize_results(self, results: str) -> str:
        """Synthesize multiple agent outputs into a cohesive answer."""
        return await self._run_sync_in_executor(self._client.synthesize, results)

"""The Gardener - Memory Management Agent."""

from orchestrator.memory.hot import HotMemoryManager
from orchestrator.memory.cold import ColdMemoryManager
from orchestrator.utils.logging import logger
import asyncio
import time

class GardenerAgent:
    """
    Background worker that maintains the memory ecosystem.
    - Prunes Hot Memory (Redis) when it gets too full
    - Archives valuable insights to Cold Memory (LanceDB)
    """
    
    def __init__(
        self, 
        hot_memory: HotMemoryManager, 
        cold_memory: ColdMemoryManager,
        interval_seconds: int = 600
    ):
        self.hot_memory = hot_memory
        self.cold_memory = cold_memory
        self.interval = interval_seconds
        self._running = False
        self._task = None
        
    async def start(self):
        """Start the gardening loop."""
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("The Gardener has started tending the memory.")

    async def stop(self):
        """Stop the gardening loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("The Gardener has finished for the day.")

    async def _loop(self):
        """Main maintenance loop."""
        while self._running:
            try:
                await self.tend_garden()
            except Exception as e:
                logger.error(f"Gardener encountered a weed: {e}")
            
            await asyncio.sleep(self.interval)

    async def tend_garden(self):
        """Perform memory maintenance tasks."""
        logger.debug("Gardener is checking memory health...")
        
        # 1. Archive Logic (Simplified for now)
        # In a real system, we'd fetch high-value items from Redis
        # For now, we assume the 'write' path in HotMemory mostly handles immediate needs
        # We could query Redis for items marked 'important' and move them.
        
        # 2. Prune Hot Memory
        # Keep Redis lean (e.g., max 1000 items)
        pruned_count = await self.hot_memory.prune(max_size=1000)
        
        if pruned_count > 0:
            logger.info(f"Gardener pruned {pruned_count} withered leaves from Hot Memory.")
        else:
            logger.debug("Hot Memory looks healthy.")

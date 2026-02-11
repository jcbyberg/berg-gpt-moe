"""API module initialization."""

from .openai_adapter import router as openai_router

__all__ = ["openai_router"]

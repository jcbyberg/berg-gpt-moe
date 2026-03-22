"""AI module initialization."""

from .gemini import gemini_client, GeminiClient
from .zai import zai_client, ZaiGLMClient
from typing import Union


def get_ai_client(provider: str) -> Union[GeminiClient, ZaiGLMClient]:
    """Get AI client instance based on provider.

    Args:
        provider: 'zai' or 'gemini' - Which AI provider to use

    Returns:
        ZaiGLMClient for 'zai' provider
        GeminiClient for 'gemini' provider

    Raises:
        ValueError: If provider is not 'zai' or 'gemini'
    """
    if provider == "zai":
        return zai_client
    elif provider == "gemini":
        return gemini_client
    else:
        raise ValueError(f"Invalid provider: {provider}. Must be 'zai' or 'gemini'")


__all__ = ["gemini_client", "GeminiClient", "zai_client", "ZaiGLMClient", "get_ai_client"]

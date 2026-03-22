"""Orchestrator configuration management."""

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Dict
import os


class AgentConfig(BaseModel):
    """Agent configuration model."""

    id: str
    name: str
    role: str
    model: str
    tools: List[str]
    hot_memory_prefix: str
    max_retries: int
    timeout: int


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_password: str = ""
    redis_max_memory: str = "4gb"
    redis_ttl: int = 3600  # 1 hour

    # LanceDB Configuration
    lancedb_path: str = "./hive_cold_memory.lance"
    lancedb_num_partitions: int = 256
    lancedb_num_sub_vectors: int = 96
    lancedb_reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # AI Configuration
    google_api_key: str = ""
    tavily_api_key: str = ""
    github_token: str = ""

    # Reddit Configuration
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "python:hive-mind:v2.1.0"

    # Gemini Configuration
    gemini_model: str = "gemini-2.5-flash"
    orchestrator_model: str = "gemini-1.5-pro"

    # ZAI Configuration
    zai_api_key: str = ""
    zai_model: str = "glm-5"
    zai_fallback_model: str = "glm-4.7"

    # MCP Configuration
    mcp_timeout: int = 30
    mcp_retry_attempts: int = 3

    # Memory Configuration
    hot_memory_prune_size: int = 1000
    cold_memory_archive_batch: int = 50

    class Config:
        """Pydantic configuration for loading from .env file."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

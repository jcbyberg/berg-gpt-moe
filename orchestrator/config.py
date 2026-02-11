"""Orchestrator configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Dict
import os


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
    
    gemini_model: str = "gemini-2.5-flash"
    orchestrator_model: str = "gemini-1.5-pro"
    
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


class AgentConfig(BaseSettings):
    """Agent-specific configuration."""
    
    id: str
    name: str
    role: str
    model: str
    tools: List[str]
    hot_memory_prefix: str
    max_retries: int = 3
    timeout: int = 30
    
    class Config(BaseSettings.Config):
        env_prefix = "AGENT_"


class SystemConfig(BaseSettings):
    """System-wide configuration."""
    
    global_context_bus: str = "RedisVL"
    long_term_memory: str = "LanceDB"
    concurrency_mode: str = "Async/Parallel"
    max_parallel_agents: int = 10
    agent_timeout: int = 60
    
    class Config(BaseSettings.Config):
        env_prefix = "SYSTEM_"

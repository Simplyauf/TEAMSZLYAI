"""
Configuration management for the Knowledge Base API
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    api_title: str = "Knowledge Base API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # Database Configuration
    postgres_host: str = Field(default="postgres", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="knowledge_base", env="POSTGRES_DB")
    postgres_user: str = Field(default="kb_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="kb_password", env="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Vector Store Configuration
    weaviate_url: str = Field(default="http://weaviate:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")

    # LLM Configuration
    ollama_url: str = Field(default="http://ollama:11434", env="OLLAMA_URL")
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")

    # Embedding Configuration
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")

    # Redis Configuration
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Slack Configuration
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
    slack_app_token: Optional[str] = Field(default=None, env="SLACK_APP_TOKEN")
    slack_signing_secret: Optional[str] = Field(default=None, env="SLACK_SIGNING_SECRET")

    # Processing Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_context_length: int = Field(default=4000, env="MAX_CONTEXT_LENGTH")

    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
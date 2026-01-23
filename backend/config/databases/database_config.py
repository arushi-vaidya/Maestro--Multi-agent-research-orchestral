"""Database configuration for MAESTRO."""
import os
from pydantic import BaseSettings

class DatabaseConfig(BaseSettings):
    """Configuration for databases."""
    
    # PostgreSQL for structured data
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "maestro")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "maestro")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    
    # Redis for caching
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Vector DB for RAG
    VECTOR_DB_TYPE: str = "chroma"  # Options: chroma, pinecone, weaviate
    VECTOR_DB_PATH: str = "./vector_store/indices"
    
    class Config:
        env_file = ".env"

database_config = DatabaseConfig()

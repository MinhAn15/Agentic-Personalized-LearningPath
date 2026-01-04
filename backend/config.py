from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application configuration for Full Mode with SQL Server + Neo4j Aura"""
    
    # API
    API_TITLE: str = "Agentic Learning Path API"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    
    # ============================================
    # PostgreSQL Database (Docker)
    # ============================================
    # Connection string format: postgresql://user:password@host:port/database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DATABASE: str = "learning_db"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    
    @property
    def DATABASE_URL(self) -> str:
        """Build PostgreSQL connection string for asyncpg"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
        )
    
    # ============================================
    # Neo4j (Docker - Local Development)
    # ============================================
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "testpassword"  # Matches docker-compose.yml
    
    # ============================================
    # Redis Cache
    # ============================================
    REDIS_URL: str = "redis://localhost:6379"
    
    # ============================================
    # LLM (Google Gemini via LlamaIndex)
    # ============================================
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # ============================================
    # Chroma Vector Database
    # ============================================
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    # ============================================
    # Agent 3: Path Planner
    # ============================================
    LINUCB_ALPHA: float = 0.1  # Exploration parameter
    TOT_BEAM_WIDTH: int = 3
    TOT_LOOKAHEAD_DEPTH: int = 3
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration"""
    
    # API
    API_TITLE: str = "Agentic Learning Path API"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/learning_db"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "testpassword"
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM (Google Gemini via LlamaIndex)
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Chroma
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

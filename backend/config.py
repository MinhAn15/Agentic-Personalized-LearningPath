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
    # SQL Server Database
    # ============================================
    # Connection string format: mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
    SQLSERVER_HOST: str = "localhost"
    SQLSERVER_PORT: int = 1433
    SQLSERVER_DATABASE: str = "learning_db"
    SQLSERVER_USER: str = "sa"
    SQLSERVER_PASSWORD: str = ""
    SQLSERVER_DRIVER: str = "ODBC Driver 17 for SQL Server"
    
    @property
    def DATABASE_URL(self) -> str:
        """Build SQL Server connection string for SQLAlchemy"""
        return (
            f"mssql+pyodbc://{self.SQLSERVER_USER}:{self.SQLSERVER_PASSWORD}"
            f"@{self.SQLSERVER_HOST}:{self.SQLSERVER_PORT}/{self.SQLSERVER_DATABASE}"
            f"?driver={self.SQLSERVER_DRIVER.replace(' ', '+')}"
        )
    
    # ============================================
    # Neo4j Aura (Cloud Knowledge Graph)
    # ============================================
    # Get credentials from https://console.neo4j.io/
    NEO4J_URI: str = "neo4j+s://xxxxxxxx.databases.neo4j.io"  # Aura connection string
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    
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
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

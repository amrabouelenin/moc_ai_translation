import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(default="2023-05-15", env="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment_name: str = Field(default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    model_name: str = Field(default="gpt-4", env="MODEL_NAME")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./translation.db", env="DATABASE_URL")
    vector_db_path: str = Field(default="./data/vector_index.faiss", env="VECTOR_DB_PATH")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Embedding Configuration
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    top_k_matches: int = Field(default=5, env="TOP_K_MATCHES")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

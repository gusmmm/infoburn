from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    Attributes:
        MONGODB_URL: MongoDB connection string
        DATABASE_NAME: Name of the database to use
        OPENROUTER_API_KEY: OpenRouter API key
        OPENAI_API_KEY: OpenAI API key
        GEMINI_API_KEY: Google Gemini API key
        MISTRAL_API_KEY: Mistral API key
        CODESTRAL_API_KEY: Codestral API key
        NOVITA_API_KEY: Novita API key
        GOOGLE_SHEET_ID: Google Sheets ID
        PYDANTIC_API_KEY: Pydantic API key
    """
    # Required settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "infoburn"
    
    # Optional API keys
    OPENROUTER_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None
    CODESTRAL_API_KEY: str | None = None
    NOVITA_API_KEY: str | None = None
    GOOGLE_SHEET_ID: str | None = None
    PYDANTIC_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore additional env vars

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Returns:
        Settings: Application settings
    """
    return Settings()
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    
    # RecallrAI
    RECALLRAI_API_KEY: str
    RECALLRAI_PROJECT_ID: str
    
    # WATI
    WATI_API_TOKEN: str
    WATI_BASE_URL: str
    ALLOWED_PHONE_NUMBERS: list[str] = []

    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
@lru_cache()
def get_settings():
    return Settings()

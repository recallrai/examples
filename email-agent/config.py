from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    
    # RecallrAI
    RECALLRAI_API_KEY: str
    RECALLRAI_PROJECT_ID: str
    RECALLRAI_USER_ID: str
    
    # ACS
    ACS_EMAIL: str
    ACS_KEY: str
    ACS_ENDPOINT: str

    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
@lru_cache()
def get_settings():
    return Settings()

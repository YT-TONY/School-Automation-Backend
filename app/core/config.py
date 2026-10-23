# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "School Portal Platform"
    ENVIRONMENT: str = "development"
    

    SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    PAYSTACK_SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
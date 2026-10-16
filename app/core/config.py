from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "School Portal Platform"
    ENVIRONMENT: str = "development"
    
    # Required environment variables (no default values hardcoded)
    SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
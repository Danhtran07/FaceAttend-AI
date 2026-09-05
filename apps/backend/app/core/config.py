from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./faceattend.db"
    AI_SERVICE_URL: str = "http://ai-service:8000"
    AI_SERVICE_TIMEOUT_SECONDS: float = 10.0

    JWT_SECRET_KEY: str = "development-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
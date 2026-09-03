from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_name: str = "buffalo_l"
    detection_threshold: float = 0.5
    recognition_threshold: float = 0.5
    face_match_threshold: float = 0.5
    min_face_size: int = 40
    min_blur_variance: float = 50.0
    embedding_dim: int = 512
    aligned_face_size: int = 112
    allow_multiple_faces_recognition: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

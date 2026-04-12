from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "বাংলা RAG সহকারী"
    redis_url: str = "redis://localhost:6379/0"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    top_k: int = 8
    cache_ttl_seconds: int = 300
    negative_cache_ttl_seconds: int = 60
    products_path: Path = Path("data/knowledge_bank.json")
    faiss_index_path: Path = Path("artifacts/index.faiss")
    product_map_path: Path = Path("artifacts/id_map.json")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

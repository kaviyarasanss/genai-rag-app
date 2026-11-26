import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    qdrant_url: str
    collection: str
    embedding_model: str
    embedding_cache_dir: str | None
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    max_upload_bytes: int


def load_settings() -> Settings:
    return Settings(
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection=os.getenv("QDRANT_COLLECTION", "documents"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
        embedding_cache_dir=os.getenv("EMBEDDING_CACHE_DIR") or None,
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
        top_k=int(os.getenv("TOP_K", "4")),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024,
    )

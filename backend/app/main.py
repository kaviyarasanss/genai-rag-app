import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from .config import load_settings
from .embeddings import FastEmbedEmbedder
from .llm import ExtractiveLLM, OpenAICompatibleLLM
from .rag import RagService
from .vector_store import VectorStore

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("rag")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def build_service() -> RagService:
    settings = load_settings()
    embedder = FastEmbedEmbedder(settings.embedding_model, settings.embedding_cache_dir)
    store = VectorStore(
        QdrantClient(url=settings.qdrant_url), settings.collection, embedder.dimension
    )
    store.ensure_collection()
    if settings.llm_api_key:
        llm = OpenAICompatibleLLM(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
        logger.info("using LLM %s at %s", settings.llm_model, settings.llm_base_url)
    else:
        llm = ExtractiveLLM()
        logger.warning("LLM_API_KEY is not set: answers will be the retrieved passages")
    return RagService(
        embedder, store, llm, settings.chunk_size, settings.chunk_overlap, settings.top_k
    )


def create_app(service: RagService | None = None, max_upload_bytes: int | None = None) -> FastAPI:
    limit = max_upload_bytes if max_upload_bytes is not None else load_settings().max_upload_bytes

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.rag = service or build_service()
        yield

    app = FastAPI(
        title="GenAI RAG backend", lifespan=lifespan, root_path=os.getenv("ROOT_PATH", "")
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/upload")
    async def upload(file: UploadFile, request: Request) -> dict:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="The file is empty")
        if len(data) > limit:
            raise HTTPException(status_code=413, detail="The file is too large")
        try:
            chunks = request.app.state.rag.ingest(file.filename or "upload", data)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"filename": file.filename, "chunks": chunks}

    @app.post("/ask")
    def ask(body: AskRequest, request: Request) -> dict:
        try:
            return request.app.state.rag.ask(body.question)
        except httpx.HTTPError as error:
            logger.error("LLM request failed: %s", error)
            raise HTTPException(status_code=502, detail="The LLM request failed") from error

    return app


app = create_app()

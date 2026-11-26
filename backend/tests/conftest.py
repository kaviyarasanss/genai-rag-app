import hashlib
import math

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

from app.main import create_app
from app.rag import RagService
from app.vector_store import VectorStore


class FakeEmbedder:
    """Deterministic bag-of-words vectors, so tests need no model download."""

    dimension = 64

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimension
            for word in text.lower().split():
                index = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dimension
                vector[index] += 1.0
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


class FakeLLM:
    def __init__(self):
        self.calls: list[tuple[str, list[str]]] = []

    def answer(self, question: str, contexts: list[str]) -> str:
        self.calls.append((question, contexts))
        return f"answer to: {question}"


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def service(llm: FakeLLM) -> RagService:
    embedder = FakeEmbedder()
    store = VectorStore(QdrantClient(location=":memory:"), "test", embedder.dimension)
    store.ensure_collection()
    return RagService(embedder, store, llm, chunk_size=200, chunk_overlap=20, top_k=2)


@pytest.fixture
def client(service: RagService):
    with TestClient(create_app(service, max_upload_bytes=1024 * 1024)) as test_client:
        yield test_client

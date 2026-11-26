import logging

from .documents import chunk_text, extract_text
from .embeddings import Embedder
from .llm import LLM
from .vector_store import VectorStore

logger = logging.getLogger("rag")

NOT_FOUND_ANSWER = "I couldn't find anything about that in the uploaded documents."


class RagService:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        llm: LLM,
        chunk_size: int,
        chunk_overlap: int,
        top_k: int,
    ):
        self.embedder = embedder
        self.store = store
        self.llm = llm
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

    def ingest(self, filename: str, data: bytes) -> int:
        text = extract_text(filename, data)
        chunks = chunk_text(text, self.chunk_size, self.chunk_overlap)
        if not chunks:
            raise ValueError("The document has no text")
        count = self.store.add(chunks, self.embedder.embed(chunks), source=filename)
        logger.info("ingested %s: %d chunks", filename, count)
        return count

    def ask(self, question: str) -> dict:
        hits = self.store.search(self.embedder.embed([question])[0], self.top_k)
        logger.info("question answered with %d retrieved chunks", len(hits))
        if not hits:
            return {"answer": NOT_FOUND_ANSWER, "sources": []}
        answer = self.llm.answer(question, [hit.text for hit in hits])
        sources = [{"source": hit.source, "text": hit.text, "score": hit.score} for hit in hits]
        return {"answer": answer, "sources": sources}

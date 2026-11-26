import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


@dataclass(frozen=True)
class Hit:
    text: str
    source: str
    score: float


class VectorStore:
    # Keeps each upsert request well under Qdrant's 32 MiB request size limit.
    BATCH_SIZE = 256

    def __init__(self, client: QdrantClient, collection: str, dimension: int):
        self.client = client
        self.collection = collection
        self.dimension = dimension

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )

    def add(self, chunks: list[str], vectors: list[list[float]], source: str) -> int:
        points = [
            PointStruct(
                id=str(uuid.uuid4()), vector=vector, payload={"text": text, "source": source}
            )
            for text, vector in zip(chunks, vectors, strict=True)
        ]
        for start in range(0, len(points), self.BATCH_SIZE):
            self.client.upsert(
                collection_name=self.collection, points=points[start : start + self.BATCH_SIZE]
            )
        return len(points)

    def search(self, vector: list[float], limit: int) -> list[Hit]:
        result = self.client.query_points(
            collection_name=self.collection, query=vector, limit=limit
        )
        return [
            Hit(text=point.payload["text"], source=point.payload["source"], score=point.score)
            for point in result.points
        ]

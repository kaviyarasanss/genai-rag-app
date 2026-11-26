from qdrant_client import QdrantClient

from app.vector_store import VectorStore


def test_large_inputs_are_upserted_in_batches(monkeypatch):
    store = VectorStore(QdrantClient(location=":memory:"), "batches", dimension=4)
    store.ensure_collection()
    sizes = []
    original_upsert = store.client.upsert

    def counting_upsert(collection_name, points):
        sizes.append(len(points))
        return original_upsert(collection_name=collection_name, points=points)

    monkeypatch.setattr(store.client, "upsert", counting_upsert)
    count = store.add(["chunk"] * 600, [[1.0, 0.0, 0.0, 0.0]] * 600, source="big.txt")

    assert count == 600
    assert sizes == [256, 256, 88]
    assert store.client.count("batches").count == 600

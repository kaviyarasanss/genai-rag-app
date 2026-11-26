import pytest
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from app.main import create_app


def metrics_text() -> str:
    return generate_latest().decode()


def test_requests_are_counted_by_route(client):
    client.post("/ask", json={"question": "anything"})
    client.get("/health")

    body = metrics_text()

    assert 'http_requests_total{method="POST",path="/ask",status="200"}' in body
    assert 'http_request_duration_seconds_count{method="POST",path="/ask"}' in body
    assert 'path="/health"' not in body


def test_metrics_are_not_served_on_the_api_port(client):
    assert client.get("/metrics").status_code == 404


class BrokenService:
    def ask(self, question):
        raise RuntimeError("boom")


def test_crashing_requests_are_counted_as_500():
    with TestClient(create_app(BrokenService(), max_upload_bytes=1024)) as client:
        with pytest.raises(RuntimeError):
            client.post("/ask", json={"question": "anything"})

    assert 'http_requests_total{method="POST",path="/ask",status="500"}' in metrics_text()

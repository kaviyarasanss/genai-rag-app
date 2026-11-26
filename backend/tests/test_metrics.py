def test_metrics_count_requests_by_route(client):
    client.post("/ask", json={"question": "anything"})
    client.get("/health")

    body = client.get("/metrics").text

    assert 'http_requests_total{method="POST",path="/ask",status="200"}' in body
    assert 'http_request_duration_seconds_count{method="POST",path="/ask"}' in body
    assert 'path="/health"' not in body
    assert 'path="/metrics"' not in body

from app.rag import NOT_FOUND_ANSWER

DOCUMENT = (
    b"The team runs its services on Kubernetes. "
    b"The billing service stores invoices in MySQL. "
    b"Deployments happen after the CI pipeline passes on the main branch."
)


def upload(client, name="notes.txt", content=DOCUMENT):
    return client.post("/upload", files={"file": (name, content, "text/plain")})


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_stores_chunks(client):
    response = upload(client)

    assert response.status_code == 200
    assert response.json() == {"filename": "notes.txt", "chunks": 1}


def test_ask_uses_retrieved_chunks(client, llm):
    upload(client)

    response = client.post("/ask", json={"question": "Where are invoices stored?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "answer to: Where are invoices stored?"
    assert body["sources"][0]["source"] == "notes.txt"
    assert "invoices in MySQL" in llm.calls[0][1][0]


def test_ask_without_documents_does_not_call_the_llm(client, llm):
    response = client.post("/ask", json={"question": "Anything?"})

    assert response.json() == {"answer": NOT_FOUND_ANSWER, "sources": []}
    assert llm.calls == []


def test_empty_question_is_rejected(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_unsupported_file_is_rejected(client):
    response = upload(client, name="photo.png")

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_empty_file_is_rejected(client):
    assert upload(client, content=b"").status_code == 400


def test_too_large_file_is_rejected(client):
    assert upload(client, content=b"a" * (1024 * 1024 + 1)).status_code == 413


def test_broken_pdf_upload_returns_400(client):
    response = upload(client, name="broken.pdf", content=b"%PDF-1.4 not really a pdf")

    assert response.status_code == 400

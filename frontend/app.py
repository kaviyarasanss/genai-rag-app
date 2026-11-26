import os

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SECONDS = 120.0


def error_message(error: httpx.HTTPError) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        try:
            return str(error.response.json()["detail"])
        except (ValueError, KeyError, TypeError):
            return f"The backend returned {error.response.status_code}"
    return f"Could not reach the backend: {error}"


st.set_page_config(page_title="Document Q&A", page_icon="📄")
st.title("Document Q&A")
st.caption("Upload a document, then ask questions about it.")

uploaded = st.file_uploader("Document", type=["txt", "md", "pdf"])
if uploaded is not None and st.button("Upload"):
    with st.spinner("Reading and indexing the document..."):
        try:
            response = httpx.post(
                f"{BACKEND_URL}/upload",
                files={"file": (uploaded.name, uploaded.getvalue())},
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            st.success(f"Stored {response.json()['chunks']} chunks from {uploaded.name}.")
        except httpx.HTTPError as error:
            st.error(error_message(error))

question = st.text_input("Question")
if st.button("Ask", disabled=not question.strip()):
    with st.spinner("Searching the documents..."):
        try:
            response = httpx.post(
                f"{BACKEND_URL}/ask", json={"question": question}, timeout=TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            st.error(error_message(error))
        else:
            body = response.json()
            st.markdown(body["answer"])
            if body["sources"]:
                with st.expander("Sources"):
                    for source in body["sources"]:
                        st.markdown(f"**{source['source']}** (score {source['score']:.2f})")
                        st.write(source["text"])

import logging
from typing import Protocol
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("rag")

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}

SYSTEM_PROMPT = (
    "You answer questions using only the context provided. "
    "If the context does not contain the answer, say you don't know."
)


class LLM(Protocol):
    def answer(self, question: str, contexts: list[str]) -> str: ...


class OpenAICompatibleLLM:
    """Calls any OpenAI-compatible chat API (Groq, OpenAI, Gemini's OpenAI endpoint)."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        url = urlparse(self.base_url)
        if api_key and url.scheme == "http" and url.hostname not in LOOPBACK_HOSTS:
            logger.warning(
                "LLM_BASE_URL uses plain http for %s: the API key is sent unencrypted", url.hostname
            )

    def answer(self, question: str, contexts: list[str]) -> str:
        context = "\n\n---\n\n".join(contexts)
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


class ExtractiveLLM:
    """Used when no LLM API key is set: returns the most relevant passages as the answer."""

    def answer(self, question: str, contexts: list[str]) -> str:
        passages = "\n\n".join(f"- {text}" for text in contexts)
        return (
            f"No LLM API key is configured, so here are the most relevant passages:\n\n{passages}"
        )

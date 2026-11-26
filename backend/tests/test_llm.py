import logging

from app.llm import OpenAICompatibleLLM


def test_warns_when_api_key_would_be_sent_over_plain_http(caplog):
    with caplog.at_level(logging.WARNING, logger="rag"):
        OpenAICompatibleLLM("http://llm.internal/v1", "secret", "model")

    assert "unencrypted" in caplog.text


def test_https_and_loopback_urls_do_not_warn(caplog):
    with caplog.at_level(logging.WARNING, logger="rag"):
        OpenAICompatibleLLM("https://api.groq.com/openai/v1", "secret", "model")
        OpenAICompatibleLLM("http://localhost:11434/v1", "secret", "model")

    assert caplog.text == ""

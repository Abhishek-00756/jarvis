"""LLM access: local Ollama model, plus an optional cloud fallback."""

from langchain_ollama import ChatOllama
from agent import config


def get_llm(bind_tools=None):
    llm = ChatOllama(model=config.MODEL_NAME, base_url=config.OLLAMA_HOST, temperature=config.TEMPERATURE)
    if bind_tools:
        llm = llm.bind_tools(bind_tools)
    return llm


def get_cloud_llm(bind_tools=None):
    if not config.CLOUD_FALLBACK_ENABLED:
        raise RuntimeError("Cloud fallback requested but ANTHROPIC_API_KEY is not set. Add it to .env to enable fallback.")
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model=config.CLOUD_FALLBACK_MODEL, api_key=config.ANTHROPIC_API_KEY, temperature=config.TEMPERATURE)
    if bind_tools:
        llm = llm.bind_tools(bind_tools)
    return llm

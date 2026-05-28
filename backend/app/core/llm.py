"""LangChain + Sarvam AI LLM client setup."""

import os
import logging
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Set LangSmith environment variables
os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"


@lru_cache()
def get_llm(streaming: bool = False, temperature: float = 0.1) -> ChatOpenAI:
    """Return a ChatOpenAI client pointing at Sarvam AI's OpenAI-compatible API."""
    kwargs = {
        "model": settings.sarvam_model,
        "openai_api_key": settings.sarvam_api_key,
        "openai_api_base": settings.sarvam_base_url,
        "temperature": temperature,
        "max_tokens": 4096,
        "streaming": streaming,
    }
    if streaming:
        kwargs["callbacks"] = [StreamingStdOutCallbackHandler()]

    llm = ChatOpenAI(**kwargs)
    logger.info(
        "Sarvam AI LLM initialised: model=%s endpoint=%s",
        settings.sarvam_model,
        settings.sarvam_base_url,
    )
    return llm


def get_analysis_llm() -> ChatOpenAI:
    """Higher-temperature LLM for creative insight generation."""
    return ChatOpenAI(
        model=settings.sarvam_model,
        openai_api_key=settings.sarvam_api_key,
        openai_api_base=settings.sarvam_base_url,
        temperature=0.4,
        max_tokens=8192,
    )


def get_sql_llm() -> ChatOpenAI:
    """Low-temperature LLM optimised for SQL generation."""
    return ChatOpenAI(
        model=settings.sarvam_model,
        openai_api_key=settings.sarvam_api_key,
        openai_api_base=settings.sarvam_base_url,
        temperature=0.0,
        max_tokens=2048,
    )

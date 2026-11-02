from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import litellm
from pydantic import BaseModel, ValidationError

from app.config import settings


@dataclass(frozen=True)
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int


class LLMClient:
    """The only place that talks to LiteLLM. `model` is a LiteLLM id: `ollama_chat/qwen3:8b`."""

    def __init__(self, model: str, temperature: float = 0.0, max_json_attempts: int = 3):
        self.model = model
        self.temperature = temperature
        self.max_json_attempts = max_json_attempts

    def generate(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        return self._complete(_messages(prompt, system))

    def generate_json[T: BaseModel](
        self, prompt: str, schema: type[T], *, system: str | None = None
    ) -> tuple[T, LLMResponse]:
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
        }
        for attempt in range(1, self.max_json_attempts + 1):
            response = self._complete(_messages(prompt, system), response_format=response_format)
            try:
                return schema.model_validate_json(response.text), response
            except ValidationError:
                if attempt == self.max_json_attempts:
                    raise
        raise AssertionError("unreachable")

    def _complete(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            **_provider_kwargs(self.model),
            **kwargs,
        )
        return LLMResponse(
            text=response.choices[0].message.content or "",
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )


class EmbeddingClient:
    def __init__(self, model: str):
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = litellm.embedding(model=self.model, input=texts, **_api_base(self.model))
        return [item["embedding"] for item in response.data]


def _messages(prompt: str, system: str | None) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": system}] if system else []
    return [*messages, {"role": "user", "content": prompt}]


def _api_base(model: str) -> dict[str, Any]:
    return {"api_base": settings.ollama_base_url} if model.startswith("ollama") else {}


def _provider_kwargs(model: str) -> dict[str, Any]:
    if not model.startswith("ollama"):
        return {}
    # Thinking models (qwen3) would otherwise spend time and tokens on reasoning,
    # skewing the benchmark's timing and token metrics.
    return {**_api_base(model), "think": False}


@lru_cache
def get_generation_client() -> LLMClient:
    return LLMClient(settings.generation_model)


@lru_cache
def get_judge_client() -> LLMClient:
    return LLMClient(settings.judge_model, temperature=settings.judge_temperature)


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    return EmbeddingClient(settings.embedding_model)

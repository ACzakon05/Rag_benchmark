# ADR-0003: LiteLLM as the LLM client library

## Context

The MVP runs local models through Ollama (generation, LLM-as-a-Judge, embeddings), but the
architecture has to allow switching to commercial APIs (OpenAI, Anthropic, OpenRouter, ...)
later without touching the RAG or evaluation logic. Ollama is the model server; we still need
a client library on the backend side to talk to it.

## Decision

Use the **LiteLLM Python SDK** as the client library, wrapped in our own LLM adapter. The rest
of the code uses only the adapter (generate, generate JSON, embed) and never imports LiteLLM
directly.

Why:

1. **One interface for many providers** - Ollama today, commercial APIs later, by changing
   the model name and credentials in configuration.
2. **Consistent token usage** across providers, which we need for the system metrics.
3. **Built-in model pricing** - covers the optional cost estimate feature with little extra work.

## Consequences

- The library sits behind our adapter, so replacing it later affects one module only.
- LiteLLM is a large, frequently released dependency - its version is pinned via the lockfile
  and upgraded deliberately.
- Reasoning ("thinking") mode of models like qwen3 is disabled by default, so it doesn't
  inflate response times and token counts in the benchmark.

## Alternatives considered

- **OpenAI SDK against Ollama's OpenAI-compatible API** - small and stable, but no native
  support for non-OpenAI-compatible providers and no pricing data.
- **Native Ollama client** - full access to Ollama features, but no path to other providers.

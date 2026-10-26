# AGENT.md

Przewodnik dla agentów AI (i nowych osób) pracujących w tym repozytorium.

## Czym jest ten projekt

RAG Benchmark & Playground — aplikacja do porównywania konfiguracji RAG na
lokalnych modelach i korzystania ze zwycięskiej konfiguracji w czacie. Pełna
specyfikacja produktowa: plik `Rag benchmark_*.txt` w katalogu głównym — to
**źródło prawdy** dla zakresu, metryk i decyzji. Czytaj go przed większymi zmianami.

Aktualny stan: **szkielet** — pliki zawierają docstringi i sygnatury, logika to
`raise NotImplementedError` / `TODO`. Zadaniem jest wypełnianie modułów, nie
przebudowa architektury.

## Mapa kodu

- `backend/app/schemas/` — kontrakty Pydantic. **Źródło prawdy dla kształtu danych.**
  Zmiana kontraktu = ustalenie z zespołem (wpływa na wiele modułów).
- `backend/app/api/routes/` — endpointy REST (opisane w `docs/api.md`).
- `backend/app/ingestion/` — parsowanie plików i chunking (Osoba 3).
- `backend/app/retrieval/` — indeksowanie, wyszukiwanie, reranking (Osoba 4).
- `backend/app/evaluation/` — Recall@k, MRR, LLM-as-a-Judge (Osoba 5).
- `backend/app/runner/` — orkiestracja eksperymentu + Playground (Osoba 1).
- `backend/app/llm/` — adapter klienta LLM (Ollama / OpenAI-compatible).
- `frontend/` — Streamlit; strony w `frontend/pages/`, klient API w `frontend/lib/`.
- `docs/` — architektura, kontrakt API, kontrakty danych.

## Zasady, których trzymamy się w tym repo

Wynikają z ryzyk opisanych w specyfikacji (sekcja 9) — nie łam ich bez uzgodnienia:

1. **Modele lokalne wołamy sekwencyjnie** (1 zapytanie naraz). Równoległe wywołania
   do Ollamy zatykają VRAM. Patrz `MAX_CONCURRENT_LLM_CALLS`.
2. **Jeden prompt sędziego** zwraca poprawność i wierność naraz (mniej wywołań).
   `temperature=0`, wymuszony JSON, retry przy błędzie parsowania.
3. **Trafność liczymy po treści cytatu** (`expected_context_snippet`, pokrycie ≥ 80%),
   NIE po `chunk_id` — różne strategie chunkingu dają różne identyfikatory.
4. **Dostęp do modeli tylko przez adapter** `app/llm/client.py` — nigdy bezpośrednio.
   Dzięki temu zmiana na komercyjne API nie dotyka logiki RAG/eval.
5. **Osobna kolekcja wektorowa per konfiguracja** — po benchmarku gotowa dla Playground.
6. **Granice modułów** z `docs/architecture.md` są kontraktem. ingestion, retrieval
   i evaluation da się rozwijać niezależnie na danych syntetycznych/mockach.

## Konwencje

- Python 3.11+, FastAPI, SQLModel. Formatowanie/lint: `ruff`. Typy: `mypy`.
- Komentarze i docstringi: zwięźle, tylko gdy wyjaśniają "dlaczego".
- Konfiguracja wyłącznie przez `.env` (wzór: `.env.example`) — bez hardkodowania modeli/URL.
- Nie commituj danych użytkownika ani baz (patrz `.gitignore`): `data/`, `*.sqlite`, `qdrant_storage/`.

## Jak uruchomić / sprawdzić

```bash
docker compose up --build          # całość
# backend lokalnie:
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload
# testy:
cd backend && pytest
# frontend lokalnie:
cd frontend && pip install -r requirements.txt && streamlit run streamlit_app.py
```

Wymaga Ollamy na hoście z modelami `qwen3:8b` i `nomic-embed-text` (sekcja README).

## Czego NIE robić

- Nie wprowadzaj ciężkich frameworków RAG (np. LangChain) — specyfikacja celowo
  wybiera czysty Python dla precyzyjnego pomiaru czasu.
- Nie rozszerzaj zakresu o rzeczy z "Out of scope" (Auto-RAG/grid search, nDCG,
  pomiar RAM/VRAM, konta użytkowników) bez decyzji zespołu.
- Nie zmieniaj kontraktów w `schemas/` ani `docs/api.md` jednostronnie.

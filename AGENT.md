# AGENT.md

Przewodnik dla agentów AI (i nowych osób) pracujących w tym repozytorium.

## Czym jest ten projekt

RAG Benchmark & Playground — aplikacja do porównywania konfiguracji RAG na
lokalnych modelach i korzystania ze zwycięskiej konfiguracji w czacie. Pełna
specyfikacja produktowa: plik `SPECIFICATION.md` (oraz `Rag benchmark_*.txt`) w katalogu głównym — to
**źródło prawdy** dla zakresu, metryk i decyzji. Czytaj go przed większymi zmianami.

Aktualny stan: **warstwa API / baza / kolejka jest gotowa i działa na danych fake**
(`FAKE_RUNNER=true`, `runner/fake_runner.py`). Moduły `ingestion`, `retrieval`, `evaluation`,
prawdziwy `runner/orchestrator.py` i frontend to jeszcze szkielety (`raise NotImplementedError`).
Zadaniem jest wypełnianie modułów, nie przebudowa architektury. Gdzie ADR (`docs/adr/`)
różni się od `SPECIFICATION.md`, wygrywa ADR.

## Mapa kodu

- `backend/app/schemas/` — kontrakty Pydantic. **Źródło prawdy dla kształtu danych.**
  Zmiana kontraktu = ustalenie z zespołem (wpływa na wiele modułów).
- `backend/app/api/routes/v1/` — endpointy REST (opisane w `docs/api.md`), cienkie; logika w `services/`.
- `backend/app/services/`, `backend/app/repositories/` — logika biznesowa i dostęp do bazy.
- `backend/app/models/`, `backend/migrations/` — modele SQLAlchemy i migracje Alembica.
- `backend/app/celery_app.py`, `backend/app/runner/tasks.py` — kolejka zadań (Celery + Redis).
- `backend/app/ingestion/` — parsowanie plików i chunking (Osoba 3).
- `backend/app/retrieval/` — indeksowanie, wyszukiwanie, reranking (Osoba 4).
- `backend/app/evaluation/` — Recall@k, MRR, LLM-as-a-Judge (Osoba 5).
- `backend/app/runner/` — orkiestracja eksperymentu + Playground (Osoba 1).
- `backend/app/llm/` — adapter klienta LLM i embeddingów (LiteLLM: Ollama / OpenAI / ...).
- `frontend/` — Streamlit; strony w `frontend/pages/`, klient API w `frontend/lib/`.
- `docs/` — architektura, kontrakt API, kontrakty danych, `docs/adr/` (decyzje architektoniczne).

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
5. **Kolekcja (`collection_id` w pgvector) per ustawienia chunkingu, współdzielona między
   konfiguracjami** (ADR-0004) — po benchmarku gotowa dla Playground.
6. **Granice modułów** z `docs/architecture.md` są kontraktem. ingestion, retrieval
   i evaluation da się rozwijać niezależnie na danych syntetycznych/mockach.

## Konwencje

- Python 3.13, FastAPI, SQLAlchemy 2.0, zależności przez `uv`. Formatowanie/lint: `ruff` (`make lint`).
- **Migracji nigdy nie piszemy ręcznie.** Zmiana schematu = zmiana modeli w `backend/app/models/`,
  potem `uv run alembic revision --autogenerate -m "..."`. Wygenerowany plik przeglądamy
  i poprawiamy tylko to, czego autogenerate nie wykrywa (np. `CREATE EXTENSION`, migracje danych).
- Komentarze i docstringi: zwięźle, tylko gdy wyjaśniają "dlaczego".
- Konfiguracja wyłącznie przez `.env` (wzór: `.env.example`) — bez hardkodowania modeli/URL.
- Nie commituj danych użytkownika ani baz (patrz `.gitignore`): `data/`, `pgdata/`.

## Jak uruchomić / sprawdzić

```bash
make up                            # całość (docker compose up); migracje idą przy starcie backendu
make migrate                       # migracje lokalnie względem bazy z compose
# backend lokalnie:
cd backend && uv sync && uv run fastapi dev app/main.py
# testy i lint:
make test                          # uv run pytest w backend/
make lint
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

# RAG Benchmark & Playground

Narzędzie typu **benchmark, evaluation & playground** dla systemów RAG
(Retrieval-Augmented Generation), działające domyślnie na **darmowych, lokalnych
modelach** (Ollama), z architekturą otwartą na komercyjne API w przyszłości.

Uruchamia kilka wariantów konfiguracji RAG na tym samym zbiorze dokumentów i pytań,
porównuje je pod kątem **jakości wyszukiwania, jakości odpowiedzi i wydajności**,
a następnie pozwala od razu korzystać ze zwycięskiej konfiguracji w interaktywnym
czacie (**Playground**).

> Status: **działa szkielet end-to-end na danych fake** — API, baza (PostgreSQL + pgvector),
> kolejka zadań (Celery + Redis) i `fake_runner` zapisujący wymyślone wyniki. Moduły RAG
> (`ingestion`, `retrieval`, `evaluation`) i orchestrator są jeszcze do implementacji
> (`FAKE_RUNNER=true` w `.env`), frontend Streamlit to na razie szkielet.

## Co porównujemy

- **Chunking:** stała liczba tokenów (z overlapem) vs podział strukturalny (nagłówki/akapity)
- **Wyszukiwanie:** wektorowe (dense) vs hybrydowe (dense + BM25, łączone przez RRF)
- **Reranking:** włączony / wyłączony (`BAAI/bge-reranker-base`)

**Metryki:** Recall@k, MRR (wyszukiwanie) · Answer Correctness, Faithfulness
(LLM-as-a-Judge) · czas wyszukiwania, czas całkowity, zużyte tokeny (system).

## Stack

| Warstwa | Technologia |
|---------|-------------|
| Frontend | **Streamlit** (Python) |
| Backend | FastAPI (Python 3.13), SQLAlchemy 2.0 + Alembic, zarządzanie zależnościami: `uv` |
| Baza danych | PostgreSQL 17 + pgvector (metadane, wyniki i wektory) |
| Zadania w tle | Celery + Redis (worker przetwarza jeden eksperyment naraz) |
| Klient modeli | LiteLLM (adapter w `backend/app/llm/`) |
| Wyszukiwanie leksykalne | `rank-bm25` |
| Modele (lokalne) | Ollama: `qwen3:8b` (generacja + sędzia), `nomic-embed-text` (embeddingi); `BAAI/bge-reranker-base` (Sentence-Transformers) |
| Infrastruktura | Docker + Docker Compose (`make` / `just` jako skróty) |

> Frontend wybrany jako Streamlit zamiast React (zespół pracuje w Pythonie).

## Struktura repozytorium

```
.
├── README.md
├── AGENT.md                  # przewodnik dla agentów AI pracujących w repo
├── SPECIFICATION.md          # specyfikacja produktowa (źródło prawdy dla zakresu)
├── docker-compose.yml        # backend, worker, frontend, postgres, redis
├── .env.example
├── Makefile / justfile       # skróty: up, migrate, test, lint
├── docs/
│   ├── architecture.md       # komponenty, przepływ danych, decyzje
│   ├── api.md                # endpointy REST (v1)
│   ├── data-contracts.md     # kontrakty danych (Etap 1)
│   └── adr/                  # Architecture Decision Records (ADR wygrywa ze specyfikacją)
├── backend/                  # FastAPI + moduły RAG
│   └── app/
│       ├── main.py           # punkt wejścia
│       ├── config.py         # ustawienia z .env
│       ├── api/routes/v1/    # datasets, experiments, results, playground
│       ├── services/         # logika biznesowa wołana z tras
│       ├── repositories/     # dostęp do bazy (CRUD)
│       ├── schemas/          # kontrakty Pydantic
│       ├── database.py       # silnik, BaseDbModel, sesja
│       ├── models/           # modele SQLAlchemy (+ migracje w backend/migrations/)
│       ├── celery_app.py     # kolejka zadań
│       ├── ingestion/        # [Osoba 3] parsowanie + chunking
│       ├── retrieval/        # [Osoba 4] indeks, wyszukiwanie, reranking
│       ├── runner/           # [Osoba 1] orkiestracja + playground (+ fake_runner)
│       ├── evaluation/       # [Osoba 5] metryki + LLM-as-a-Judge
│       └── llm/              # adapter klienta LLM i embeddingów (LiteLLM)
├── frontend/                 # [Osoba 2 / 6] Streamlit (strony: Konfigurator, Dashboard, Playground)
└── datasets/demo/            # przykładowy zbiór pokazowy
```

## Uruchomienie (docelowo)

> Wymaga lokalnie zainstalowanej **Ollamy** z pobranymi modelami.

```bash
# 1. Modele Ollama (na hoście)
ollama pull qwen3:8b
ollama pull nomic-embed-text

# 2. Konfiguracja
cp .env.example .env

# 3. Start całości (migracje stosują się przy starcie backendu)
make up          # lub: docker compose up --build
```

Przydatne: `make migrate`, `make create_migration m="opis"`, `make test`, `make lint`
(odpowiedniki w `justfile`). Backend lokalnie: `cd backend && uv sync && uv run fastapi dev app/main.py`.

- Frontend (Streamlit): http://localhost:8501
- Backend (Swagger): http://localhost:8000/docs

## Podział pracy

Mapowanie osób na moduły: patrz `docs/architecture.md` i sekcja 8 specyfikacji
produktowej (`SPECIFICATION.md`).

## Plan implementacji (skrót)

1. **Etap 1 — fundamenty:** zatwierdzenie kontraktów danych (`docs/data-contracts.md`) i API (`docs/api.md`).
2. **Etap 2 — walking skeleton:** 1 plik → chunk → indeks → odpowiedź dla 1 pytania.
3. **Etap 3 — równolegle:** chunking/retrieval/reranking · metryki/sędzia · UI.
4. **Etap 4 — integracja:** pełny przebieg 4 konfiguracji + strojenie promptów.
5. **Etap 5 — demo:** zbiór pokazowy eksponujący różnice A/B/C/D.

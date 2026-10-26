# RAG Benchmark & Playground

Narzędzie typu **benchmark, evaluation & playground** dla systemów RAG
(Retrieval-Augmented Generation), działające domyślnie na **darmowych, lokalnych
modelach** (Ollama), z architekturą otwartą na komercyjne API w przyszłości.

Uruchamia kilka wariantów konfiguracji RAG na tym samym zbiorze dokumentów i pytań,
porównuje je pod kątem **jakości wyszukiwania, jakości odpowiedzi i wydajności**,
a następnie pozwala od razu korzystać ze zwycięskiej konfiguracji w interaktywnym
czacie (**Playground**).

> Status: **szkielet projektu** (sucha architektura, bez implementacji). Wypełnianie
> modułów zgodnie z `docs/` i podziałem pracy z sekcji 8 specyfikacji.

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
| Backend | FastAPI (Python 3.11+), SQLModel |
| Baza relacyjna | SQLite |
| Baza wektorowa | Qdrant (Docker) + `rank-bm25` |
| Modele (lokalne) | Ollama: `qwen3:8b` (generacja + sędzia), `nomic-embed-text` (embeddingi); `BAAI/bge-reranker-base` (Sentence-Transformers) |
| Infrastruktura | Docker + Docker Compose |

> Frontend wybrany jako Streamlit zamiast React (zespół pracuje w Pythonie).

## Struktura repozytorium

```
.
├── README.md
├── AGENT.md                  # przewodnik dla agentów AI pracujących w repo
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── architecture.md       # komponenty, przepływ danych, decyzje
│   ├── api.md                # propozycja endpointów REST (v1)
│   └── data-contracts.md     # kontrakty danych (Etap 1)
├── backend/                  # FastAPI + moduły RAG
│   └── app/
│       ├── main.py           # punkt wejścia
│       ├── config.py         # ustawienia z .env
│       ├── api/routes/       # datasets, experiments, results, playground
│       ├── schemas/          # kontrakty Pydantic
│       ├── db/               # SQLite + modele
│       ├── ingestion/        # [Osoba 3] parsowanie + chunking
│       ├── retrieval/        # [Osoba 4] indeks, wyszukiwanie, reranking
│       ├── runner/           # [Osoba 1] orkiestracja + playground
│       ├── evaluation/       # [Osoba 5] metryki + LLM-as-a-Judge
│       └── llm/              # adapter klienta LLM (Ollama/OpenAI)
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

# 3. Start całości
docker compose up --build
```

- Frontend (Streamlit): http://localhost:8501
- Backend (Swagger): http://localhost:8000/docs

## Podział pracy

Mapowanie osób na moduły: patrz `docs/architecture.md` i sekcja 8 specyfikacji
produktowej (`Rag benchmark_*.txt`).

## Plan implementacji (skrót)

1. **Etap 1 — fundamenty:** zatwierdzenie kontraktów danych (`docs/data-contracts.md`) i API (`docs/api.md`).
2. **Etap 2 — walking skeleton:** 1 plik → chunk → indeks → odpowiedź dla 1 pytania.
3. **Etap 3 — równolegle:** chunking/retrieval/reranking · metryki/sędzia · UI.
4. **Etap 4 — integracja:** pełny przebieg 4 konfiguracji + strojenie promptów.
5. **Etap 5 — demo:** zbiór pokazowy eksponujący różnice A/B/C/D.

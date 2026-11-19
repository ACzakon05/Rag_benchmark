# Architektura

Modularny monolit z asynchroniczną kolejką zadań w tle, komunikujący się z
lokalnym serwerem modeli (Ollama). Szczegóły w specyfikacji produktowej (sekcja 4).

## Komponenty i podział odpowiedzialności (6 osób)

Zgodnie z sekcją 8 specyfikacji produktowej (`SPECIFICATION.md`):

| # | Rola w zespole | Katalog / Pliki | Właściciel | Zakres odpowiedzialności | Punkty styku |
|---|----------------|-----------------|------------|---------------------------|--------------|
| 1 | **Architekt Backendu & Orkiestracji** | `backend/app/api/`<br>`backend/app/runner/`<br>`backend/app/services/`<br>`backend/app/repositories/`<br>`backend/app/database.py`<br>`backend/app/models/`<br>`backend/migrations/`<br>`backend/app/celery_app.py`<br>`backend/app/llm/` | **Osoba 1** | Szkielet FastAPI (trasy `v1`, warstwy `services/` i `repositories/`), baza PostgreSQL + pgvector (schemat, migracje Alembic, sesje), kolejkowanie zadań eksperymentu (Celery + Redis), ujednolicony klient LLM (Ollama: qwen3:8b), zliczanie czasów i tokenów, endpointy dla modułu Playground. | Wystawia REST API dla Osób 2 i 6; wywołuje moduły Osób 3, 4 i 5. |
| 2 | **Frontend Developer – Benchmark UI** | `frontend/pages/1_Konfigurator.py`<br>`frontend/pages/2_Dashboard.py` *(widok makro)*<br>`frontend/lib/api_client.py` | **Osoba 2** | Widok wgrywania plików i pytań testowych, formularz wyboru konfiguracji (A, B, C, D), pasek postępu eksperymentu, główna tabela porównawcza metryk. | Korzysta z REST API wystawionego przez Osobę 1. |
| 3 | **Inżynier Przetwarzania Danych & Datasetu** | `backend/app/ingestion/`<br>`datasets/demo/` | **Osoba 3** | Ekstrakcja tekstu z PDF/MD/TXT, chunker stałej liczby tokenów (z overlapem), chunker strukturalny (nagłówki/akapity). Przygotowanie wzorcowego zbioru dokumentów i pytań testowych. | Dostarcza funkcję:<br>`chunk_documents(files, config) -> list[DocumentChunk]`. |
| 4 | **Inżynier Wyszukiwania i Rerankingu** | `backend/app/retrieval/` | **Osoba 4** | Zapis/wyszukiwanie wektorów w pgvector, integracja modelu `nomic-embed-text`, indeksowanie BM25, wyszukiwanie hybrydowe (RRF) oraz integracja modelu `BAAI/bge-reranker-base`. | Dostarcza interfejs:<br>`index_chunks(collection_id, chunks)` oraz `search(collection_id, query, config) -> list[ScoredChunk]`. |
| 5 | **Inżynier Ewaluacji** | `backend/app/evaluation/` | **Osoba 5** | Implementacja algorytmów Recall@k i MRR (dopasowanie po `expected_context_snippet`) oraz inżynieria promptów i walidacja JSON dla modelu `qwen3:8b` w roli sędziego (LLM-as-a-Judge). | Dostarcza funkcję:<br>`evaluate(question, ground_truth, retrieved_chunks, answer) -> EvaluationMetrics`. |
| 6 | **Full-stack / Playground & DevOps** | `frontend/pages/3_Playground.py`<br>`frontend/pages/2_Dashboard.py` *(widok mikro)*<br>`docker-compose.yml`<br>`*/Dockerfile` | **Osoba 6** | Budowa widoku szczegółowej inspekcji pytania oraz interfejsu czatu RAG Playground na frontendzie, konfiguracja Docker Compose i wsparcie integracji backend-frontend. | Współpracuje z Osobą 2 na frontendzie i dba o konteneryzację. |

## Przepływ danych

1. Upload dokumentów + testsetu → backend zapisuje pliki i rejestruje pytania w PostgreSQL (Osoba 1 / Osoba 2).
2. Start eksperymentu → backend tworzy zadanie w tle i przekazuje konfiguracje do runnera (Osoba 1).
3. Dla każdej brakującej kolekcji (zbiór pocięty i zembeddowany wg danych ustawień chunkingu):
   `chunk_documents` (Osoba 3) → `index_chunks` (Osoba 4, chunki + wektory w pgvector pod `collection_id` + indeks BM25).
   Następnie dla każdej konfiguracji (sekwencyjnie):
   - per pytanie: `search` (Osoba 4) → (opcjonalny `rerank`, Osoba 4) → `generate` (Osoba 1 / qwen3:8b), pomiar czasu i tokenów.
4. `evaluate` (Osoba 5): Recall@k, MRR (deterministyczne) + jeden prompt sędziego (poprawność + wierność).
5. Metryki zapisywane w PostgreSQL; frontend odpytuje o status i renderuje dashboard (Osoba 1 / Osoba 2 / Osoba 6).
6. Playground: zapytanie → runner → istniejąca kolekcja konfiguracji (`collection_id`) → odpowiedź na żywo (Osoba 1 / Osoba 6).

## Kluczowe decyzje projektowe

- **Wzorzec Adaptera dla modeli** (`backend/app/llm/client.py`, [ADR-0003](adr/0003-litellm-client.md)):
  `LLMClient` i `EmbeddingClient` opakowują LiteLLM → przejście na komercyjne API przez zmianę
  identyfikatora modelu w `.env`, bez zmian w logice RAG/eval.
- **Zadania w tle: Celery + Redis** ([ADR-0005](adr/0005-celery-redis.md)) — osobny proces `worker`,
  jeden eksperyment naraz; stan i wyniki tylko w PostgreSQL.
- **SQLAlchemy + Alembic** ([ADR-0002](adr/0002-sqlalchemy-alembic.md)) — każda zmiana schematu
  przez migrację.
- **Tryb fake** (`FAKE_RUNNER=true`) — dopóki ingestion/retrieval/evaluation nie są gotowe,
  `runner/fake_runner.py` zapisuje wiarygodne, wymyślone wyniki przez te same tabele.
- **Sekwencyjne wywołania LLM** dla modeli lokalnych (`MAX_CONCURRENT_LLM_CALLS=1`) —
  ochrona VRAM (ryzyko #1 w specyfikacji).
- **Trafność po treści cytatu, nie po `chunk_id`** — różne strategie chunkingu dają różne
  identyfikatory; trafienie = chunk zawiera `expected_context_snippet` (pokrycie ≥ 80%).
- **Jeden prompt sędziego** zwracający poprawność + wierność naraz — o połowę mniej wywołań.
- **PostgreSQL + pgvector jako jedyna baza** ([ADR-0001](adr/0001-postgres-pgvector.md)) —
  metadane, wyniki i wektory w jednym miejscu. Wektory w tabeli chunków (`vector(768)`
  dla `nomic-embed-text`), kolekcje rozróżniane kolumną `collection_id`.
- **Kolekcje współdzielone między konfiguracjami** ([ADR-0004](adr/0004-shared-collections.md)) —
  kolekcja = zbiór pocięty i zembeddowany wg ustawień chunkingu; konfiguracje o tych samych
  ustawieniach (także z różnych eksperymentów) korzystają z jednej kolekcji. Gotowa do użycia
  w Playground po benchmarku, bez ponownego indeksowania.
- **BM25 w pamięci (`rank-bm25`)** — budowany z chunków danej kolekcji pobranych z Postgresa.

## Granice modułów (kontrakty dla niezależnego developmentu)

```python
# Osoba 3 (Ingestion):
ingestion.chunk_documents(files: list[str], config: RagConfig) -> list[DocumentChunk]

# Osoba 4 (Retrieval):
retrieval.index_chunks(collection_id: str, chunks: list[DocumentChunk]) -> None
retrieval.search(collection_id: str, query: str, config: RagConfig) -> list[ScoredChunk]
retrieval.warm_up(config: RagConfig) -> None   # ładuje modele przed pętlą pytań (czasy benchmarku)
# import: from app.retrieval.retriever import index_chunks, search, warm_up

# Osoba 5 (Evaluation):
evaluation.evaluate(question: str, ground_truth: str, retrieved_chunks: list[ScoredChunk], answer: str) -> EvaluationMetrics

# Osoba 1 (LLM Client) — `app/llm/client.py`:
LLMClient.generate(prompt: str, *, system: str | None = None) -> LLMResponse   # text, prompt_tokens, completion_tokens
LLMClient.generate_json(prompt: str, schema: type[BaseModel], *, system: str | None = None) -> tuple[BaseModel, LLMResponse]
EmbeddingClient.embed(texts: list[str]) -> list[list[float]]
```

Uwagi do kontraktów ingestion → retrieval (tabela `chunk`): `DocumentChunk.chunk_id` i `document_id`
muszą być UUID-ami w postaci tekstowej, a `document_id` — istniejącym `document.id`
(klucz obcy). `collection_id` to UUID z tabeli `collection`.

## Moduł retrieval (Osoba 4)

Publiczne wejście to `retrieval/retriever.py` (fasada), a logika jest rozdzielona na pliki:

| Plik | Odpowiedzialność |
|---|---|
| `retriever.py` | `search`, `warm_up`, re-eksport `index_chunks` |
| `indexing.py` | `index_chunks`: embedding w paczkach + zapis do tabeli `chunk` (jedna transakcja) |
| `embedding.py` | embeddingi dokumentów i zapytań (prefiksy `nomic-embed-text`, walidacja wymiaru) |
| `dense.py` | wyszukiwanie wektorowe w pgvector (odległość kosinusowa, dokładne, bez indeksu ANN) |
| `bm25.py` | BM25 (`rank-bm25`) budowany w pamięci z chunków kolekcji, cache per kolekcja i proces |
| `fusion.py` | Reciprocal Rank Fusion (`k=60`) |
| `reranker.py` | cross-encoder `bge-reranker`, ładowany leniwie (raz na proces) |
| `common.py` | konwersja wiersza `Chunk` na `DocumentChunk` |

Przepływ `search(collection_id, query, config)`:

1. Wielkość puli kandydatów: `top_k`, a dla `hybrid` lub włączonego rerankingu `4 × top_k`.
2. `dense`: tylko wyszukiwanie wektorowe. `hybrid`: dense + BM25 łączone przez RRF.
3. Reranking (jeśli włączony) przeszeregowuje pulę i przycina do `top_k`.

`ScoredChunk.score` ma różną skalę zależnie od trybu (podobieństwo kosinusowe, suma RRF
rzędu 0,01–0,03, ocena rerankera 0–1), więc nie porównuje się wyników między trybami; liczy
się kolejność (`rank`). `contains_expected_snippet` wypełnia evaluation.

`index_chunks` i `search` same otwierają sesję bazy (`SessionLocal`), a pomijanie kolekcji, które
mają już chunki, należy do orchestratora. Cache BM25 jest per proces, więc worker (benchmark)
i backend (Playground) budują go niezależnie. Decyzje projektowe: [ADR-0006](adr/0006-retrieval-design.md).

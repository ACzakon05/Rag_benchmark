# Architektura

Modularny monolit z asynchroniczną kolejką zadań w tle, komunikujący się z
lokalnym serwerem modeli (Ollama). Szczegóły w specyfikacji produktowej (sekcja 4).

## Komponenty i podział odpowiedzialności (6 osób)

Zgodnie z sekcją 8 specyfikacji produktowej (`Rag benchmark_*.txt`):

| # | Rola w zespole | Katalog / Pliki | Właściciel | Zakres odpowiedzialności | Punkty styku |
|---|----------------|-----------------|------------|---------------------------|--------------|
| 1 | **Architekt Backendu & Orkiestracji** | `backend/app/api/`<br>`backend/app/runner/`<br>`backend/app/db/`<br>`backend/app/llm/` | **Osoba 1** | Szkielet FastAPI, baza SQLite, kolejkowanie zadań eksperymentu, ujednolicony klient LLM (Ollama: qwen3:8b), zliczanie czasów i tokenów, endpointy dla modułu Playground. | Wystawia REST API dla Osób 2 i 6; wywołuje moduły Osób 3, 4 i 5. |
| 2 | **Frontend Developer – Benchmark UI** | `frontend/pages/1_Konfigurator.py`<br>`frontend/pages/2_Dashboard.py` *(widok makro)*<br>`frontend/lib/api_client.py` | **Osoba 2** | Widok wgrywania plików i pytań testowych, formularz wyboru konfiguracji (A, B, C, D), pasek postępu eksperymentu, główna tabela porównawcza metryk. | Korzysta z REST API wystawionego przez Osobę 1. |
| 3 | **Inżynier Przetwarzania Danych & Datasetu** | `backend/app/ingestion/`<br>`datasets/demo/` | **Osoba 3** | Ekstrakcja tekstu z PDF/MD/TXT, chunker stałej liczby tokenów (z overlapem), chunker strukturalny (nagłówki/akapity). Przygotowanie wzorcowego zbioru dokumentów i pytań testowych. | Dostarcza funkcję:<br>`chunk_documents(files, config) -> list[DocumentChunk]`. |
| 4 | **Inżynier Wyszukiwania i Rerankingu** | `backend/app/retrieval/`<br>Baza wektorowa (Qdrant) | **Osoba 4** | Integracja bazy wektorowej (Qdrant) i modelu `nomic-embed-text`, indeksowanie BM25, wyszukiwanie hybrydowe (RRF) oraz integracja modelu `BAAI/bge-reranker-base`. | Dostarcza interfejs:<br>`index_chunks(collection_id, chunks)` oraz `search(collection_id, query, config) -> list[ScoredChunk]`. |
| 5 | **Inżynier Ewaluacji** | `backend/app/evaluation/` | **Osoba 5** | Implementacja algorytmów Recall@k i MRR (dopasowanie po `expected_context_snippet`) oraz inżynieria promptów i walidacja JSON dla modelu `qwen3:8b` w roli sędziego (LLM-as-a-Judge). | Dostarcza funkcję:<br>`evaluate(question, ground_truth, retrieved_chunks, answer) -> EvaluationMetrics`. |
| 6 | **Full-stack / Playground & DevOps** | `frontend/pages/3_Playground.py`<br>`frontend/pages/2_Dashboard.py` *(widok mikro)*<br>`docker-compose.yml`<br>`*/Dockerfile` | **Osoba 6** | Budowa widoku szczegółowej inspekcji pytania oraz interfejsu czatu RAG Playground na frontendzie, konfiguracja Docker Compose i wsparcie integracji backend-frontend. | Współpracuje z Osobą 2 na frontendzie i dba o konteneryzację. |

## Przepływ danych

1. Upload dokumentów + testsetu → backend zapisuje pliki i rejestruje pytania w SQLite (Osoba 1 / Osoba 2).
2. Start eksperymentu → backend tworzy zadanie w tle i przekazuje konfiguracje do runnera (Osoba 1).
3. Dla każdej konfiguracji (sekwencyjnie):
   - `chunk_documents` (Osoba 3) → `index_chunks` (Osoba 4, osobna kolekcja wektorowa + indeks BM25),
   - per pytanie: `search` (Osoba 4) → (opcjonalny `rerank`, Osoba 4) → `generate` (Osoba 1 / qwen3:8b), pomiar czasu i tokenów.
4. `evaluate` (Osoba 5): Recall@k, MRR (deterministyczne) + jeden prompt sędziego (poprawność + wierność).
5. Metryki zapisywane w SQLite; frontend odpytuje o status i renderuje dashboard (Osoba 1 / Osoba 2 / Osoba 6).
6. Playground: zapytanie → runner → istniejąca kolekcja → odpowiedź na żywo (Osoba 1 / Osoba 6).

## Kluczowe decyzje projektowe

- **Wzorzec Adaptera dla modeli** (`backend/app/llm/client.py`): ujednolicony interfejs
  kompatybilny z OpenAI API → przejście na komercyjne API bez zmian w logice RAG/eval.
- **Sekwencyjne wywołania LLM** dla modeli lokalnych (`MAX_CONCURRENT_LLM_CALLS=1`) —
  ochrona VRAM (ryzyko #1 w specyfikacji).
- **Trafność po treści cytatu, nie po `chunk_id`** — różne strategie chunkingu dają różne
  identyfikatory; trafienie = chunk zawiera `expected_context_snippet` (pokrycie ≥ 80%).
- **Jeden prompt sędziego** zwracający poprawność + wierność naraz — o połowę mniej wywołań.
- **Osobna kolekcja wektorowa per konfiguracja** — gotowa do użycia w Playground po benchmarku.

## Granice modułów (kontrakty dla niezależnego developmentu)

```python
# Osoba 3 (Ingestion):
ingestion.chunk_documents(files: list[str], config: RagConfig) -> list[DocumentChunk]

# Osoba 4 (Retrieval):
retrieval.index_chunks(collection_id: str, chunks: list[DocumentChunk]) -> None
retrieval.search(collection_id: str, query: str, config: RagConfig) -> list[ScoredChunk]

# Osoba 5 (Evaluation):
evaluation.evaluate(question: str, ground_truth: str, retrieved_chunks: list[ScoredChunk], answer: str) -> EvaluationMetrics

# Osoba 1 (LLM Client):
llm.LLMClient.generate(prompt: str, system: str | None) -> LLMResponse
llm.LLMClient.generate_json(prompt: str, schema: dict, system: str | None) -> dict
```

# Architektura

Modularny monolit z asynchroniczną kolejką zadań w tle, komunikujący się z
lokalnym serwerem modeli (Ollama). Szczegóły w specyfikacji produktowej (sekcja 4).

## Komponenty

| # | Komponent | Katalog | Właściciel |
|---|-----------|---------|-----------|
| 1 | Frontend (Streamlit) | `frontend/` | Osoba 2, Osoba 6 |
| 2 | Backend API & Orchestrator | `backend/app/api`, `backend/app/runner` | Osoba 1 |
| 3 | RAG Execution Engine | `backend/app/ingestion`, `backend/app/retrieval` | Osoba 3, Osoba 4 |
| 4 | Evaluation Engine | `backend/app/evaluation` | Osoba 5 |
| 5 | Local AI Runtime | Ollama (host) + `backend/app/llm` + reranker | Osoba 1, Osoba 4 |
| 6 | Storage | SQLite (`backend/app/db`) + baza wektorowa (Qdrant) | Osoba 1 |

## Przepływ danych

1. Upload dokumentów + testsetu → backend zapisuje pliki i rejestruje pytania w SQLite.
2. Start eksperymentu → backend tworzy zadanie w tle i przekazuje konfiguracje do runnera.
3. Dla każdej konfiguracji (sekwencyjnie):
   - `chunk_documents` → `index_chunks` (osobna kolekcja wektorowa + indeks BM25),
   - per pytanie: `search` → (opcjonalny `rerank`) → `generate` (qwen3:8b), pomiar czasu i tokenów.
4. `evaluate`: Recall@k, MRR (deterministyczne) + jeden prompt sędziego (poprawność + wierność).
5. Metryki zapisywane w SQLite; frontend odpytuje o status i renderuje dashboard.
6. Playground: zapytanie → runner → istniejąca kolekcja → odpowiedź na żywo.

## Kluczowe decyzje projektowe

- **Wzorzec Adaptera dla modeli** (`backend/app/llm/client.py`): ujednolicony interfejs
  kompatybilny z OpenAI API → przejście na komercyjne API bez zmian w logice RAG/eval.
- **Sekwencyjne wywołania LLM** dla modeli lokalnych (`MAX_CONCURRENT_LLM_CALLS=1`) —
  ochrona VRAM (ryzyko #1 w specyfikacji).
- **Trafność po treści cytatu, nie po `chunk_id`** — różne strategie chunkingu dają różne
  identyfikatory; trafienie = chunk zawiera `expected_context_snippet` (pokrycie ≥ 80%).
- **Jeden prompt sędziego** zwracający poprawność + wierność naraz — o połowę mniej wywołań.
- **Osobna kolekcja wektorowa per konfiguracja** — gotowa do użycia w Playground po benchmarku.

## Granice modułów (mogą powstawać niezależnie)

```
ingestion.chunk_documents(files, config)              -> list[DocumentChunk]
retrieval.index_chunks(collection_id, chunks)         -> None
retrieval.search(collection_id, query, config)        -> list[ScoredChunk]
evaluation.evaluate(question, gt, chunks, answer)      -> (RetrievalMetrics, JudgeMetrics)
llm.LLMClient.generate / generate_json / embed
```

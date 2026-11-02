# API REST (v1)

Bazowy prefix: `/api/v1`. Interaktywna dokumentacja (zawsze aktualna): `http://localhost:8000/docs`.
Kształt ciał żądań/odpowiedzi opisują modele Pydantic w `backend/app/schemas/`.

- **Identyfikatory** to UUID (przesyłane jako string).
- **Błędy** mają postać `{"detail": ...}`:
  - błędy domenowe: `detail` to tekst (`404`, `409`, `503`) albo lista `DatasetValidationError`
    (`422` przy wgrywaniu zbioru),
  - błędy walidacji FastAPI (np. brak pola w żądaniu): `422`, `detail` to lista
    `{loc, msg, type}`.
- **Tryb fake:** dopóki ingestion / retrieval / evaluation nie są gotowe (`FAKE_RUNNER=true`),
  worker zapisuje wymyślone, ale wiarygodne wyniki (odpowiedzi z prefiksem `[fake]`). Kształt
  odpowiedzi API jest docelowy — frontend nie musi się zmieniać po podmianie runnera.

`GET /health` (poza prefiksem) → `{"status": "ok"}`, gdy baza jest osiągalna.

---

## 1. Datasets — zbiory danych (US-1)

### `POST /api/v1/datasets`
- **Request:** `multipart/form-data`
  - `documents`: 1..N plików (`.txt`, `.md`, `.pdf`), bez powtórzonych nazw
  - `testset`: 1 plik `.json` (lista obiektów) lub `.csv` (wiersz nagłówka), UTF-8, z polami
    `question`, `ground_truth_answer`, `expected_context_snippet` (niepuste)
  - `name` *(opcjonalne)*: nazwa zbioru, domyślnie nazwa pliku testowego
- **Response `201`:** `DatasetSummary`
  ```json
  { "dataset_id": "…", "name": "demo", "created_at": "2026-11-02T17:51:43Z",
    "document_count": 5, "total_size_bytes": 48211, "question_count": 10 }
  ```
- **Response `422`:** wszystkie błędy naraz, `row` liczony od 1:
  ```json
  { "detail": [
      { "row": 2, "field": "ground_truth_answer", "message": "Field must not be empty." },
      { "row": null, "field": "documents", "message": "Unsupported file type: 'x.docx'." } ] }
  ```

### `GET /api/v1/datasets` → `200`: lista `DatasetSummary`
### `GET /api/v1/datasets/{dataset_id}` → `200`: `DatasetSummary` · `404`

---

## 2. Experiments — konfiguracja i uruchomienie (US-2)

### `POST /api/v1/experiments`
- **Request:** `ExperimentConfig`
  ```json
  {
    "dataset_id": "…",
    "configs": [
      { "label": "A", "chunking": "fixed_tokens", "chunk_size_tokens": 512,
        "chunk_overlap_tokens": 64, "retrieval": "dense", "top_k": 5,
        "reranking_enabled": false },
      { "label": "B", "chunking": "structural", "retrieval": "hybrid",
        "top_k": 5, "reranking_enabled": true }
    ]
  }
  ```
  Walidacja: 2–4 konfiguracje, unikalne `label`, `top_k` 1–50; `fixed_tokens` wymaga
  `chunk_size_tokens` i `chunk_overlap_tokens` (overlap < size); dla `structural` są ignorowane.
- **Response `202`:** `ExperimentProgress` ze `status = "pending"` · `404` nieznany dataset ·
  `503` kolejka zadań niedostępna (eksperyment zostaje oznaczony jako `failed`).

### `GET /api/v1/experiments` → `200`: lista `ExperimentRead`, najnowsze pierwsze
### `GET /api/v1/experiments/{experiment_id}` → `200`: `ExperimentRead` · `404`
```json
{ "experiment_id": "…", "dataset_id": "…", "status": "completed", "error": null,
  "generation_model": "ollama_chat/qwen3:8b", "judge_model": "ollama_chat/qwen3:8b",
  "created_at": "…", "started_at": "…", "finished_at": "…",
  "configs": [ { "label": "A", "chunking": "fixed_tokens", "chunk_size_tokens": 512, "…": "…" } ] }
```

### `GET /api/v1/experiments/{experiment_id}/progress`
Odpytywane cyklicznie (polling co ~1–2 s) dla paska postępu.
- **Response `200`:** `ExperimentProgress`
  ```json
  { "experiment_id": "…", "status": "running",
    "current_config": 2, "total_configs": 4,
    "current_question": 6, "total_questions": 15, "message": null }
  ```
  `status`: `pending` → `indexing` → `running` → `completed` | `failed` (`message` = błąd).
  `current_question` = liczba pytań ukończonych w bieżącej konfiguracji.

---

## 3. Results — wyniki (US-3, US-4)

### `GET /api/v1/experiments/{experiment_id}/results`
- **Response `200`:** `ExperimentResults`. W trakcie eksperymentu zwraca wyniki częściowe
  (to, co już zapisano).
  - `aggregates`: lista `ConfigAggregateResult` → tabela makro
  - `per_question`: lista `QuestionResult` (posortowana po pytaniu, potem konfiguracji) → widok
    mikro, z `retrieved_chunks` (ranking, `contains_expected_snippet`)
  - `answer_correctness` / `faithfulness` mogą być `null`, gdy sędzia LLM zawiódł.

### `GET /api/v1/experiments/{experiment_id}/export?fmt=csv|json` *(Should-have, niezaimplementowane)*

---

## 4. Playground — czat na żywo (US-5)

### `POST /api/v1/playground/ask`
Pytanie do gotowej kolekcji wybranej konfiguracji (bez reindeksacji).
- **Request:** `PlaygroundQuery` — `{ experiment_id, config_label, question }`
- **Response `200`:** `PlaygroundResponse`
  ```json
  { "answer": "…",
    "retrieved_chunks": [ { "chunk": { "chunk_id": "…", "text": "…", "…": "…" }, "score": 0.82, "rank": 1 } ],
    "retrieval_time_ms": 120.5, "generation_time_ms": 3400.0 }
  ```
- `404` nieznany eksperyment lub `config_label` · `409` konfiguracja nie ma jeszcze
  zaindeksowanych chunków (eksperyment nie został uruchomiony).

---

## Otwarte decyzje

1. **Postęp eksperymentu:** polling (obecnie) vs streaming (SSE/WebSocket).
2. **Stały endpoint `POST /api/v1/ask`** (Should-have) — aktywacja wybranej konfiguracji.
3. **Klucz API komercyjny** (Should-have) — per żądanie czy w konfiguracji.

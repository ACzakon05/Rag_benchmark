# Propozycja API REST (v1)

> Status: **do zatwierdzenia na Etapie 1**. To propozycja kontraktu, na którym
> frontend (Streamlit) może pracować równolegle do backendu — na zamockowanych
> odpowiedziach. Bazowy prefix: `/api/v1`.

Pełne, interaktywne schematy wygeneruje FastAPI automatycznie pod `/docs` (Swagger).
Kształt ciał żądań/odpowiedzi opisują modele Pydantic w `backend/app/schemas/`.

---

## 1. Datasets — zbiory danych (US-1)

### `POST /api/v1/datasets`
Wgranie dokumentów + pliku testowego.
- **Request:** `multipart/form-data`
  - `documents`: 1..N plików (`.txt`, `.md`, `.pdf`)
  - `testset`: 1 plik (`.json` lub `.csv`) z polami `question`, `ground_truth_answer`, `expected_context_snippet`
- **Response `201`:** `DatasetSummary` — `{ dataset_id, document_count, total_size_bytes, question_count }`
- **Response `422`:** lista `DatasetValidationError` (brakujące pola / zły format)

### `GET /api/v1/datasets/{dataset_id}`
- **Response `200`:** `DatasetSummary`

---

## 2. Experiments — konfiguracja i uruchomienie (US-2)

### `POST /api/v1/experiments`
Tworzy eksperyment i startuje zadanie w tle.
- **Request:** `ExperimentConfig`
  ```json
  {
    "dataset_id": "ds_abc",
    "configs": [
      { "label": "A", "chunking": "fixed_tokens", "chunk_size_tokens": 512,
        "chunk_overlap_tokens": 64, "retrieval": "dense", "top_k": 5,
        "reranking_enabled": false },
      { "label": "B", "chunking": "structural", "retrieval": "hybrid",
        "top_k": 5, "reranking_enabled": true }
    ]
  }
  ```
  Walidacja: `2 <= len(configs) <= 4`.
- **Response `202`:** `ExperimentProgress` z `experiment_id` i `status = "pending"`.

### `GET /api/v1/experiments/{experiment_id}/progress`
Odpytywane cyklicznie (polling) przez UI dla paska postępu.
- **Response `200`:** `ExperimentProgress`
  ```json
  {
    "experiment_id": "exp_123", "status": "running",
    "current_config": 2, "total_configs": 4,
    "current_question": 6, "total_questions": 15, "message": null
  }
  ```

---

## 3. Results — wyniki (US-3, US-4)

### `GET /api/v1/experiments/{experiment_id}/results`
- **Response `200`:** `ExperimentResults`
  - `aggregates`: lista `ConfigAggregateResult` → tabela makro
  - `per_question`: lista `QuestionResult` → widok mikro (inspekcja)
- Gdy `status != completed` → `409` lub częściowe wyniki (decyzja Etap 1).

### `GET /api/v1/experiments/{experiment_id}/export?fmt=csv|json` *(Should-have)*
Eksport wyników.

---

## 4. Playground — czat na żywo (US-5)

### `POST /api/v1/playground/ask`
Pytanie do gotowego indeksu wybranej konfiguracji (bez reindeksacji).
- **Request:** `PlaygroundQuery` — `{ experiment_id, config_label, question }`
- **Response `200`:** `PlaygroundResponse`
  ```json
  {
    "answer": "...",
    "retrieved_chunks": [ { "chunk": { "...": "..." }, "score": 0.82, "rank": 1 } ],
    "retrieval_time_ms": 120.5,
    "generation_time_ms": 3400.0
  }
  ```

---

## Decyzje do rozstrzygnięcia przy zatwierdzaniu kontraktu

1. **Postęp eksperymentu:** polling (`GET /progress`) vs streaming (SSE/WebSocket).
   Propozycja MVP: polling co ~1–2 s (prostsze, wystarczające).
2. **Identyfikatory:** format `dataset_id` / `experiment_id` (UUID vs krótki slug).
3. **Częściowe wyniki** podczas trwania benchmarku — zwracać czy blokować.
4. **Stały endpoint `POST /api/v1/ask`** (Should-have) — aktywacja wybranej
   konfiguracji jako domyślnej dla aplikacji zewnętrznych.
5. **Klucz API komercyjny** (Should-have) — przekazywany per żądanie czy w konfiguracji eksperymentu.

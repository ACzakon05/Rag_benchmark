# Kontrakty danych (Etap 1 — blokujący)

Źródło prawdy: modele Pydantic w `backend/app/schemas/`. Ten dokument je streszcza.
Zatwierdzenie tych kontraktów odblokowuje pracę równoległą zespołu.

## Plik testowy (wejście od użytkownika)

JSON (lista obiektów) lub CSV (nagłówki = nazwy pól):

```json
[
  {
    "question": "Jaki jest limit X?",
    "ground_truth_answer": "Limit wynosi 100.",
    "expected_context_snippet": "maksymalny limit X to 100 jednostek"
  }
]
```

- `question` — pytanie testowe.
- `ground_truth_answer` — wzorcowa odpowiedź (dla sędziego: Answer Correctness).
- `expected_context_snippet` — krótki, jednoznaczny cytat ze źródła; podstawa Recall@k / MRR.

## Schematy wewnętrzne (`schemas/`)

| Plik | Modele |
|------|--------|
| `config.py` | `ChunkingStrategy`, `RetrievalMethod`, `LLMProvider` |
| `dataset.py` | `TestQuestion`, `DatasetSummary`, `DatasetValidationError` |
| `chunk.py` | `DocumentChunk`, `ScoredChunk` |
| `experiment.py` | `RagConfig`, `ExperimentConfig`, `ExperimentStatus`, `ExperimentProgress` |
| `evaluation.py` | `RetrievalMetrics`, `JudgeMetrics`, `SystemMetrics`, `QuestionResult`, `ConfigAggregateResult`, `ExperimentResults` |
| `playground.py` | `PlaygroundQuery`, `PlaygroundResponse` |

## Otwarte pytania (sekcja 11 specyfikacji)

1. **Język danych** (PL/EN) → wybór wagi rerankera: `bge-reranker-base` (EN) vs `bge-reranker-v2-m3` (PL/multi).
2. **Sprzęt** — czy każdy uciągnie `qwen3:8b`; fallback `qwen3:1.7b` w `.env`.
3. ~~Frontend React vs Streamlit~~ → **zdecydowano: Streamlit**.

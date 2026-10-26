"""Modele bazodanowe (SQLModel) — metadane i wyniki zapisywane w SQLite.

Szkielet — przechowuje: zbiory danych, definicje eksperymentow, konfiguracje,
szczegolowe wyniki ewaluacji oraz historie zapytan Playground.
Wlasciciel: Osoba 1. Do uzgodnienia z kontraktami ze `schemas/` na Etapie 1.

Planowane tabele:
  - Dataset(id, name, document_count, total_size_bytes, question_count, created_at)
  - TestQuestionRow(id, dataset_id, question, ground_truth_answer, expected_context_snippet)
  - Experiment(id, dataset_id, status, created_at)
  - RagConfigRow(id, experiment_id, label, chunking, retrieval, top_k, reranking_enabled, ...)
  - QuestionResultRow(id, experiment_id, config_label, question_id, generated_answer, metryki...)
  - PlaygroundQueryLog(id, experiment_id, config_label, question, answer, created_at)
"""

from __future__ import annotations

# from sqlmodel import SQLModel, Field
# TODO (Etap 1): zdefiniowac tabele zgodnie z opisem powyzej.

"""Klient REST do backendu (Osoba 2/6).

Cienka warstwa nad `requests` mapujaca endpointy z docs/api.md.
Szkielet — bez implementacji. Pozwala budowac UI na zamockowanych danych.
"""

from __future__ import annotations

import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000/api/v1")


def upload_dataset(documents, testset) -> dict:
    """POST /datasets"""
    raise NotImplementedError


def create_experiment(config: dict) -> dict:
    """POST /experiments"""
    raise NotImplementedError


def get_progress(experiment_id: str) -> dict:
    """GET /experiments/{id}/progress"""
    raise NotImplementedError


def get_results(experiment_id: str) -> dict:
    """GET /experiments/{id}/results"""
    raise NotImplementedError


def ask_playground(experiment_id: str, config_label: str, question: str) -> dict:
    """POST /playground/ask"""
    raise NotImplementedError

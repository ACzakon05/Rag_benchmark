"""Klient REST do backendu (Osoba 2/6).

Cienka warstwa nad `requests` mapujaca endpointy z docs/api.md.
Szkielet — bez implementacji. Pozwala budowac UI na zamockowanych danych.
"""

from __future__ import annotations

import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")

REQUEST_TIMEOUT = (5, 120)

class APIClientError(RuntimeError):
    """Error returned by the backend or connection failure."""

def _get_error_detail(response: requests.Response) -> str:
    """Extract a readable error message from the API response."""

    try:
        body = response.json()
    except ValueError:
        return response.text or "Unexpected backend error."

    detail = body.get("detail", body) if isinstance(body, dict) else body

    if isinstance(detail, list):
        messages = []

        for item in detail:
            if isinstance(item, dict):
                location = []

                if item.get("row") is not None:
                    location.append(f"row {item['row']}")

                if item.get("field"):
                    location.append(str(item["field"]))

                message = str(
                    item.get("message", item.get("msg", "Validation error."))
                )

                prefix = ", ".join(location)
                messages.append(f"{prefix}: {message}" if prefix else message)

            else:
                messages.append(str(item))

        return "\n".join(messages)

    return str(detail)



def upload_dataset(documents, testset) -> dict:
    """POST /datasets

    Sends source documents and a validated test set to the backend.
    Returns DatasetSummary, including dataset_id.
    """

    if not documents:
        raise APIClientError("At least one document is required.")

    if testset is None:
        raise APIClientError("A test set is required.")

    files = [
        ("documents", (document.name, document.getvalue()))
        for document in documents
    ]

    files.append(
        ("testset", (testset.name, testset.getvalue()))
    )

    try:
        response = requests.post(
            f"{API_BASE_URL}/datasets",
            files=files,
            timeout=REQUEST_TIMEOUT
        )

    except requests.Timeout as error:
        raise APIClientError(
            "The backend did not respond in time."
        ) from error

    except requests.ConnectionError as error:
        raise APIClientError(
            f"Cannot connect to backend at {API_BASE_URL}. "
            "Check whether the backend is running."
        ) from error

    except requests.RequestException as error:
        raise APIClientError(str(error)) from error

    if not response.ok:
        raise APIClientError(
            f"HTTP {response.status_code}: "
            f"{_get_error_detail(response)}"
        )

    try:
        result = response.json()
    except ValueError as error:
        raise APIClientError(
            "Backend returned an invalid JSON response."
        ) from error

    if not isinstance(result, dict):
        raise APIClientError("Unexpected response format from backend.")

    return result



def _request_json(method: str, path: str, **kwargs) -> dict:
    """makes an HTTP request and returns a JSON response."""

    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            timeout=REQUEST_TIMEOUT,
            **kwargs
        )

    except requests.Timeout as error:
        raise APIClientError(
            "The backend did not respond in time."
        ) from error

    except requests.ConnectionError as error:
        raise APIClientError(
            f"Cannot connect to backend at {API_BASE_URL}."
        ) from error

    except requests.RequestException as error:
        raise APIClientError(str(error)) from error

    if not response.ok:
        raise APIClientError(
            f"HTTP {response.status_code}: "
            f"{_get_error_detail(response)}"
        )

    try:
        result = response.json()
    except ValueError as error:
        raise APIClientError(
            "Backend returned an invalid JSON response."
        ) from error

    if not isinstance(result, dict):
        raise APIClientError(
            "Unexpected response format from backend."
        )

    return result





def create_experiment(config: dict) -> dict:
    """POST /experiments — tworzy i uruchamia eksperyment."""

    return _request_json(
        "POST",
        "/experiments",
        json=config
    )


def get_progress(experiment_id: str) -> dict:
    """GET /experiments/{id}/progress — pobiera postęp."""

    return _request_json(
        "GET",
        f"/experiments/{experiment_id}/progress"
    )


def get_results(experiment_id: str) -> dict:
    """GET /experiments/{id}/results — pobiera wyniki."""

    return _request_json(
        "GET",
        f"/experiments/{experiment_id}/results"
    )



def ask_playground(experiment_id: str, config_label: str, question: str) -> dict:
    """POST /playground/ask"""
    raise NotImplementedError

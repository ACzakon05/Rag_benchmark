
"""Logika konfiguracji eksperymentów RAG.

Odpowiada za:
- domyślne warianty konfiguracji,
- walidację parametrów,
- przygotowanie payloadu dla backendu.
"""

from copy import deepcopy


CHUNKING_STRATEGIES = [
    "fixed_tokens",
    "structural",
]

RETRIEVAL_METHODS = [
    "dense",
    "hybrid",
]

MIN_CONFIGS = 2
MAX_CONFIGS = 4


def get_default_configurations() -> list[dict]:
    """Zwraca dwie przykładowe konfiguracje startowe."""

    return [
        {
            "label": "A",
            "chunking": "fixed_tokens",
            "chunk_size_tokens": 512,
            "chunk_overlap_tokens": 64,
            "retrieval": "dense",
            "top_k": 5,
            "reranking_enabled": False,
        },
        {
            "label": "B",
            "chunking": "structural",
            "chunk_size_tokens": None,
            "chunk_overlap_tokens": None,
            "retrieval": "dense",
            "top_k": 5,
            "reranking_enabled": False,
        },
    ]


def validate_configurations(configurations: list[dict]) -> list[dict]:
    """Waliduje i normalizuje warianty eksperymentu."""

    if not MIN_CONFIGS <= len(configurations) <= MAX_CONFIGS:
        raise ValueError(
            f"Experiment must contain between "
            f"{MIN_CONFIGS} and {MAX_CONFIGS} configurations."
        )

    validated = []
    labels = set()

    for index, config in enumerate(configurations):

        label = str(config.get("label", "")).strip()

        if not 1 <= len(label) <= 32:
            raise ValueError(
                f"Configuration {index + 1}: "
                "label must contain between 1 and 32 characters."
            )

        if label in labels:
            raise ValueError(
                f"Configuration label '{label}' is duplicated."
            )

        labels.add(label)

        chunking = config.get("chunking")

        if chunking not in CHUNKING_STRATEGIES:
            raise ValueError(
                f"Configuration {label}: invalid chunking strategy."
            )

        retrieval = config.get("retrieval")

        if retrieval not in RETRIEVAL_METHODS:
            raise ValueError(
                f"Configuration {label}: invalid retrieval method."
            )

        top_k = config.get("top_k")

        if type(top_k) is not int or not 1 <= top_k <= 50:
            raise ValueError(
                f"Configuration {label}: top_k must be between 1 and 50."
            )

        reranking_enabled = config.get("reranking_enabled")

        if not isinstance(reranking_enabled, bool):
            raise ValueError(
                f"Configuration {label}: reranking_enabled must be boolean."
            )

        normalized = {
            "label": label,
            "chunking": chunking,
            "retrieval": retrieval,
            "top_k": top_k,
            "reranking_enabled": reranking_enabled,
        }

        if chunking == "fixed_tokens":

            chunk_size = config.get("chunk_size_tokens")
            overlap = config.get("chunk_overlap_tokens")

            if type(chunk_size) is not int or chunk_size <= 0:
                raise ValueError(
                    f"Configuration {label}: "
                    "chunk_size_tokens must be greater than 0."
                )

            if type(overlap) is not int or overlap < 0:
                raise ValueError(
                    f"Configuration {label}: "
                    "chunk_overlap_tokens cannot be negative."
                )

            if overlap >= chunk_size:
                raise ValueError(
                    f"Configuration {label}: "
                    "overlap must be smaller than chunk size."
                )

            normalized["chunk_size_tokens"] = chunk_size
            normalized["chunk_overlap_tokens"] = overlap

        validated.append(normalized)

    return validated


def build_experiment_payload(
    dataset_id: str,
    configurations: list[dict]
) -> dict:
    """Buduje payload zgodny z POST /experiments."""

    if not dataset_id:
        raise ValueError("Dataset ID is required.")

    validated = validate_configurations(
        deepcopy(configurations)
    )

    return {
        "dataset_id": str(dataset_id),
        "configs": validated,
    }

import csv
import hashlib
import json
from collections import Counter
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

from lib.api_client import APIClientError, create_experiment, get_progress, upload_dataset
from lib.configurator import (
    CHUNKING_STRATEGIES,
    MAX_CONFIGS,
    MIN_CONFIGS,
    RETRIEVAL_METHODS,
    build_experiment_payload,
    get_default_configurations,
)
from lib.i18n import t, render_language_selector


# --------------------------------------------------
# LANGUAGE
# --------------------------------------------------

render_language_selector()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.header(t("configurator.title"))
st.caption(t("configurator.description"))


# --------------------------------------------------
# 1. DOCUMENT UPLOAD
# --------------------------------------------------

st.subheader(t("documents.title"))

uploaded = st.file_uploader(
    t("documents.upload"),
    type=["pdf", "md", "txt"],
    accept_multiple_files=True,
    help=t("documents.help"),
    key="documents_uploader"
)


# Remove duplicate files using SHA256
def deduplicate_files(files):
    seen = {}
    unique, duplicates = [], []

    for file in files:
        digest = hashlib.sha256(file.getvalue()).hexdigest()

        if digest in seen:
            duplicates.append((file.name, seen[digest]))
        else:
            seen[digest] = file.name
            unique.append(file)

    return unique, duplicates

def calculate_dataset_fingerprint(files, testset):
    digest = hashlib.sha256()

    for file in [*files, testset]:
        digest.update(json.dumps(file.name).encode("utf-8"))
        digest.update(hashlib.sha256(file.getvalue()).digest())

    return digest.hexdigest()

documents, duplicates = deduplicate_files(uploaded or [])

if documents:
    st.success(
        t("documents.count", count=len(documents))
    )

if duplicates:
    duplicate_messages = [
        t(
            "documents.duplicate_item",
            duplicate=duplicate,
            original=original
        )
        for duplicate, original in duplicates
    ]

    st.warning(
        t("documents.duplicates")
        + "\n\n"
        + "\n".join(duplicate_messages)
    )


# --------------------------------------------------
# 2. TEST SET UPLOAD AND VALIDATION
# --------------------------------------------------

st.subheader(t("testset.title"))

testset = st.file_uploader(
    t("testset.upload"),
    type=["json", "csv"],
    help=t("testset.help"),
    key="testset_uploader"
)

REQUIRED_FIELDS = [
    "question",
    "ground_truth_answer",
    "expected_context_snippet"
]

def read_questions(file):
    content = file.getvalue().decode("utf-8-sig")
    if Path(file.name).suffix.lower() == ".json":
        rows = json.loads(content)
        if not isinstance(rows, list):
            raise ValueError(t("testset.invalid_type"))
    else:
        reader = csv.DictReader(StringIO(content))
        missing = [field for field in REQUIRED_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(t("testset.missing_fields", fields=", ".join(missing)))
        rows = list(reader)

    if not rows:
        raise ValueError(t("testset.empty"))

    questions = []
    for number, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(t("testset.invalid_row", row=number))
        missing = [field for field in REQUIRED_FIELDS if field not in row or row[field] is None]
        if missing:
            raise ValueError(t("testset.row_missing_fields", row=number, fields=", ".join(missing)))
        for field in REQUIRED_FIELDS:
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(t("testset.invalid_value", row=number, field=field))
        questions.append({field: row[field] for field in REQUIRED_FIELDS})
    return pd.DataFrame(questions)


duplicate_names = sorted(
    name for name, count in Counter(Path(doc.name).name for doc in documents).items()
    if count > 1
)
if duplicate_names:
    st.error(t("documents.duplicate_names", names=", ".join(duplicate_names)))

questions_df = None
if testset is not None:
    try:
        questions_df = read_questions(testset)
    except (ValueError, csv.Error) as error:
        st.error(t("testset.invalid", error=str(error)))
    else:
        st.success(t("testset.success", count=len(questions_df)))
        with st.expander(t("testset.preview")):
            st.dataframe(questions_df, width="stretch")


# --------------------------------------------------
# 3. DATASET SUMMARY
# --------------------------------------------------

st.divider()
st.subheader(t("summary.title"))

if documents and not duplicate_names and questions_df is not None:

    total_size = sum(
        len(document.getvalue())
        for document in documents
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        t("summary.documents"),
        len(documents)
    )

    col2.metric(
        t("summary.size"),
        f"{total_size / 1024:.1f} KB"
    )

    col3.metric(
        t("summary.questions"),
        len(questions_df)
    )

    st.success(t("summary.ready"))

else:
    st.info(t("summary.waiting"))




# --------------------------------------------------
# 4. SEND DATASET TO BACKEND
# --------------------------------------------------

valid_dataset = (
    bool(documents)
    and not duplicate_names
    and testset is not None
    and questions_df is not None
)

current_fingerprint = (
    calculate_dataset_fingerprint(documents, testset)
    if valid_dataset
    else None
)

# Invalidate the previous backend dataset if files changed.
if st.session_state.get("uploaded_dataset_fingerprint") != current_fingerprint:
    st.session_state.pop("dataset_id", None)
    st.session_state.pop("backend_dataset_summary", None)

    st.session_state["uploaded_dataset_fingerprint"] = current_fingerprint


if valid_dataset:

    backend_summary = st.session_state.get("backend_dataset_summary")
    if backend_summary is None and st.button(
        t("dataset.upload_to_backend"), type="primary", key="send_dataset_to_backend"
    ):
        try:
            with st.spinner(t("dataset.sending")):
                backend_summary = upload_dataset(documents, testset)
                dataset_id = backend_summary.get("dataset_id")
                if not isinstance(dataset_id, str) or not dataset_id:
                    raise APIClientError(t("dataset.missing_id"))
            st.session_state["dataset_id"] = dataset_id
            st.session_state["backend_dataset_summary"] = backend_summary
        except APIClientError as error:
            backend_summary = None
            st.error(t("dataset.upload_error", error=str(error)))

    if backend_summary is not None:
        st.success(t("dataset.uploaded"))
        st.caption(t("dataset.backend_id", dataset_id=backend_summary["dataset_id"]))


ACTIVE_STATUSES = {"pending", "indexing", "running"}


def render_configuration(defaults):
    label = defaults["label"]
    prefix = f"benchmark_{label}"
    chunking = st.selectbox(
        t("variants.chunking"),
        CHUNKING_STRATEGIES,
        index=CHUNKING_STRATEGIES.index(defaults["chunking"]),
        format_func=lambda option: t(f"variants.{option}"),
        key=f"{prefix}_chunking",
    )
    config = {"label": label, "chunking": chunking}
    if chunking == "fixed_tokens":
        for field, minimum, fallback in (
            ("chunk_size_tokens", 1, 512),
            ("chunk_overlap_tokens", 0, 64),
        ):
            key = f"{prefix}_{field}"
            value = st.number_input(
                t(f"variants.{field}"), min_value=minimum, value=defaults[field] or fallback,
                key=key,
            )
            config[field] = value
    config["retrieval"] = st.selectbox(
        t("variants.retrieval"),
        RETRIEVAL_METHODS,
        index=RETRIEVAL_METHODS.index(defaults["retrieval"]),
        format_func=lambda option: t(f"variants.{option}"),
        key=f"{prefix}_retrieval",
    )
    config["top_k"] = st.number_input(
        t("variants.top_k"), min_value=1, max_value=50, value=defaults["top_k"],
        key=f"{prefix}_top_k",
    )
    config["reranking_enabled"] = st.checkbox(
        t("variants.reranking"), value=defaults["reranking_enabled"], key=f"{prefix}_reranking",
    )
    return config


st.divider()
st.subheader(t("variants.title"))
count = st.selectbox(
    t("variants.count"), range(MIN_CONFIGS, MAX_CONFIGS + 1), key="benchmark_config_count"
)
defaults = get_default_configurations()[:count]
tabs = st.tabs([config["label"] for config in defaults])
configurations = []
for tab, variant in zip(tabs, defaults, strict=True):
    with tab:
        configurations.append(render_configuration(variant))

dataset_id = st.session_state.get("dataset_id")
progress = st.session_state.get("experiment_progress")
active = progress is not None and progress["status"] in ACTIVE_STATUSES
if dataset_id is None:
    st.info(t("benchmark.requires_dataset"))

if st.button(
    t("benchmark.start"), type="primary", key="start_benchmark",
    disabled=dataset_id is None or active,
):
    try:
        payload = build_experiment_payload(dataset_id, configurations)
        with st.spinner(t("benchmark.starting")):
            progress = create_experiment(payload)
            experiment_id = progress.get("experiment_id")
            if not isinstance(experiment_id, str) or not experiment_id:
                raise APIClientError(t("benchmark.missing_id"))
        st.session_state["experiment_id"] = experiment_id
        st.session_state["experiment_progress"] = progress
        st.rerun()
    except (ValueError, APIClientError) as error:
        st.error(t("benchmark.start_error", error=str(error)))


@st.fragment(run_every=2 if active else None)
def render_progress():
    progress = st.session_state["experiment_progress"]
    experiment_id = st.session_state["experiment_id"]
    st.subheader(t("benchmark.progress"))
    st.caption(t("benchmark.id", experiment_id=experiment_id))

    if active:
        try:
            progress = get_progress(experiment_id)
            st.session_state["experiment_progress"] = progress
        except APIClientError as error:
            st.warning(t("benchmark.poll_error", error=str(error)))
        else:
            if progress["status"] not in ACTIVE_STATUSES:
                st.rerun()

    status = progress["status"]
    current_config = progress["current_config"]
    total_configs = progress["total_configs"]
    current_question = progress["current_question"]
    total_questions = progress["total_questions"]
    fraction = 0.0
    if status == "completed":
        fraction = 1.0
    elif current_config and total_configs and total_questions:
        completed = (current_config - 1) * total_questions + current_question
        fraction = min(1.0, completed / (total_configs * total_questions))

    st.progress(fraction, text=t(f"benchmark.{status}"))
    if status == "running":
        st.caption(t(
            "benchmark.counters", config=current_config, configs=total_configs,
            question=current_question, questions=total_questions,
        ))
    if status == "failed":
        st.error(progress.get("message") or t("benchmark.failed"))
    elif status == "completed":
        st.success(t("benchmark.completed"))


if progress is not None:
    render_progress()

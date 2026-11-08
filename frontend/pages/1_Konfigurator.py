
from lib.api_client import upload_dataset, APIClientError
import json
import hashlib
from io import BytesIO

import pandas as pd
import streamlit as st

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

    for file in files:
        digest.update(file.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.getvalue())

    digest.update(testset.name.encode("utf-8"))
    digest.update(b"\0")
    digest.update(testset.getvalue())

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

questions_df = None
validation_error = None

if testset:
    try:
        file_content = testset.getvalue()

        if testset.name.endswith(".json"):
            questions = json.loads(
                file_content.decode("utf-8")
            )

            if not isinstance(questions, list):
                raise ValueError(
                    t("testset.invalid_type")
                )

            questions_df = pd.DataFrame(questions)

        else:
            questions_df = pd.read_csv(
                BytesIO(file_content)
            )

        # Check required columns
        missing_fields = [
            field for field in REQUIRED_FIELDS
            if field not in questions_df.columns
        ]

        if missing_fields:
            raise ValueError(
                t(
                    "testset.missing_fields",
                    fields=", ".join(missing_fields)
                )
            )

        # Check empty values
        for field in REQUIRED_FIELDS:
            values = questions_df[field]

            invalid = (
                values.isna()
                | values.astype(str).str.strip().eq("")
            )

            if invalid.any():
                rows = list(
                    questions_df.index[invalid] + 1
                )

                raise ValueError(
                    t(
                        "testset.empty_values",
                        field=field,
                        rows=rows
                    )
                )

        if questions_df.empty:
            raise ValueError(
                t("testset.empty")
            )

        st.success(
            t(
                "testset.success",
                count=len(questions_df)
            )
        )

        with st.expander(t("testset.preview")):
            st.dataframe(
                questions_df,
                use_container_width=True
            )

    except (
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError
    ) as error:

        validation_error = str(error)
        questions_df = None

    if validation_error:
        st.error(
            t(
                "testset.invalid",
                error=validation_error
            )
        )


# --------------------------------------------------
# 3. DATASET SUMMARY
# --------------------------------------------------

st.divider()
st.subheader(t("summary.title"))

if documents and questions_df is not None:

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

    if backend_summary is None:

        if st.button(
            t("dataset.upload_to_backend"),
            type="primary",
            key="send_dataset_to_backend"
        ):

            try:
                with st.spinner(t("dataset.sending")):
                    backend_summary = upload_dataset(
                        documents,
                        testset
                    )

                st.session_state["dataset_id"] = (
                    backend_summary["dataset_id"]
                )

                st.session_state["backend_dataset_summary"] = (
                    backend_summary
                )

                st.success(t("dataset.uploaded"))

                st.caption(
                    t(
                        "dataset.backend_id",
                        dataset_id=backend_summary["dataset_id"]
                    )
                )

            except APIClientError as error:
                st.error(
                    t(
                        "dataset.upload_error",
                        error=str(error)
                    )
                )

    else:
        st.success(t("dataset.uploaded"))

        st.caption(
            t(
                "dataset.backend_id",
                dataset_id=backend_summary["dataset_id"]
            )
        )


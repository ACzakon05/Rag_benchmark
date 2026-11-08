
import streamlit as st


TRANSLATIONS = {
    "en": {
        "language": "Language",
        "english": "English",
        "polish": "Polski",

        "configurator.title": "Experiment configurator",
        "configurator.description": (
            "Prepare source documents and a test question set "
            "for your RAG benchmark."
        ),

        "documents.title": "1. Source documents",
        "documents.upload": "Upload documents",
        "documents.help": "You can select multiple documents.",
        "documents.count": "Number of documents: {count}",
        "documents.duplicates": "Duplicate files were skipped:",
        "documents.duplicate_item": (
            "- `{duplicate}` is identical to `{original}`"
        ),

        "testset.title": "2. Test question set",
        "testset.upload": "Upload test set",
        "testset.help": (
            "Required fields: question, ground_truth_answer, "
            "expected_context_snippet."
        ),
        "testset.invalid_type": "The JSON file must contain a list of questions.",
        "testset.missing_fields": "Missing required fields: {fields}",
        "testset.empty_values": (
            "Field '{field}' contains empty values "
            "(rows: {rows})."
        ),
        "testset.empty": "The test set does not contain any questions.",
        "testset.success": "Successfully loaded {count} questions.",
        "testset.preview": "Preview questions",
        "testset.invalid": "Invalid test set: {error}",

        "summary.title": "3. Dataset summary",
        "summary.documents": "Documents",
        "summary.size": "Document size",
        "summary.questions": "Questions",
        "summary.ready": "Dataset is ready for configuration.",
        "summary.waiting": (
            "Upload documents and a valid test set "
            "to see the dataset summary."
        ),

        "dataset.upload_to_backend": "Send dataset to backend",
        "dataset.sending": "Uploading dataset...",
        "dataset.uploaded": "Dataset successfully saved on backend.",
        "dataset.backend_id": "Dataset ID: {dataset_id}",
        "dataset.upload_error": "Dataset upload failed: {error}",




    },

    "pl": {
        "language": "Język",
        "english": "English",
        "polish": "Polski",

        "configurator.title": "Konfigurator eksperymentu",
        "configurator.description": (
            "Przygotuj dokumenty źródłowe i zestaw pytań "
            "do przeprowadzenia benchmarku RAG."
        ),

        "documents.title": "1. Dokumenty źródłowe",
        "documents.upload": "Wybierz dokumenty",
        "documents.help": "Możesz wybrać kilka dokumentów jednocześnie.",
        "documents.count": "Liczba dokumentów: {count}",
        "documents.duplicates": "Pominięto duplikaty:",
        "documents.duplicate_item": (
            "- `{duplicate}` jest identyczny z `{original}`"
        ),

        "testset.title": "2. Zestaw pytań testowych",
        "testset.upload": "Wybierz plik z pytaniami",
        "testset.help": (
            "Wymagane pola: question, ground_truth_answer, "
            "expected_context_snippet."
        ),
        "testset.invalid_type": "Plik JSON musi zawierać listę pytań.",
        "testset.missing_fields": "Brak wymaganych pól: {fields}",
        "testset.empty_values": (
            "Pole '{field}' zawiera puste wartości "
            "(wiersze: {rows})."
        ),
        "testset.empty": "Testset nie zawiera żadnych pytań.",
        "testset.success": "Poprawnie wczytano {count} pytań.",
        "testset.preview": "Podgląd pytań",
        "testset.invalid": "Niepoprawny testset: {error}",

        "summary.title": "3. Podsumowanie zbioru",
        "summary.documents": "Liczba dokumentów",
        "summary.size": "Rozmiar dokumentów",
        "summary.questions": "Liczba pytań",
        "summary.ready": "Zbiór danych jest gotowy do konfiguracji.",
        "summary.waiting": (
            "Wybierz dokumenty oraz poprawny plik testowy, "
            "aby zobaczyć podsumowanie."
        ),

        "dataset.upload_to_backend": "Wyślij zbiór do backendu",
        "dataset.sending": "Wysyłanie zbioru danych...",
        "dataset.uploaded": "Zbiór danych został zapisany w backendzie.",
        "dataset.backend_id": "ID zbioru danych: {dataset_id}",
        "dataset.upload_error": "Nie udało się wysłać zbioru: {error}",
    }
}


def t(key, **kwargs):
    """Return a translated UI string."""
    language = st.session_state.get("language", "en")

    translation = TRANSLATIONS[language].get(key, key)

    return translation.format(**kwargs)


def render_language_selector():
    """Display a language selector in the sidebar."""

    languages = {
        "en": "English",
        "pl": "Polski"
    }

    st.sidebar.selectbox(
        t("language"),
        options=list(languages.keys()),
        format_func=lambda language: languages[language],
        key="language"
    )

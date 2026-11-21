
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

        "documents.duplicate_names": "Documents must have unique names: {names}",
        "testset.invalid_row": "Row {row} must be an object.",
        "testset.row_missing_fields": "Row {row} is missing fields: {fields}",
        "testset.invalid_value": "Row {row}: field '{field}' must contain non-empty text.",
        "dataset.missing_id": "The backend response did not include a dataset ID.",
        "variants.title": "4. RAG configurations",
        "variants.count": "Number of configurations",
        "variants.chunking": "Chunking strategy",
        "variants.fixed_tokens": "Fixed token count",
        "variants.structural": "Document structure",
        "variants.chunk_size_tokens": "Chunk size (tokens)",
        "variants.chunk_overlap_tokens": "Chunk overlap (tokens)",
        "variants.retrieval": "Retrieval method",
        "variants.dense": "Vector search (Dense)",
        "variants.hybrid": "Hybrid search (Dense + BM25)",
        "variants.top_k": "Number of retrieved chunks (k)",
        "variants.reranking": "Enable reranking",
        "benchmark.requires_dataset": "Send the dataset to the backend to run a benchmark.",
        "benchmark.start": "Run benchmark",
        "benchmark.starting": "Starting the benchmark…",
        "benchmark.missing_id": "The backend response did not include an experiment ID.",
        "benchmark.start_error": "Could not start the benchmark: {error}",
        "benchmark.progress": "Benchmark progress",
        "benchmark.id": "Experiment ID: {experiment_id}",
        "benchmark.poll_error": "Could not refresh progress. Retrying automatically. {error}",
        "benchmark.pending": "Waiting in the queue",
        "benchmark.indexing": "Indexing documents",
        "benchmark.running": "Benchmark in progress",
        "benchmark.completed": "Benchmark completed",
        "benchmark.failed": "Benchmark failed",
        "benchmark.counters": "Configuration {config}/{configs}, questions completed {question}/{questions}",
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

        "documents.duplicate_names": "Nazwy dokumentów muszą być unikalne: {names}",
        "testset.invalid_row": "Wiersz {row} musi być obiektem.",
        "testset.row_missing_fields": "Brak pól w wierszu {row}: {fields}",
        "testset.invalid_value": "Wiersz {row}: pole „{field}” musi zawierać niepusty tekst.",
        "dataset.missing_id": "Odpowiedź backendu nie zawiera identyfikatora zbioru.",
        "variants.title": "4. Warianty RAG",
        "variants.count": "Liczba wariantów",
        "variants.chunking": "Strategia dzielenia dokumentów",
        "variants.fixed_tokens": "Stała liczba tokenów",
        "variants.structural": "Struktura dokumentu",
        "variants.chunk_size_tokens": "Rozmiar fragmentu (tokeny)",
        "variants.chunk_overlap_tokens": "Nakładanie fragmentów (tokeny)",
        "variants.retrieval": "Metoda wyszukiwania",
        "variants.dense": "Wektorowe (Dense)",
        "variants.hybrid": "Hybrydowe (Dense + BM25)",
        "variants.top_k": "Liczba pobieranych fragmentów (k)",
        "variants.reranking": "Włącz reranking",
        "benchmark.requires_dataset": "Wyślij zbiór do backendu, aby uruchomić benchmark.",
        "benchmark.start": "Uruchom benchmark",
        "benchmark.starting": "Uruchamianie benchmarku…",
        "benchmark.missing_id": "Odpowiedź backendu nie zawiera identyfikatora eksperymentu.",
        "benchmark.start_error": "Nie udało się uruchomić benchmarku: {error}",
        "benchmark.progress": "Postęp benchmarku",
        "benchmark.id": "ID eksperymentu: {experiment_id}",
        "benchmark.poll_error": "Nie udało się odświeżyć postępu. Ponawiam automatycznie. {error}",
        "benchmark.pending": "Oczekiwanie w kolejce",
        "benchmark.indexing": "Indeksowanie dokumentów",
        "benchmark.running": "Benchmark w toku",
        "benchmark.completed": "Benchmark ukończony",
        "benchmark.failed": "Benchmark zakończył się błędem",
        "benchmark.counters": "Wariant {config}/{configs}, ukończone pytania {question}/{questions}",
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

"""Testy ekstrakcji tekstu z plików .txt, .md i .pdf."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ingestion import extractor
from app.ingestion.extractor import extract_pdf_pages, extract_text


def _minimal_pdf_bytes(text: str) -> bytes:
    """Buduje poprawny, minimalny 1-stronicowy PDF z tekstem ASCII do testu pypdf."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        (
            f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1")
            + stream
            + b"\nendstream endobj\n"
        ),
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for offset in offsets:
        out.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    trailer = f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    out.extend(trailer.encode("latin-1"))
    return bytes(out)


def test_extract_txt_with_polish_chars_and_crlf(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_bytes("Zażółć gęślą jaźń.\r\n\r\n\r\nDrugi akapit.   \r\n".encode("utf-8-sig"))

    assert extract_text(path) == "Zażółć gęślą jaźń.\n\nDrugi akapit."


def test_extract_md_preserves_headings(tmp_path: Path) -> None:
    path = tmp_path / "readme.md"
    path.write_text("# Tytuł\n\n## Sekcja\nTreść sekcji.\n", encoding="utf-8")

    assert extract_text(path) == "# Tytuł\n\n## Sekcja\nTreść sekcji."


def test_extract_cp1250_fallback(tmp_path: Path) -> None:
    path = tmp_path / "legacy.txt"
    path.write_bytes("Łódź i Kraków".encode("cp1250"))

    assert extract_text(path) == "Łódź i Kraków"


def test_extract_real_pdf(tmp_path: Path) -> None:
    path = tmp_path / "sample.pdf"
    path.write_bytes(_minimal_pdf_bytes("Limit wynosi 100 jednostek."))

    assert extract_text(path) == "Limit wynosi 100 jednostek."
    assert extract_pdf_pages(path) == [(1, "Limit wynosi 100 jednostek.")]


def test_extract_pdf_skips_empty_pages_and_keeps_numbers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "multi.pdf"
    path.write_bytes(b"%PDF-1.4")

    fake_reader = SimpleNamespace(
        is_encrypted=False,
        pages=[
            SimpleNamespace(extract_text=lambda: "Strona pierwsza."),
            SimpleNamespace(extract_text=lambda: "   \n "),
            SimpleNamespace(extract_text=lambda: "Strona trzecia."),
        ],
    )
    monkeypatch.setattr(extractor, "PdfReader", lambda _p: fake_reader)

    assert extract_pdf_pages(path) == [(1, "Strona pierwsza."), (3, "Strona trzecia.")]
    assert extract_text(path) == "Strona pierwsza.\n\nStrona trzecia."


def test_encrypted_pdf_raises_clear_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "secret.pdf"
    path.write_bytes(b"%PDF-1.4")

    fake_reader = SimpleNamespace(is_encrypted=True, decrypt=lambda _pw: 0, pages=[])
    monkeypatch.setattr(extractor, "PdfReader", lambda _p: fake_reader)

    with pytest.raises(ValueError, match="encrypted"):
        extract_text(path)


def test_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        extract_text(tmp_path / "missing.txt")


def test_unsupported_extension_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "notes.docx"
    path.write_text("abc", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        extract_text(path)


def test_extract_pdf_pages_rejects_non_pdf(tmp_path: Path) -> None:
    path = tmp_path / "plain.txt"
    path.write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a .pdf"):
        extract_pdf_pages(path)


def test_extract_text_replaces_undecodable_bytes(tmp_path: Path) -> None:
    path = tmp_path / "broken.txt"
    # 0x81 is undefined in cp1250 and invalid in UTF-8, forcing the final fallback.
    path.write_bytes(b"ok \x81 end")

    text = extract_text(path)
    assert text.startswith("ok ")
    assert text.endswith(" end")

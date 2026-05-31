"""File reading utilities for PDF, DOCX, and plain text."""

from pathlib import Path

import PyPDF2
import docx


def read_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    import io

    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def read_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    import io

    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs).strip()


def read_file(file_bytes: bytes, filename: str) -> str:
    """Read uploaded file and return plain text content."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return read_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return read_docx(file_bytes)
    else:
        return file_bytes.decode("utf-8", errors="ignore").strip()

"""Extract supported document formats and create translated output files."""
from __future__ import annotations

from pathlib import Path


def extract_document(path: str) -> tuple[str, str]:
    suffix = Path(path).suffix.lower()
    if suffix == ".txt":
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
        if not text:
            raise ValueError("This PDF has no selectable text. It appears scanned; convert it with OCR to a text PDF first.")
    elif suffix == ".docx":
        from docx import Document
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text.strip() for cell in row.cells))
        text = "\n".join(paragraphs)
    else:
        raise ValueError("Supported document formats are PDF, DOCX, and TXT.")
    if not text.strip():
        raise ValueError("The document did not contain extractable text.")
    return text, suffix


def write_translated_document(translated: str, source_format: str, output_path: str) -> str:
    """Write DOCX when the input was DOCX; PDF/TXT output is plain UTF-8 text."""
    if source_format == ".docx":
        from docx import Document
        doc = Document()
        for line in translated.splitlines():
            doc.add_paragraph(line)
        doc.save(output_path)
    else:
        Path(output_path).write_text(translated, encoding="utf-8")
    return output_path

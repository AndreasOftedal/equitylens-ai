from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class ParsedPage:
    document_id: str
    page_number: int
    text: str


def parse_pdf(document_id: str, pdf_path: Path) -> list[ParsedPage]:
    """Extract page-level text from a PDF while preserving provenance."""

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages: list[ParsedPage] = []

    with pymupdf.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf):
            text = page.get_text("text").strip()

            pages.append(
                ParsedPage(
                    document_id=document_id,
                    page_number=page_index + 1,
                    text=text,
                )
            )

    return pages
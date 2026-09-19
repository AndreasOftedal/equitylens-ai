from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

DocumentType = Literal[
    "annual_report",
    "quarterly_report",
    "earnings_release",
    "investor_presentation",
    "transcript",
]


@dataclass(frozen=True)
class Document:
    document_id: str
    company: str
    ticker: str
    document_type: DocumentType
    reporting_period: str
    publication_date: date
    source_url: str
    local_path: Path


@dataclass(frozen=True)
class ParsedTable:
    document_id: str
    page_number: int
    table_number: int
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class EvidenceRef:
    document_id: str
    page_number: int
    table_number: int | None = None
    row_label: str | None = None
    column_label: str | None = None


@dataclass(frozen=True)
class FinancialFact:
    fact_id: str
    metric: str
    period: str
    value: Decimal
    unit: str
    evidence: EvidenceRef
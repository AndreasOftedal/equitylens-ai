from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from equitylens.documents import EQUINOR_Q1_2026, EQUINOR_Q2_2026
from equitylens.models import Document, EvidenceRef, FinancialFact


def test_document_stores_source_metadata():
    document = Document(
        document_id="equinor-q2-2026-quarterly-report",
        company="Equinor ASA",
        ticker="EQNR",
        document_type="quarterly_report",
        reporting_period="Q2 2026",
        publication_date=date(2026, 7, 22),
        source_url="https://example.com/report.pdf",
        local_path=Path("data/raw/equinor/report.pdf"),
    )

    assert document.company == "Equinor ASA"
    assert document.reporting_period == "Q2 2026"
    assert document.document_type == "quarterly_report"


@pytest.mark.integration
def test_equinor_q1_2026_source_exists():
    assert EQUINOR_Q1_2026.local_path.exists()
    assert EQUINOR_Q1_2026.local_path.suffix == ".pdf"
    assert EQUINOR_Q1_2026.reporting_period == "Q1 2026"


@pytest.mark.integration
def test_equinor_q2_2026_source_exists():
    assert EQUINOR_Q2_2026.local_path.exists()
    assert EQUINOR_Q2_2026.local_path.suffix == ".pdf"
    assert EQUINOR_Q2_2026.reporting_period == "Q2 2026"


def test_financial_fact_preserves_evidence():
    evidence = EvidenceRef(
        document_id=EQUINOR_Q2_2026.document_id,
        page_number=39,
        table_number=1,
        row_label="Average daily rate",
        column_label="Q2 2026",
    )

    fact = FinancialFact(
        fact_id="equinor-usd-nok-average-rate-q2-2026",
        metric="USD/NOK average daily rate",
        period="Q2 2026",
        value=Decimal("9.4240"),
        unit="NOK per USD",
        evidence=evidence,
    )

    assert fact.value == Decimal("9.4240")
    assert fact.period == "Q2 2026"
    assert fact.evidence.page_number == 39
    assert fact.evidence.table_number == 1
    assert fact.evidence.column_label == "Q2 2026"
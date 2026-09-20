from datetime import date
from pathlib import Path

from equitylens.models import Document

EQUINOR_Q1_2026 = Document(
    document_id="equinor-q1-2026-financial-statements-and-review",
    company="Equinor ASA",
    ticker="EQNR",
    document_type="quarterly_report",
    reporting_period="Q1 2026",
    publication_date=date(2026, 5, 6),
    source_url="https://www.equinor.com/investors/quarterly-results",
    local_path=Path(
        "data/raw/equinor/equinor_q1_2026_financial_statements_and_review.pdf"
    ),
)


EQUINOR_Q2_2026 = Document(
    document_id="equinor-q2-2026-financial-statements-and-review",
    company="Equinor ASA",
    ticker="EQNR",
    document_type="quarterly_report",
    reporting_period="Q2 2026",
    publication_date=date(2026, 7, 22),
    source_url="https://www.equinor.com/investors/quarterly-results",
    local_path=Path(
        "data/raw/equinor/equinor_q2_2026_financial_statements_and_review.pdf"
    ),
)


AKER_BP_Q1_2026 = Document(
    document_id="aker-bp-q1-2026-report",
    company="Aker BP ASA",
    ticker="AKRBP",
    document_type="quarterly_report",
    reporting_period="Q1 2026",
    publication_date=date(2026, 5, 7),
    source_url=(
        "https://akerbp.com/borsmelding/"
        "first-quarter-2026-results/"
    ),
    local_path=Path(
        "data/raw/aker_bp/aker_bp_q1_2026_report.pdf"
    ),
)


AKER_BP_Q2_2026 = Document(
    document_id="aker-bp-q2-2026-report",
    company="Aker BP ASA",
    ticker="AKRBP",
    document_type="quarterly_report",
    reporting_period="Q2 2026",
    publication_date=date(2026, 7, 15),
    source_url=(
        "https://akerbp.com/borsmelding/"
        "second-quarter-2026-results/"
    ),
    local_path=Path(
        "data/raw/aker_bp/aker_bp_q2_2026_report.pdf"
    ),
)
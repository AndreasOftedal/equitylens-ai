from datetime import date
from pathlib import Path

from equitylens.models import Document

EQUINOR_Q2_2026 = Document(
    document_id="equinor-q2-2026-financial-statements-and-review",
    company="Equinor ASA",
    ticker="EQNR",
    document_type="quarterly_report",
    reporting_period="Q2 2026",
    publication_date=date(2026, 7, 22),
    source_url=(
        "https://www.equinor.com/investors/quarterly-results"
    ),
    local_path=Path(
        "data/raw/equinor/"
        "equinor_q2_2026_financial_statements_and_review.pdf"
    ),
)
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentSource:
    document_id: str
    download_url: str
    local_path: Path
    sha256: str


EQUINOR_Q1_2026_SOURCE = DocumentSource(
    document_id="equinor-q1-2026-financial-statements-and-review",
    download_url=(
        "https://cdn.equinor.com/files/h61q9gi9/global/"
        "53aaf7c1ee7944aea232befdf1c95d6c872a6a76.pdf"
        "?q1-2026-financial-statements-and-review-equinor.pdf="
    ),
    local_path=Path(
        "data/raw/equinor/equinor_q1_2026_financial_statements_and_review.pdf"
    ),
    sha256="06694e7a21d408a4badab11ac18e9f5277d7f8602edc2b513840b475517cf0de",
)


EQUINOR_Q2_2026_SOURCE = DocumentSource(
    document_id="equinor-q2-2026-financial-statements-and-review",
    download_url=(
        "https://cdn.equinor.com/files/h61q9gi9/global/"
        "c0440c05d52a88d521781730b795e0bb635703ba.pdf"
        "?q2-2026-financial-statements-and-review-equinor.pdf="
    ),
    local_path=Path(
        "data/raw/equinor/equinor_q2_2026_financial_statements_and_review.pdf"
    ),
    sha256="0089fd824e5c93a65922ef343ee96a962a7d30c60f79d7d2336e40ea7d0fa293",
)


EQUINOR_SOURCES = (
    EQUINOR_Q1_2026_SOURCE,
    EQUINOR_Q2_2026_SOURCE,
)
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


AKER_BP_Q1_2026_SOURCE = DocumentSource(
    document_id="aker-bp-q1-2026-report",
    download_url=(
        "https://akerbp.com/wp-content/uploads/2026/04/"
        "aker-bp-2026-q1-report.pdf"
    ),
    local_path=Path(
        "data/raw/aker_bp/aker_bp_q1_2026_report.pdf"
    ),
    sha256="f5eb705f3a1b41ecc1cfad91c83b582c352138a42b270cee2fc7ca9433870726",
)


AKER_BP_Q2_2026_SOURCE = DocumentSource(
    document_id="aker-bp-q2-2026-report",
    download_url=(
        "https://mb.cision.com/Public/1629/4374189/"
        "9113084bda5ee923.pdf"
    ),
    local_path=Path(
        "data/raw/aker_bp/aker_bp_q2_2026_report.pdf"
    ),
    sha256="612f278be984b2b4f11aa5fae63037748dab423e2e7984e82c33c5c6e8159df2",
)


AKER_BP_SOURCES = (
    AKER_BP_Q1_2026_SOURCE,
    AKER_BP_Q2_2026_SOURCE,
)


ALL_SOURCES = (
    *EQUINOR_SOURCES,
    *AKER_BP_SOURCES,
)
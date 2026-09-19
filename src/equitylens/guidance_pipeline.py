from collections.abc import Iterable

from equitylens.capital_distribution_guidance import (
    extract_equinor_share_buyback_guidance,
)
from equitylens.guidance import GuidanceItem
from equitylens.guidance_extractor import (
    extract_equinor_formal_outlook_guidance,
)
from equitylens.guidance_report import (
    GuidanceReport,
    build_guidance_report,
)
from equitylens.parser import ParsedPage


def extract_equinor_guidance(
    document_id: str,
    pages: Iterable[ParsedPage],
) -> tuple[GuidanceItem, ...]:
    """
    Extract all currently supported Equinor guidance
    from one report.

    The page iterable is materialised once because the
    individual extractors each need to inspect it.
    """

    materialized_pages = tuple(
        pages
    )

    formal_outlook = (
        extract_equinor_formal_outlook_guidance(
            document_id=document_id,
            pages=materialized_pages,
        )
    )

    share_buyback = (
        extract_equinor_share_buyback_guidance(
            document_id=document_id,
            pages=materialized_pages,
        )
    )

    return (
        *formal_outlook,
        share_buyback,
    )


def build_equinor_guidance_report(
    previous_document_id: str,
    previous_pages: Iterable[
        ParsedPage
    ],
    current_document_id: str,
    current_pages: Iterable[
        ParsedPage
    ],
) -> GuidanceReport:
    previous_guidance = (
        extract_equinor_guidance(
            document_id=(
                previous_document_id
            ),
            pages=previous_pages,
        )
    )

    current_guidance = (
        extract_equinor_guidance(
            document_id=(
                current_document_id
            ),
            pages=current_pages,
        )
    )

    return build_guidance_report(
        previous_document_id=(
            previous_document_id
        ),
        current_document_id=(
            current_document_id
        ),
        previous_items=previous_guidance,
        current_items=current_guidance,
    )
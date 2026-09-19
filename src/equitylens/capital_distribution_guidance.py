import re
from collections.abc import Iterable
from decimal import Decimal

from equitylens.guidance import GuidanceItem
from equitylens.parser import ParsedPage

_Q1_STYLE_PATTERN = re.compile(
    r"The expected share buy-back programme for "
    r"(?P<year>20\d{2}) is up to USD "
    r"(?P<value>\d+(?:\.\d+)?) billion",
    re.IGNORECASE,
)

_Q2_STYLE_PATTERN = re.compile(
    r"This brings the total expected programme for "
    r"(?P<year>20\d{2}) to up to USD "
    r"(?P<value>\d+(?:\.\d+)?) billion",
    re.IGNORECASE,
)


def _normalize_whitespace(
    text: str,
) -> str:
    return " ".join(
        text.split()
    )


def _extract_match(
    text: str,
) -> re.Match[str] | None:
    for pattern in (
        _Q1_STYLE_PATTERN,
        _Q2_STYLE_PATTERN,
    ):
        match = pattern.search(
            text
        )

        if match is not None:
            return match

    return None


def extract_equinor_share_buyback_guidance(
    document_id: str,
    pages: Iterable[ParsedPage],
) -> GuidanceItem:
    """
    Extract Equinor's expected full-year share buy-back programme.

    The extractor intentionally targets the annual programme and ignores
    individual share buy-back tranches.
    """

    if not document_id.strip():
        raise ValueError(
            "document_id cannot be empty."
        )

    matches: list[
        tuple[
            int,
            str,
            Decimal,
            str,
        ]
    ] = []

    for page in pages:
        if (
            page.document_id
            != document_id
        ):
            raise ValueError(
                "Parsed page document_id does not "
                "match the requested document."
            )

        normalized_text = (
            _normalize_whitespace(
                page.text
            )
        )

        match = _extract_match(
            normalized_text
        )

        if match is None:
            continue

        statement = match.group(0)

        matches.append(
            (
                page.page_number,
                statement,
                Decimal(
                    match.group("value")
                ),
                match.group("year"),
            )
        )

    if not matches:
        raise ValueError(
            "Expected full-year share buy-back "
            "guidance was not found."
        )

    unique_values = {
        (
            value,
            year,
        )
        for _, _, value, year
        in matches
    }

    if len(unique_values) != 1:
        raise ValueError(
            "Conflicting full-year share buy-back "
            "guidance detected."
        )

    page_number, statement, value, year = min(
        matches,
        key=lambda item: item[0],
    )

    return GuidanceItem(
        metric_id="share_buyback",
        target_period=f"FY {year}",
        category="capital_distribution",
        document_id=document_id,
        page_number=page_number,
        section="Capital distribution",
        statement=statement,
        numeric_value=value,
        unit="USD billion",
        qualifier="up to",
    )
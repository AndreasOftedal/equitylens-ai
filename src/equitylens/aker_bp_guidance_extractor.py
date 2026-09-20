import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from equitylens.guidance import GuidanceItem
from equitylens.parser import ParsedPage


@dataclass(frozen=True)
class _ScalarGuidanceRule:
    metric_id: str
    pattern: re.Pattern[str]
    unit: str
    qualifier: str | None = None


@dataclass(frozen=True)
class _RangeGuidanceRule:
    metric_id: str
    pattern: re.Pattern[str]
    unit: str
    qualifier: str | None = None


_EXPECTED_METRIC_IDS = (
    "production_guidance",
    "production_cost_guidance",
    "capex_guidance",
    "exploration_spend_guidance",
    "abandonment_spend_guidance",
    "dividend_guidance",
)


_GUIDANCE_YEAR_PATTERN = re.compile(
    r"\bGuidance for (?P<year>20\d{2})\b",
    re.IGNORECASE,
)


_RANGE_RULES = (
    _RangeGuidanceRule(
        metric_id="production_guidance",
        pattern=re.compile(
            r"\bProduction:\s*"
            r"(?P<lower>\d+(?:\.\d+)?)"
            r"\s*[-–]\s*"
            r"(?P<upper>\d+(?:\.\d+)?)"
            r"\s*mboepd\b",
            re.IGNORECASE,
        ),
        unit="mboepd",
        qualifier="guidance range",
    ),
    _RangeGuidanceRule(
        metric_id="capex_guidance",
        pattern=re.compile(
            r"\bCapex:\s*USD\s*"
            r"(?P<lower>\d+(?:\.\d+)?)"
            r"\s*[-–]\s*"
            r"(?P<upper>\d+(?:\.\d+)?)"
            r"\s*billion\b",
            re.IGNORECASE,
        ),
        unit="USD billion",
        qualifier="guidance range",
    ),
)


_SCALAR_RULES = (
    _ScalarGuidanceRule(
        metric_id="production_cost_guidance",
        pattern=re.compile(
            r"\bProduction cost:\s*USD\s*~"
            r"(?P<value>\d+(?:\.\d+)?)"
            r"\s*per boe\b",
            re.IGNORECASE,
        ),
        unit="USD per boe",
        qualifier="approximately",
    ),
    _ScalarGuidanceRule(
        metric_id="exploration_spend_guidance",
        pattern=re.compile(
            r"\bExploration spend:\s*USD\s*~"
            r"(?P<value>\d+(?:\.\d+)?)"
            r"\s*million\b",
            re.IGNORECASE,
        ),
        unit="USD million",
        qualifier="approximately",
    ),
    _ScalarGuidanceRule(
        metric_id="abandonment_spend_guidance",
        pattern=re.compile(
            r"\bAbandonment spend:\s*USD\s*~"
            r"(?P<value>\d+(?:\.\d+)?)"
            r"\s*million\b",
            re.IGNORECASE,
        ),
        unit="USD million",
        qualifier="approximately",
    ),
    _ScalarGuidanceRule(
        metric_id="dividend_guidance",
        pattern=re.compile(
            r"\bDividend:\s*USD\s*"
            r"(?P<value>\d+(?:\.\d+)?)"
            r"\s*per share per quarter\b",
            re.IGNORECASE,
        ),
        unit="USD per share per quarter",
    ),
)


def _normalize_whitespace(
    text: str,
) -> str:
    return " ".join(
        text.split()
    )


def _extract_guidance_year(
    normalized_text: str,
) -> str | None:
    match = _GUIDANCE_YEAR_PATTERN.search(
        normalized_text
    )

    if match is None:
        return None

    return match.group(
        "year"
    )


def _build_range_item(
    *,
    document_id: str,
    page: ParsedPage,
    normalized_text: str,
    target_year: str,
    rule: _RangeGuidanceRule,
) -> GuidanceItem | None:
    match = rule.pattern.search(
        normalized_text
    )

    if match is None:
        return None

    return GuidanceItem(
        metric_id=rule.metric_id,
        target_period=f"FY {target_year}",
        category="formal_outlook",
        document_id=document_id,
        page_number=page.page_number,
        section="Outlook",
        statement=match.group(0),
        numeric_lower_bound=Decimal(
            match.group("lower")
        ),
        numeric_upper_bound=Decimal(
            match.group("upper")
        ),
        unit=rule.unit,
        qualifier=rule.qualifier,
    )


def _build_scalar_item(
    *,
    document_id: str,
    page: ParsedPage,
    normalized_text: str,
    target_year: str,
    rule: _ScalarGuidanceRule,
) -> GuidanceItem | None:
    match = rule.pattern.search(
        normalized_text
    )

    if match is None:
        return None

    return GuidanceItem(
        metric_id=rule.metric_id,
        target_period=f"FY {target_year}",
        category="formal_outlook",
        document_id=document_id,
        page_number=page.page_number,
        section="Outlook",
        statement=match.group(0),
        numeric_value=Decimal(
            match.group("value")
        ),
        unit=rule.unit,
        qualifier=rule.qualifier,
    )


def extract_aker_bp_formal_outlook_guidance(
    document_id: str,
    pages: Iterable[ParsedPage],
    require_complete: bool = True,
) -> tuple[GuidanceItem, ...]:
    """
    Extract Aker BP formal annual guidance using deterministic rules.

    Only pages containing the formal Outlook section and an explicit
    "Guidance for YYYY" heading are eligible.

    The extractor reads the current value immediately following each
    guidance label. Parenthesised values describing previous guidance
    are therefore not interpreted as current guidance.
    """

    if not document_id.strip():
        raise ValueError(
            "document_id cannot be empty."
        )

    extracted: dict[
        str,
        GuidanceItem,
    ] = {}

    for page in pages:
        if page.document_id != document_id:
            raise ValueError(
                "Parsed page document_id does not "
                "match the requested document."
            )

        normalized_text = (
            _normalize_whitespace(
                page.text
            )
        )

        if not re.search(
            r"\bOutlook\b",
            normalized_text,
            re.IGNORECASE,
        ):
            continue

        target_year = (
            _extract_guidance_year(
                normalized_text
            )
        )

        if target_year is None:
            continue

        candidates: list[
            GuidanceItem
        ] = []

        for rule in _RANGE_RULES:
            item = _build_range_item(
                document_id=document_id,
                page=page,
                normalized_text=(
                    normalized_text
                ),
                target_year=target_year,
                rule=rule,
            )

            if item is not None:
                candidates.append(
                    item
                )

        for rule in _SCALAR_RULES:
            item = _build_scalar_item(
                document_id=document_id,
                page=page,
                normalized_text=(
                    normalized_text
                ),
                target_year=target_year,
                rule=rule,
            )

            if item is not None:
                candidates.append(
                    item
                )

        for item in candidates:
            if item.metric_id in extracted:
                raise ValueError(
                    "Duplicate Aker BP formal "
                    "Outlook guidance detected for "
                    f"{item.metric_id}."
                )

            extracted[
                item.metric_id
            ] = item

    if require_complete:
        missing_metric_ids = (
            set(_EXPECTED_METRIC_IDS)
            - set(extracted)
        )

        if missing_metric_ids:
            missing = ", ".join(
                sorted(
                    missing_metric_ids
                )
            )

            raise ValueError(
                "Missing expected Aker BP formal "
                f"Outlook guidance: {missing}"
            )

    return tuple(
        extracted[metric_id]
        for metric_id
        in _EXPECTED_METRIC_IDS
        if metric_id in extracted
    )
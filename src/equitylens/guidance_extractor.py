import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from equitylens.guidance import GuidanceItem
from equitylens.parser import ParsedPage


@dataclass(frozen=True)
class _NumericGuidanceRule:
    metric_id: str
    pattern: re.Pattern[str]
    unit: str
    qualifier: str


_EXPECTED_METRIC_IDS = (
    "organic_capex",
    "oil_gas_production_growth",
    "unit_production_cost_position",
    "maintenance_production_impact",
)


_NUMERIC_RULES = (
    _NumericGuidanceRule(
        metric_id="organic_capex",
        pattern=re.compile(
            r"Organic capital expenditures\*? "
            r"are estimated at around USD "
            r"(?P<value>\d+(?:\.\d+)?) billion "
            r"for (?P<year>20\d{2})",
            re.IGNORECASE,
        ),
        unit="USD billion",
        qualifier="around",
    ),
    _NumericGuidanceRule(
        metric_id="oil_gas_production_growth",
        pattern=re.compile(
            r"Oil\s*&\s*gas production for "
            r"(?P<year>20\d{2}) is estimated to grow "
            r"around (?P<value>\d+(?:\.\d+)?)% "
            r"compared to (?P<base_year>20\d{2}) level",
            re.IGNORECASE,
        ),
        unit="percent",
        qualifier="around",
    ),
    _NumericGuidanceRule(
        metric_id="maintenance_production_impact",
        pattern=re.compile(
            r"Scheduled maintenance activity is estimated "
            r"to reduce equity production by around "
            r"(?P<value>\d+(?:\.\d+)?) mboe per day "
            r"for the full year of (?P<year>20\d{2})",
            re.IGNORECASE,
        ),
        unit="mboe per day",
        qualifier="around",
    ),
)


_COST_POSITION_PATTERN = re.compile(
    r"Equinor(?:’|')s ambition is to keep the "
    r"unit of production cost in the top quartile "
    r"of its peer group",
    re.IGNORECASE,
)


def _normalize_whitespace(
    text: str,
) -> str:
    return " ".join(
        text.split()
    )


def _build_numeric_item(
    document_id: str,
    page: ParsedPage,
    normalized_text: str,
    rule: _NumericGuidanceRule,
) -> GuidanceItem | None:
    match = rule.pattern.search(
        normalized_text
    )

    if match is None:
        return None

    year = match.group(
        "year"
    )

    return GuidanceItem(
        metric_id=rule.metric_id,
        target_period=f"FY {year}",
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


def _build_cost_position_item(
    document_id: str,
    page: ParsedPage,
    normalized_text: str,
) -> GuidanceItem | None:
    match = _COST_POSITION_PATTERN.search(
        normalized_text
    )

    if match is None:
        return None

    return GuidanceItem(
        metric_id="unit_production_cost_position",
        target_period="ongoing",
        category="formal_outlook",
        document_id=document_id,
        page_number=page.page_number,
        section="Outlook",
        statement=match.group(0),
        qualitative_value=(
            "top quartile of peer group"
        ),
        qualifier="ambition",
    )


def extract_equinor_formal_outlook_guidance(
    document_id: str,
    pages: Iterable[ParsedPage],
) -> tuple[GuidanceItem, ...]:
    """
    Extract Equinor's formal Outlook guidance using deterministic rules.

    The extractor intentionally targets the formal Outlook language rather
    than generic forward-looking words such as "expected" or "growth".
    This prevents historical performance statements from being mistaken
    for management guidance.
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

        if not re.search(
            r"\bOutlook\b",
            normalized_text,
            re.IGNORECASE,
        ):
            continue

        candidates: list[
            GuidanceItem
        ] = []

        for rule in _NUMERIC_RULES:
            item = _build_numeric_item(
                document_id=document_id,
                page=page,
                normalized_text=normalized_text,
                rule=rule,
            )

            if item is not None:
                candidates.append(
                    item
                )

        cost_item = (
            _build_cost_position_item(
                document_id=document_id,
                page=page,
                normalized_text=normalized_text,
            )
        )

        if cost_item is not None:
            candidates.append(
                cost_item
            )

        for item in candidates:
            if (
                item.metric_id
                in extracted
            ):
                raise ValueError(
                    "Duplicate formal Outlook "
                    "guidance detected for "
                    f"{item.metric_id}."
                )

            extracted[
                item.metric_id
            ] = item

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
            "Missing expected formal Outlook "
            f"guidance: {missing}"
        )

    return tuple(
        extracted[metric_id]
        for metric_id
        in _EXPECTED_METRIC_IDS
    )
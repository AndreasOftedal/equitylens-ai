from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

GuidanceCategory = Literal[
    "formal_outlook",
    "capital_distribution",
    "other_forward_looking",
]

GuidanceChangeType = Literal[
    "unchanged",
    "increased",
    "decreased",
    "changed",
]


@dataclass(frozen=True)
class GuidanceItem:
    metric_id: str
    target_period: str
    category: GuidanceCategory
    document_id: str
    page_number: int
    section: str
    statement: str
    numeric_value: Decimal | None = None
    unit: str | None = None
    qualifier: str | None = None
    qualitative_value: str | None = None

    def __post_init__(self) -> None:
        if not self.metric_id.strip():
            raise ValueError(
                "metric_id cannot be empty."
            )

        if not self.target_period.strip():
            raise ValueError(
                "target_period cannot be empty."
            )

        if not self.document_id.strip():
            raise ValueError(
                "document_id cannot be empty."
            )

        if self.page_number < 1:
            raise ValueError(
                "page_number must be at least 1."
            )

        if not self.section.strip():
            raise ValueError(
                "section cannot be empty."
            )

        if not self.statement.strip():
            raise ValueError(
                "statement cannot be empty."
            )

        has_numeric_value = (
            self.numeric_value is not None
        )

        has_qualitative_value = bool(
            self.qualitative_value
            and self.qualitative_value.strip()
        )

        if (
            has_numeric_value
            == has_qualitative_value
        ):
            raise ValueError(
                "GuidanceItem must contain exactly "
                "one numeric or qualitative value."
            )

        if (
            has_numeric_value
            and not self.unit
        ):
            raise ValueError(
                "Numeric guidance requires a unit."
            )

        if (
            has_qualitative_value
            and self.unit is not None
        ):
            raise ValueError(
                "Qualitative guidance cannot "
                "contain a numeric unit."
            )


@dataclass(frozen=True)
class GuidanceChange:
    metric_id: str
    target_period: str
    change_type: GuidanceChangeType
    previous: GuidanceItem
    current: GuidanceItem
    qualifier_changed: bool
    category_changed: bool


def _normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return " ".join(
        value.lower().split()
    )


def compare_guidance(
    previous: GuidanceItem,
    current: GuidanceItem,
) -> GuidanceChange:
    if previous.metric_id != current.metric_id:
        raise ValueError(
            "Guidance metric_ids must match."
        )

    if (
        previous.target_period
        != current.target_period
    ):
        raise ValueError(
            "Guidance target periods must match."
        )

    qualifier_changed = (
        _normalize_optional_text(
            previous.qualifier
        )
        != _normalize_optional_text(
            current.qualifier
        )
    )

    category_changed = (
        previous.category
        != current.category
    )

    previous_is_numeric = (
        previous.numeric_value is not None
    )

    current_is_numeric = (
        current.numeric_value is not None
    )

    if (
        previous_is_numeric
        and current_is_numeric
    ):
        if (
            _normalize_optional_text(
                previous.unit
            )
            != _normalize_optional_text(
                current.unit
            )
        ):
            raise ValueError(
                "Numeric guidance units must match."
            )

        if (
            current.numeric_value
            > previous.numeric_value
        ):
            change_type: GuidanceChangeType = (
                "increased"
            )

        elif (
            current.numeric_value
            < previous.numeric_value
        ):
            change_type = "decreased"

        elif (
            qualifier_changed
            or category_changed
        ):
            change_type = "changed"

        else:
            change_type = "unchanged"

    elif (
        not previous_is_numeric
        and not current_is_numeric
    ):
        previous_value = (
            _normalize_optional_text(
                previous.qualitative_value
            )
        )

        current_value = (
            _normalize_optional_text(
                current.qualitative_value
            )
        )

        if (
            previous_value == current_value
            and not qualifier_changed
            and not category_changed
        ):
            change_type = "unchanged"

        else:
            change_type = "changed"

    else:
        change_type = "changed"

    return GuidanceChange(
        metric_id=previous.metric_id,
        target_period=previous.target_period,
        change_type=change_type,
        previous=previous,
        current=current,
        qualifier_changed=(
            qualifier_changed
        ),
        category_changed=(
            category_changed
        ),
    )
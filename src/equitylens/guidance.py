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

GuidanceValueType = Literal[
    "scalar",
    "range",
    "qualitative",
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
    numeric_lower_bound: Decimal | None = None
    numeric_upper_bound: Decimal | None = None
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

        has_scalar_value = (
            self.numeric_value is not None
        )

        has_lower_bound = (
            self.numeric_lower_bound is not None
        )

        has_upper_bound = (
            self.numeric_upper_bound is not None
        )

        if has_lower_bound != has_upper_bound:
            raise ValueError(
                "Numeric range guidance requires "
                "both lower and upper bounds."
            )

        has_range_value = (
            has_lower_bound
            and has_upper_bound
        )

        has_qualitative_value = bool(
            self.qualitative_value
            and self.qualitative_value.strip()
        )

        value_type_count = sum(
            (
                has_scalar_value,
                has_range_value,
                has_qualitative_value,
            )
        )

        if value_type_count != 1:
            raise ValueError(
                "GuidanceItem must contain exactly one "
                "numeric or qualitative value type: "
                "scalar numeric, numeric range, or "
                "qualitative value."
            )

        if (
            has_range_value
            and self.numeric_lower_bound
            > self.numeric_upper_bound
        ):
            raise ValueError(
                "Numeric guidance lower bound "
                "cannot exceed upper bound."
            )

        has_numeric_guidance = (
            has_scalar_value
            or has_range_value
        )

        if (
            has_numeric_guidance
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


def _guidance_value_type(
    item: GuidanceItem,
) -> GuidanceValueType:
    if item.numeric_value is not None:
        return "scalar"

    if (
        item.numeric_lower_bound is not None
        and item.numeric_upper_bound is not None
    ):
        return "range"

    return "qualitative"


def _validate_numeric_units(
    previous: GuidanceItem,
    current: GuidanceItem,
) -> None:
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


def _compare_scalar_guidance(
    previous: GuidanceItem,
    current: GuidanceItem,
    qualifier_changed: bool,
    category_changed: bool,
) -> GuidanceChangeType:
    _validate_numeric_units(
        previous,
        current,
    )

    assert (
        previous.numeric_value is not None
    )

    assert (
        current.numeric_value is not None
    )

    if (
        current.numeric_value
        > previous.numeric_value
    ):
        return "increased"

    if (
        current.numeric_value
        < previous.numeric_value
    ):
        return "decreased"

    if (
        qualifier_changed
        or category_changed
    ):
        return "changed"

    return "unchanged"


def _compare_range_guidance(
    previous: GuidanceItem,
    current: GuidanceItem,
    qualifier_changed: bool,
    category_changed: bool,
) -> GuidanceChangeType:
    _validate_numeric_units(
        previous,
        current,
    )

    assert (
        previous.numeric_lower_bound
        is not None
    )

    assert (
        previous.numeric_upper_bound
        is not None
    )

    assert (
        current.numeric_lower_bound
        is not None
    )

    assert (
        current.numeric_upper_bound
        is not None
    )

    previous_lower = (
        previous.numeric_lower_bound
    )

    previous_upper = (
        previous.numeric_upper_bound
    )

    current_lower = (
        current.numeric_lower_bound
    )

    current_upper = (
        current.numeric_upper_bound
    )

    bounds_unchanged = (
        current_lower == previous_lower
        and current_upper == previous_upper
    )

    if bounds_unchanged:
        if (
            qualifier_changed
            or category_changed
        ):
            return "changed"

        return "unchanged"

    moved_up = (
        current_lower >= previous_lower
        and current_upper >= previous_upper
        and (
            current_lower > previous_lower
            or current_upper > previous_upper
        )
    )

    if moved_up:
        return "increased"

    moved_down = (
        current_lower <= previous_lower
        and current_upper <= previous_upper
        and (
            current_lower < previous_lower
            or current_upper < previous_upper
        )
    )

    if moved_down:
        return "decreased"

    return "changed"


def _compare_qualitative_guidance(
    previous: GuidanceItem,
    current: GuidanceItem,
    qualifier_changed: bool,
    category_changed: bool,
) -> GuidanceChangeType:
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
        return "unchanged"

    return "changed"


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

    previous_value_type = (
        _guidance_value_type(
            previous
        )
    )

    current_value_type = (
        _guidance_value_type(
            current
        )
    )

    if (
        previous_value_type
        != current_value_type
    ):
        change_type: GuidanceChangeType = (
            "changed"
        )

    elif previous_value_type == "scalar":
        change_type = (
            _compare_scalar_guidance(
                previous=previous,
                current=current,
                qualifier_changed=(
                    qualifier_changed
                ),
                category_changed=(
                    category_changed
                ),
            )
        )

    elif previous_value_type == "range":
        change_type = (
            _compare_range_guidance(
                previous=previous,
                current=current,
                qualifier_changed=(
                    qualifier_changed
                ),
                category_changed=(
                    category_changed
                ),
            )
        )

    else:
        change_type = (
            _compare_qualitative_guidance(
                previous=previous,
                current=current,
                qualifier_changed=(
                    qualifier_changed
                ),
                category_changed=(
                    category_changed
                ),
            )
        )

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
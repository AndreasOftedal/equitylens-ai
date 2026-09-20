from decimal import Decimal

import pytest

from equitylens.guidance import (
    GuidanceItem,
    compare_guidance,
)


def _range_guidance(
    *,
    document_id: str,
    lower: str,
    upper: str,
    unit: str = "mboe per day",
    qualifier: str = "guidance range",
) -> GuidanceItem:
    return GuidanceItem(
        metric_id="production_guidance",
        target_period="FY 2026",
        category="formal_outlook",
        document_id=document_id,
        page_number=16,
        section="Outlook",
        statement=(
            f"Production guidance is "
            f"{lower}-{upper} {unit}."
        ),
        numeric_lower_bound=Decimal(lower),
        numeric_upper_bound=Decimal(upper),
        unit=unit,
        qualifier=qualifier,
    )


def test_numeric_range_guidance_is_valid():
    item = _range_guidance(
        document_id="q1",
        lower="370",
        upper="400",
    )

    assert item.numeric_value is None

    assert (
        item.numeric_lower_bound
        == Decimal(370)
    )

    assert (
        item.numeric_upper_bound
        == Decimal(400)
    )

    assert item.qualitative_value is None


def test_numeric_range_requires_both_bounds():
    with pytest.raises(
        ValueError,
        match="both lower and upper bounds",
    ):
        GuidanceItem(
            metric_id="production_guidance",
            target_period="FY 2026",
            category="formal_outlook",
            document_id="q1",
            page_number=16,
            section="Outlook",
            statement="Production guidance.",
            numeric_lower_bound=Decimal(370),
            unit="mboe per day",
        )


def test_numeric_range_requires_ordered_bounds():
    with pytest.raises(
        ValueError,
        match="lower bound cannot exceed upper bound",
    ):
        _range_guidance(
            document_id="q1",
            lower="410",
            upper="400",
        )


def test_numeric_range_cannot_mix_with_scalar_value():
    with pytest.raises(
        ValueError,
        match="exactly one",
    ):
        GuidanceItem(
            metric_id="production_guidance",
            target_period="FY 2026",
            category="formal_outlook",
            document_id="q1",
            page_number=16,
            section="Outlook",
            statement="Production guidance.",
            numeric_value=Decimal(385),
            numeric_lower_bound=Decimal(370),
            numeric_upper_bound=Decimal(400),
            unit="mboe per day",
        )


def test_unchanged_range_is_detected():
    previous = _range_guidance(
        document_id="q1",
        lower="370",
        upper="400",
    )

    current = _range_guidance(
        document_id="q2",
        lower="370",
        upper="400",
    )

    assert (
        compare_guidance(
            previous,
            current,
        ).change_type
        == "unchanged"
    )


def test_range_shift_up_is_detected_as_increase():
    previous = _range_guidance(
        document_id="q1",
        lower="370",
        upper="400",
    )

    current = _range_guidance(
        document_id="q2",
        lower="380",
        upper="400",
    )

    assert (
        compare_guidance(
            previous,
            current,
        ).change_type
        == "increased"
    )


def test_range_shift_down_is_detected_as_decrease():
    previous = _range_guidance(
        document_id="q1",
        lower="380",
        upper="410",
    )

    current = _range_guidance(
        document_id="q2",
        lower="370",
        upper="400",
    )

    assert (
        compare_guidance(
            previous,
            current,
        ).change_type
        == "decreased"
    )


def test_mixed_range_change_is_detected_as_changed():
    previous = _range_guidance(
        document_id="q1",
        lower="370",
        upper="400",
    )

    current = _range_guidance(
        document_id="q2",
        lower="360",
        upper="410",
    )

    assert (
        compare_guidance(
            previous,
            current,
        ).change_type
        == "changed"
    )


def test_range_units_must_match():
    previous = _range_guidance(
        document_id="q1",
        lower="370",
        upper="400",
        unit="mboe per day",
    )

    current = _range_guidance(
        document_id="q2",
        lower="380",
        upper="400",
        unit="boe per day",
    )

    with pytest.raises(
        ValueError,
        match="units must match",
    ):
        compare_guidance(
            previous,
            current,
        )
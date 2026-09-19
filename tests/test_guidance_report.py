from decimal import Decimal

import pytest

from equitylens.guidance import (
    GuidanceItem,
)
from equitylens.guidance_report import (
    build_guidance_report,
)

PREVIOUS_DOCUMENT = "q1"
CURRENT_DOCUMENT = "q2"


def _numeric_item(
    document_id: str,
    metric_id: str,
    value: str,
    target_period: str = "FY 2026",
) -> GuidanceItem:
    return GuidanceItem(
        metric_id=metric_id,
        target_period=target_period,
        category="formal_outlook",
        document_id=document_id,
        page_number=10,
        section="Outlook",
        statement="Guidance statement.",
        numeric_value=Decimal(value),
        unit="USD billion",
        qualifier="around",
    )


def _buyback_item(
    document_id: str,
    value: str,
) -> GuidanceItem:
    return GuidanceItem(
        metric_id="share_buyback",
        target_period="FY 2026",
        category="capital_distribution",
        document_id=document_id,
        page_number=6,
        section="Capital distribution",
        statement="Buyback guidance.",
        numeric_value=Decimal(value),
        unit="USD billion",
        qualifier="up to",
    )


def test_builds_report_for_shared_guidance():
    report = build_guidance_report(
        previous_document_id=(
            PREVIOUS_DOCUMENT
        ),
        current_document_id=(
            CURRENT_DOCUMENT
        ),
        previous_items=(
            _numeric_item(
                PREVIOUS_DOCUMENT,
                "organic_capex",
                "13",
            ),
            _buyback_item(
                PREVIOUS_DOCUMENT,
                "1.5",
            ),
        ),
        current_items=(
            _numeric_item(
                CURRENT_DOCUMENT,
                "organic_capex",
                "13",
            ),
            _buyback_item(
                CURRENT_DOCUMENT,
                "3",
            ),
        ),
    )

    assert len(report.changes) == 2
    assert len(report.unchanged) == 1
    assert len(report.changed) == 1

    assert (
        report.changed[0].metric_id
        == "share_buyback"
    )

    assert (
        report.changed[0].change_type
        == "increased"
    )


def test_introduced_guidance_is_preserved():
    report = build_guidance_report(
        previous_document_id=(
            PREVIOUS_DOCUMENT
        ),
        current_document_id=(
            CURRENT_DOCUMENT
        ),
        previous_items=(),
        current_items=(
            _numeric_item(
                CURRENT_DOCUMENT,
                "new_metric",
                "5",
            ),
        ),
    )

    assert report.changes == ()
    assert len(report.introduced) == 1
    assert report.withdrawn == ()

    assert (
        report.introduced[0].metric_id
        == "new_metric"
    )


def test_withdrawn_guidance_is_preserved():
    report = build_guidance_report(
        previous_document_id=(
            PREVIOUS_DOCUMENT
        ),
        current_document_id=(
            CURRENT_DOCUMENT
        ),
        previous_items=(
            _numeric_item(
                PREVIOUS_DOCUMENT,
                "old_metric",
                "5",
            ),
        ),
        current_items=(),
    )

    assert report.changes == ()
    assert report.introduced == ()
    assert len(report.withdrawn) == 1

    assert (
        report.withdrawn[0].metric_id
        == "old_metric"
    )


def test_changed_target_period_is_not_compared_directly():
    report = build_guidance_report(
        previous_document_id=(
            PREVIOUS_DOCUMENT
        ),
        current_document_id=(
            CURRENT_DOCUMENT
        ),
        previous_items=(
            _numeric_item(
                PREVIOUS_DOCUMENT,
                "organic_capex",
                "13",
                target_period="FY 2026",
            ),
        ),
        current_items=(
            _numeric_item(
                CURRENT_DOCUMENT,
                "organic_capex",
                "14",
                target_period="FY 2027",
            ),
        ),
    )

    assert report.changes == ()
    assert len(report.introduced) == 1
    assert len(report.withdrawn) == 1


def test_duplicate_guidance_is_rejected():
    item = _numeric_item(
        PREVIOUS_DOCUMENT,
        "organic_capex",
        "13",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate guidance item",
    ):
        build_guidance_report(
            previous_document_id=(
                PREVIOUS_DOCUMENT
            ),
            current_document_id=(
                CURRENT_DOCUMENT
            ),
            previous_items=(
                item,
                item,
            ),
            current_items=(),
        )


def test_previous_document_mismatch_is_rejected():
    item = _numeric_item(
        "wrong-document",
        "organic_capex",
        "13",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Guidance item document_id does not "
            "match"
        ),
    ):
        build_guidance_report(
            previous_document_id=(
                PREVIOUS_DOCUMENT
            ),
            current_document_id=(
                CURRENT_DOCUMENT
            ),
            previous_items=(
                item,
            ),
            current_items=(),
        )


def test_current_document_mismatch_is_rejected():
    item = _numeric_item(
        "wrong-document",
        "organic_capex",
        "13",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Guidance item document_id does not "
            "match"
        ),
    ):
        build_guidance_report(
            previous_document_id=(
                PREVIOUS_DOCUMENT
            ),
            current_document_id=(
                CURRENT_DOCUMENT
            ),
            previous_items=(),
            current_items=(
                item,
            ),
        )


def test_same_document_comparison_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "requires two different documents"
        ),
    ):
        build_guidance_report(
            previous_document_id="q1",
            current_document_id="q1",
            previous_items=(),
            current_items=(),
        )
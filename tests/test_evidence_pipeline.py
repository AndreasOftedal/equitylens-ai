from types import SimpleNamespace

import pytest

from equitylens.evidence_pipeline import (
    build_evidence_assessments,
)
from equitylens.parser import ParsedPage


class FakeDataset:
    def __init__(
        self,
        comparison_type: str = "qoq",
    ) -> None:
        self.comparison_type = (
            comparison_type
        )
        self.calls: list[
            tuple[str, str, str]
        ] = []

    def compare(
        self,
        metric_id: str,
        from_period: str,
        to_period: str,
    ):
        self.calls.append(
            (
                metric_id,
                from_period,
                to_period,
            )
        )

        return SimpleNamespace(
            comparison_type=(
                self.comparison_type
            )
        )


DOCUMENT_ID = "q2-document"


def _pages():
    return (
        ParsedPage(
            document_id=DOCUMENT_ID,
            page_number=1,
            text=(
                "Group review. "
                "Net operating income decreased "
                "compared to the prior quarter "
                "due to lower realised prices."
            ),
        ),
        ParsedPage(
            document_id=DOCUMENT_ID,
            page_number=2,
            text=(
                "Cash flow information. "
                "Cash flow decreased compared "
                "to the prior quarter due to "
                "higher tax payments."
            ),
        ),
    )


def test_builds_assessment_for_enabled_metric():
    dataset = FakeDataset()

    assessments = (
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=_pages(),
            dataset=dataset,
            metric_ids=(
                "net_operating_income",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )
    )

    assert set(
        assessments
    ) == {
        "net_operating_income"
    }

    assessment = assessments[
        "net_operating_income"
    ]

    assert (
        assessment.query
        == "What drove net operating income?"
    )

    assert (
        assessment.expected_comparison_type
        == "qoq"
    )


def test_uses_financial_change_comparison_type():
    dataset = FakeDataset(
        comparison_type="yoy"
    )

    assessments = (
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=_pages(),
            dataset=dataset,
            metric_ids=(
                "net_operating_income",
            ),
            from_period="Q2 2025",
            to_period="Q2 2026",
        )
    )

    assert (
        assessments[
            "net_operating_income"
        ].expected_comparison_type
        == "yoy"
    )


def test_unvalidated_metric_is_skipped():
    dataset = FakeDataset()

    assessments = (
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=_pages(),
            dataset=dataset,
            metric_ids=(
                "net_income",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )
    )

    assert assessments == {}

    assert dataset.calls == []


def test_mixed_metrics_only_assess_supported_queries():
    dataset = FakeDataset()

    assessments = (
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=_pages(),
            dataset=dataset,
            metric_ids=(
                "net_operating_income",
                "net_income",
                "operating_cash_flow",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )
    )

    assert set(
        assessments
    ) == {
        "net_operating_income",
        "operating_cash_flow",
    }

    assert {
        call[0]
        for call in dataset.calls
    } == {
        "net_operating_income",
        "operating_cash_flow",
    }


def test_single_use_page_iterable_is_supported():
    dataset = FakeDataset()

    pages = (
        page
        for page in _pages()
    )

    assessments = (
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=pages,
            dataset=dataset,
            metric_ids=(
                "net_operating_income",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )
    )

    assert (
        "net_operating_income"
        in assessments
    )


def test_mismatched_page_document_is_rejected():
    dataset = FakeDataset()

    wrong_page = ParsedPage(
        document_id="wrong-document",
        page_number=1,
        text="Some narrative.",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Parsed page document_id does not match"
        ),
    ):
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=(wrong_page,),
            dataset=dataset,
            metric_ids=(
                "net_operating_income",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )


def test_duplicate_metrics_are_rejected():
    dataset = FakeDataset()

    with pytest.raises(
        ValueError,
        match="metric_ids must be unique",
    ):
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=_pages(),
            dataset=dataset,
            metric_ids=(
                "net_operating_income",
                "net_operating_income",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )


def test_empty_metrics_are_rejected():
    dataset = FakeDataset()

    with pytest.raises(
        ValueError,
        match="metric_ids cannot be empty",
    ):
        build_evidence_assessments(
            document_id=DOCUMENT_ID,
            pages=_pages(),
            dataset=dataset,
            metric_ids=(),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )
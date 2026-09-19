from types import SimpleNamespace

from equitylens.consistency import (
    assess_consistency,
)


def _evidence(
    *,
    availability="direct_explanation",
    comparison_type="qoq",
    sentences=(),
):
    direct_explanations = tuple(
        SimpleNamespace(
            sentence=SimpleNamespace(
                text=text
            )
        )
        for text in sentences
    )

    return SimpleNamespace(
        availability=availability,
        expected_comparison_type=(
            comparison_type
        ),
        direct_explanations=(
            direct_explanations
        ),
    )


def test_matching_increase_is_consistent():
    assessment = assess_consistency(
        metric_id="net_operating_income",
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            sentences=(
                (
                    "Net operating income increased "
                    "compared to the prior quarter "
                    "due to higher prices."
                ),
            ),
        ),
    )

    assert (
        assessment.status
        == "consistent"
    )

    assert (
        assessment.financial_direction
        == "increase"
    )


def test_matching_decrease_is_consistent():
    assessment = assess_consistency(
        metric_id="operating_cash_flow",
        absolute_change=-100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            sentences=(
                (
                    "Cash flow decreased compared "
                    "to the prior quarter due to "
                    "higher tax payments."
                ),
            ),
        ),
    )

    assert (
        assessment.status
        == "consistent"
    )


def test_matching_unchanged_is_consistent():
    assessment = assess_consistency(
        metric_id=(
            "adjusted_operating_income"
        ),
        absolute_change=0,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            sentences=(
                (
                    "Adjusted operating income "
                    "remained at a similar level "
                    "compared to the prior quarter."
                ),
            ),
        ),
    )

    assert (
        assessment.status
        == "consistent"
    )


def test_opposing_direction_is_potential_tension():
    assessment = assess_consistency(
        metric_id="net_operating_income",
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            sentences=(
                (
                    "Net operating income decreased "
                    "compared to the prior quarter "
                    "due to lower prices."
                ),
            ),
        ),
    )

    assert (
        assessment.status
        == "potential_tension"
    )


def test_aligned_context_is_insufficient():
    assessment = assess_consistency(
        metric_id=(
            "adjusted_operating_income"
        ),
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            availability=(
                "aligned_context_only"
            ),
            sentences=(),
        ),
    )

    assert (
        assessment.status
        == "insufficient_evidence"
    )

    assert (
        assessment.narrative_directions
        == ()
    )


def test_unavailable_evidence_is_insufficient():
    assessment = assess_consistency(
        metric_id="net_operating_income",
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            availability="unavailable",
            sentences=(),
        ),
    )

    assert (
        assessment.status
        == "insufficient_evidence"
    )


def test_missing_evidence_is_insufficient():
    assessment = assess_consistency(
        metric_id="net_income",
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=None,
    )

    assert (
        assessment.status
        == "insufficient_evidence"
    )


def test_comparison_mismatch_is_not_comparable():
    assessment = assess_consistency(
        metric_id="net_operating_income",
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            comparison_type="yoy",
            sentences=(
                (
                    "Net operating income increased "
                    "compared to last year."
                ),
            ),
        ),
    )

    assert (
        assessment.status
        == "not_comparable"
    )


def test_other_comparison_is_not_comparable():
    assessment = assess_consistency(
        metric_id="net_operating_income",
        absolute_change=100,
        comparison_type="other",
        evidence_assessment=None,
    )

    assert (
        assessment.status
        == "not_comparable"
    )


def test_conflicting_direct_evidence_is_insufficient():
    assessment = assess_consistency(
        metric_id="net_operating_income",
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            sentences=(
                (
                    "Net operating income increased "
                    "compared to the prior quarter."
                ),
                (
                    "Net operating income decreased "
                    "compared to the prior quarter."
                ),
            ),
        ),
    )

    assert (
        assessment.status
        == "insufficient_evidence"
    )


def test_unknown_direct_direction_is_insufficient():
    assessment = assess_consistency(
        metric_id="net_operating_income",
        absolute_change=100,
        comparison_type="qoq",
        evidence_assessment=_evidence(
            sentences=(
                (
                    "Management discussed net "
                    "operating income during "
                    "the quarter."
                ),
            ),
        ),
    )

    assert (
        assessment.status
        == "insufficient_evidence"
    )
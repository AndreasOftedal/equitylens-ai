from types import SimpleNamespace

import pytest

from equitylens.synthesis_eval import (
    SynthesisEvalCase,
    run_synthesis_eval,
)
from equitylens.synthesis_output import (
    SynthesisDraft,
)


def _draft(
    title="Test synthesis",
):
    return SynthesisDraft(
        schema_version="1.0",
        title=title,
        claims=(),
        limitations=(),
    )


def _case(
    case_id,
    expected_outcome,
):
    return SynthesisEvalCase(
        case_id=case_id,
        description=(
            f"Evaluation case {case_id}"
        ),
        draft=_draft(),
        expected_outcome=(
            expected_outcome
        ),
    )


def test_expected_acceptance_passes(
    monkeypatch,
):
    monkeypatch.setattr(
        "equitylens.synthesis_eval."
        "validate_synthesis_semantics",
        lambda synthesis_input, draft: None,
    )

    report = run_synthesis_eval(
        SimpleNamespace(),
        (
            _case(
                "valid-control",
                "accept",
            ),
        ),
    )

    result = report.results[0]

    assert result.passed is True
    assert (
        result.observed_outcome
        == "accept"
    )
    assert result.error_type is None
    assert result.error_message is None


def test_expected_rejection_passes(
    monkeypatch,
):
    def reject(
        synthesis_input,
        draft,
    ):
        raise ValueError(
            "guardrail rejected output"
        )

    monkeypatch.setattr(
        "equitylens.synthesis_eval."
        "validate_synthesis_semantics",
        reject,
    )

    report = run_synthesis_eval(
        SimpleNamespace(),
        (
            _case(
                "fabricated-number",
                "reject",
            ),
        ),
    )

    result = report.results[0]

    assert result.passed is True

    assert (
        result.observed_outcome
        == "reject"
    )

    assert (
        result.error_type
        == "ValueError"
    )

    assert (
        result.error_message
        == "guardrail rejected output"
    )


def test_unexpected_acceptance_is_eval_failure(
    monkeypatch,
):
    monkeypatch.setattr(
        "equitylens.synthesis_eval."
        "validate_synthesis_semantics",
        lambda synthesis_input, draft: None,
    )

    report = run_synthesis_eval(
        SimpleNamespace(),
        (
            _case(
                "attack-not-blocked",
                "reject",
            ),
        ),
    )

    result = report.results[0]

    assert result.passed is False

    assert (
        result.observed_outcome
        == "accept"
    )


def test_unexpected_rejection_is_eval_failure(
    monkeypatch,
):
    def reject(
        synthesis_input,
        draft,
    ):
        raise ValueError(
            "unexpected rejection"
        )

    monkeypatch.setattr(
        "equitylens.synthesis_eval."
        "validate_synthesis_semantics",
        reject,
    )

    report = run_synthesis_eval(
        SimpleNamespace(),
        (
            _case(
                "valid-control",
                "accept",
            ),
        ),
    )

    result = report.results[0]

    assert result.passed is False

    assert (
        result.observed_outcome
        == "reject"
    )


def test_report_calculates_pass_rate():
    calls = 0

    def alternating_validator(
        synthesis_input,
        draft,
    ):
        nonlocal calls

        calls += 1

        if calls == 2:
            raise ValueError(
                "rejected"
            )

    import equitylens.synthesis_eval as eval_module

    original_validator = (
        eval_module.validate_synthesis_semantics
    )

    eval_module.validate_synthesis_semantics = (
        alternating_validator
    )

    try:
        report = run_synthesis_eval(
            SimpleNamespace(),
            (
                _case(
                    "case-1",
                    "accept",
                ),
                _case(
                    "case-2",
                    "reject",
                ),
                _case(
                    "case-3",
                    "reject",
                ),
            ),
        )
    finally:
        eval_module.validate_synthesis_semantics = (
            original_validator
        )

    assert report.total_cases == 3
    assert report.passed_cases == 2
    assert report.failed_cases == 1

    assert report.pass_rate == pytest.approx(
        2 / 3
    )


def test_empty_eval_suite_is_rejected():
    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        run_synthesis_eval(
            SimpleNamespace(),
            (),
        )


def test_duplicate_case_ids_are_rejected():
    with pytest.raises(
        ValueError,
        match="case_ids must be unique",
    ):
        run_synthesis_eval(
            SimpleNamespace(),
            (
                _case(
                    "duplicate",
                    "accept",
                ),
                _case(
                    "duplicate",
                    "reject",
                ),
            ),
        )
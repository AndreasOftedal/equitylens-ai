from dataclasses import dataclass
from typing import Literal

from equitylens.synthesis_input import SynthesisInput
from equitylens.synthesis_output import SynthesisDraft
from equitylens.synthesis_semantics import validate_synthesis_semantics

EvalOutcome = Literal[
    "accept",
    "reject",
]


@dataclass(frozen=True)
class SynthesisEvalCase:
    case_id: str
    description: str
    draft: SynthesisDraft
    expected_outcome: EvalOutcome
    synthesis_input: SynthesisInput | None = None


@dataclass(frozen=True)
class SynthesisEvalResult:
    case_id: str
    description: str
    expected_outcome: EvalOutcome
    observed_outcome: EvalOutcome
    passed: bool
    error_type: str | None
    error_message: str | None


@dataclass(frozen=True)
class SynthesisEvalReport:
    results: tuple[SynthesisEvalResult, ...]

    @property
    def total_cases(self) -> int:
        return len(self.results)

    @property
    def passed_cases(self) -> int:
        return sum(
            result.passed
            for result in self.results
        )

    @property
    def failed_cases(self) -> int:
        return (
            self.total_cases
            - self.passed_cases
        )

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0

        return (
            self.passed_cases
            / self.total_cases
        )


def run_synthesis_eval(
    synthesis_input: SynthesisInput,
    cases: tuple[SynthesisEvalCase, ...],
) -> SynthesisEvalReport:
    """
    Evaluate synthesis guardrails against explicit
    expected accept/reject outcomes.

    Each case may optionally override the default
    synthesis input. This allows one benchmark to
    evaluate different evidence and consistency
    states without weakening the validators.

    A case passes only when the deterministic
    validators produce the expected outcome.
    """
    if not cases:
        raise ValueError(
            "At least one synthesis eval case "
            "is required."
        )

    case_ids = tuple(
        case.case_id
        for case in cases
    )

    if len(case_ids) != len(
        set(case_ids)
    ):
        raise ValueError(
            "Synthesis eval case_ids must be unique."
        )

    results: list[SynthesisEvalResult] = []

    for case in cases:
        error_type = None
        error_message = None

        case_input = (
            case.synthesis_input
            if case.synthesis_input is not None
            else synthesis_input
        )

        try:
            validate_synthesis_semantics(
                case_input,
                case.draft,
            )

            observed_outcome: EvalOutcome = (
                "accept"
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            observed_outcome = "reject"
            error_type = type(exc).__name__
            error_message = str(exc)

        results.append(
            SynthesisEvalResult(
                case_id=case.case_id,
                description=case.description,
                expected_outcome=(
                    case.expected_outcome
                ),
                observed_outcome=(
                    observed_outcome
                ),
                passed=(
                    observed_outcome
                    == case.expected_outcome
                ),
                error_type=error_type,
                error_message=error_message,
            )
        )

    return SynthesisEvalReport(
        results=tuple(results)
    )
from dataclasses import dataclass
from typing import Protocol

from equitylens.synthesis_input import SynthesisInput
from equitylens.synthesis_llm import SynthesisLLMResponse
from equitylens.synthesis_output import SynthesisDraft
from equitylens.synthesis_parser import parse_synthesis_response
from equitylens.synthesis_prompt import SynthesisPrompt, build_synthesis_prompt
from equitylens.synthesis_semantics import validate_synthesis_semantics

DEFAULT_MAX_ATTEMPTS = 2


class SynthesisGenerator(Protocol):
    def generate(
        self,
        prompt: SynthesisPrompt,
    ) -> SynthesisLLMResponse: ...


@dataclass(frozen=True)
class SynthesisFailure:
    attempt: int
    error_type: str
    error_message: str


@dataclass(frozen=True)
class ValidatedSynthesis:
    draft: SynthesisDraft
    model: str
    attempts: int
    failures: tuple[SynthesisFailure, ...]


def _build_retry_prompt(
    original_prompt: SynthesisPrompt,
    failure: SynthesisFailure,
) -> SynthesisPrompt:
    retry_instruction = (
        "\n\nPREVIOUS_OUTPUT_REJECTED\n"
        f"Attempt {failure.attempt} was rejected by EquityLens.\n"
        f"Validation error type: {failure.error_type}\n"
        f"Validation error: {failure.error_message}\n"
        "Produce a new complete JSON response from the original "
        "RESEARCH_DATA. Correct the validation issue without "
        "weakening, bypassing, or contradicting any original rule.\n"
        "For guidance_update claims, re-read the exact change_type in "
        "RESEARCH_DATA before writing the replacement claim. "
        "If change_type is 'unchanged', explicitly say the guidance "
        "'was unchanged' or 'remained unchanged'. "
        "If change_type is 'increased', explicitly say it 'increased'. "
        "If change_type is 'decreased', explicitly say it 'decreased'. "
        "If change_type is 'changed', use neutral wording such as "
        "'changed' or 'was revised' and do not assign an increase, "
        "decrease, or unchanged direction.\n"
        "Do not discuss the validation error in the response. "
        "Return JSON only.\n"
        "END_PREVIOUS_OUTPUT_REJECTED"
    )

    return SynthesisPrompt(
        system_message=original_prompt.system_message,
        user_message=(
            original_prompt.user_message
            + retry_instruction
        ),
    )


def _parse_and_validate(
    synthesis_input: SynthesisInput,
    response: SynthesisLLMResponse,
) -> SynthesisDraft:
    draft = parse_synthesis_response(
        response.raw_text
    )

    validate_synthesis_semantics(
        synthesis_input,
        draft,
    )

    return draft


def run_synthesis(
    synthesis_input: SynthesisInput,
    generator: SynthesisGenerator,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> ValidatedSynthesis:
    """
    Run the guarded EquityLens synthesis pipeline.

    Raw model output is never returned as an accepted
    synthesis result. It must pass the strict JSON parser
    and deterministic semantic validation.

    Parser or validation failures receive at most one
    controlled retry by default. The retry receives the
    original research data and validation feedback, but
    must pass the same unchanged guardrails.
    """
    if max_attempts < 1:
        raise ValueError(
            "max_attempts must be at least 1."
        )

    original_prompt = build_synthesis_prompt(
        synthesis_input
    )

    prompt = original_prompt
    failures: list[SynthesisFailure] = []

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        response = generator.generate(
            prompt
        )

        try:
            draft = _parse_and_validate(
                synthesis_input,
                response,
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            failure = SynthesisFailure(
                attempt=attempt,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            failures.append(
                failure
            )

            if attempt >= max_attempts:
                raise

            prompt = _build_retry_prompt(
                original_prompt,
                failure,
            )

            continue

        return ValidatedSynthesis(
            draft=draft,
            model=response.model,
            attempts=attempt,
            failures=tuple(
                failures
            ),
        )

    raise RuntimeError(
        "Synthesis pipeline exhausted attempts "
        "without returning or raising."
    )
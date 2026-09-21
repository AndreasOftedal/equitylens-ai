from dataclasses import dataclass
from typing import Protocol

from equitylens.synthesis_input import (
    SynthesisGuidanceChange,
    SynthesisGuidanceItem,
    SynthesisInput,
)
from equitylens.synthesis_llm import SynthesisLLMResponse
from equitylens.synthesis_output import (
    SynthesisClaim,
    SynthesisDraft,
)
from equitylens.synthesis_parser import parse_synthesis_response
from equitylens.synthesis_prompt import (
    SynthesisPrompt,
    build_synthesis_prompt,
)
from equitylens.synthesis_semantics import (
    validate_synthesis_semantics,
)

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
        "weakening, bypassing, or contradicting any original rule. "
        "Do not discuss the error. Return JSON only.\n"
        "END_PREVIOUS_OUTPUT_REJECTED"
    )

    return SynthesisPrompt(
        system_message=original_prompt.system_message,
        user_message=(
            original_prompt.user_message
            + retry_instruction
        ),
    )


def _guidance_label(
    metric_id: str,
) -> str:
    normalized = metric_id.removesuffix(
        "_guidance"
    )

    return (
        normalized
        .replace("_", " ")
        .strip()
        .capitalize()
    )


def _format_guidance_value(
    item: SynthesisGuidanceItem,
) -> str | None:
    if (
        item.numeric_lower_bound is not None
        and item.numeric_upper_bound is not None
    ):
        value = (
            f"{item.numeric_lower_bound}-"
            f"{item.numeric_upper_bound}"
        )

    elif item.numeric_value is not None:
        value = item.numeric_value

    elif item.qualitative_value:
        value = item.qualitative_value

    else:
        return None

    if item.qualifier:
        value = (
            f"{item.qualifier} {value}"
        )

    if item.unit:
        value = (
            f"{value} {item.unit}"
        )

    return value


def _build_guidance_change_text(
    change: SynthesisGuidanceChange,
) -> str:
    label = _guidance_label(
        change.metric_id
    )

    prefix = (
        f"{label} guidance for "
        f"{change.target_period}"
    )

    previous_value = (
        _format_guidance_value(
            change.previous
        )
    )

    current_value = (
        _format_guidance_value(
            change.current
        )
    )

    if change.change_type == "unchanged":
        if current_value is not None:
            return (
                f"{prefix} was unchanged at "
                f"{current_value}."
            )

        return (
            f"{prefix} was unchanged."
        )

    if change.change_type == "increased":
        if (
            previous_value is not None
            and current_value is not None
        ):
            return (
                f"{prefix} increased from "
                f"{previous_value} to "
                f"{current_value}."
            )

        if current_value is not None:
            return (
                f"{prefix} increased to "
                f"{current_value}."
            )

        return (
            f"{prefix} increased."
        )

    if change.change_type == "decreased":
        if (
            previous_value is not None
            and current_value is not None
        ):
            return (
                f"{prefix} decreased from "
                f"{previous_value} to "
                f"{current_value}."
            )

        if current_value is not None:
            return (
                f"{prefix} decreased to "
                f"{current_value}."
            )

        return (
            f"{prefix} decreased."
        )

    if (
        previous_value is not None
        and current_value is not None
    ):
        return (
            f"{prefix} was revised from "
            f"{previous_value} to "
            f"{current_value}."
        )

    return (
        f"{prefix} was revised."
    )


def _build_guidance_item_text(
    item: SynthesisGuidanceItem,
    status: str,
) -> str:
    label = _guidance_label(
        item.metric_id
    )

    prefix = (
        f"{label} guidance for "
        f"{item.target_period}"
    )

    value = _format_guidance_value(
        item
    )

    if (
        status == "introduced"
        and value is not None
    ):
        return (
            f"{prefix} was introduced at "
            f"{value}."
        )

    if status == "introduced":
        return (
            f"{prefix} was introduced."
        )

    if (
        status == "withdrawn"
        and value is not None
    ):
        return (
            f"{prefix} was withdrawn; "
            f"the previous level was "
            f"{value}."
        )

    return (
        f"{prefix} was withdrawn."
    )


def _build_deterministic_guidance_claim(
    synthesis_input: SynthesisInput,
    model_claim: SynthesisClaim,
) -> SynthesisClaim:
    if model_claim.target_period is None:
        raise ValueError(
            f"Claim '{model_claim.claim_id}' "
            "references guidance without a "
            "target_period."
        )

    key = (
        model_claim.metric_id,
        model_claim.target_period,
    )

    changes = {
        (
            change.metric_id,
            change.target_period,
        ): change
        for change
        in synthesis_input.guidance_changes
    }

    introduced = {
        (
            item.metric_id,
            item.target_period,
        ): item
        for item
        in synthesis_input.guidance_introduced
    }

    withdrawn = {
        (
            item.metric_id,
            item.target_period,
        ): item
        for item
        in synthesis_input.guidance_withdrawn
    }

    if key in changes:
        text = (
            _build_guidance_change_text(
                changes[key]
            )
        )

    elif key in introduced:
        text = (
            _build_guidance_item_text(
                introduced[key],
                "introduced",
            )
        )

    elif key in withdrawn:
        text = (
            _build_guidance_item_text(
                withdrawn[key],
                "withdrawn",
            )
        )

    else:
        raise ValueError(
            f"Claim '{model_claim.claim_id}' "
            "references unknown guidance."
        )

    return SynthesisClaim(
        claim_id=model_claim.claim_id,
        claim_type="guidance_update",
        text=text,
        metric_id=model_claim.metric_id,
        target_period=(
            model_claim.target_period
        ),
    )


def _replace_model_guidance_claims(
    synthesis_input: SynthesisInput,
    draft: SynthesisDraft,
) -> SynthesisDraft:
    claims = tuple(
        (
            _build_deterministic_guidance_claim(
                synthesis_input,
                claim,
            )
            if (
                claim.claim_type
                == "guidance_update"
            )
            else claim
        )
        for claim in draft.claims
    )

    return SynthesisDraft(
        schema_version=draft.schema_version,
        title=draft.title,
        claims=claims,
        limitations=draft.limitations,
    )


def _parse_and_validate(
    synthesis_input: SynthesisInput,
    response: SynthesisLLMResponse,
) -> SynthesisDraft:
    model_draft = (
        parse_synthesis_response(
            response.raw_text
        )
    )

    final_draft = (
        _replace_model_guidance_claims(
            synthesis_input,
            model_draft,
        )
    )

    validate_synthesis_semantics(
        synthesis_input,
        final_draft,
    )

    return final_draft


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

    The model may select which guidance items are relevant
    to the synthesis, but it does not control the accepted
    wording of guidance claims. Selected guidance claims
    are rebuilt deterministically from structured
    EquityLens guidance data before validation.

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
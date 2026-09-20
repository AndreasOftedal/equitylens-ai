from dataclasses import dataclass
from typing import Literal

from equitylens.synthesis_input import SynthesisInput

SynthesisClaimType = Literal[
    "financial_observation",
    "management_explanation",
    "consistency_observation",
    "guidance_update",
]


@dataclass(frozen=True)
class SynthesisClaim:
    claim_id: str
    claim_type: SynthesisClaimType
    text: str
    metric_id: str
    target_period: str | None = None
    source_fact_ids: tuple[str, ...] = ()
    evidence_sentence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SynthesisDraft:
    schema_version: str
    title: str
    claims: tuple[SynthesisClaim, ...]
    limitations: tuple[str, ...]


def _require_exact_source_facts(
    claim: SynthesisClaim,
    metric,
) -> None:
    expected = tuple(
        fact.fact_id
        for fact in metric.source_facts
    )

    actual = claim.source_fact_ids

    if (
        len(actual) != len(set(actual))
        or set(actual) != set(expected)
    ):
        raise ValueError(
            f"Claim '{claim.claim_id}' must cite "
            "the exact deterministic source facts "
            f"for metric '{claim.metric_id}'."
        )


def _validate_financial_observation(
    claim: SynthesisClaim,
    metric,
) -> None:
    if claim.target_period is not None:
        raise ValueError(
            "Financial observations cannot contain "
            "a guidance target_period."
        )

    _require_exact_source_facts(
        claim,
        metric,
    )

    if claim.evidence_sentence_ids:
        raise ValueError(
            "Financial observations cannot cite "
            "management narrative evidence."
        )


def _validate_management_explanation(
    claim: SynthesisClaim,
    metric,
) -> None:
    if claim.target_period is not None:
        raise ValueError(
            "Management explanations cannot contain "
            "a guidance target_period."
        )

    _require_exact_source_facts(
        claim,
        metric,
    )

    if (
        metric.evidence_availability
        != "direct_explanation"
    ):
        raise ValueError(
            f"Metric '{claim.metric_id}' has no "
            "validated direct management "
            "explanation."
        )

    allowed_sentence_ids = {
        evidence.sentence_id
        for evidence
        in metric.direct_explanations
    }

    if not claim.evidence_sentence_ids:
        raise ValueError(
            "Management explanations must cite at "
            "least one direct evidence sentence."
        )

    if len(
        claim.evidence_sentence_ids
    ) != len(
        set(
            claim.evidence_sentence_ids
        )
    ):
        raise ValueError(
            "Evidence sentence citations must be "
            "unique within a claim."
        )

    unsupported = (
        set(
            claim.evidence_sentence_ids
        )
        - allowed_sentence_ids
    )

    if unsupported:
        raise ValueError(
            "Management explanation cites "
            "unsupported evidence sentence IDs: "
            f"{sorted(unsupported)}."
        )


def _validate_consistency_observation(
    claim: SynthesisClaim,
    metric,
) -> None:
    if claim.target_period is not None:
        raise ValueError(
            "Consistency observations cannot "
            "contain a guidance target_period."
        )

    _require_exact_source_facts(
        claim,
        metric,
    )

    if metric.consistency_status not in {
        "consistent",
        "potential_tension",
    }:
        raise ValueError(
            f"Metric '{claim.metric_id}' does not "
            "support a consistency conclusion."
        )

    allowed_sentence_ids = {
        evidence.sentence_id
        for evidence
        in metric.direct_explanations
    }

    if not claim.evidence_sentence_ids:
        raise ValueError(
            "Consistency observations must cite at "
            "least one direct evidence sentence."
        )

    if len(
        claim.evidence_sentence_ids
    ) != len(
        set(
            claim.evidence_sentence_ids
        )
    ):
        raise ValueError(
            "Evidence sentence citations must be "
            "unique within a claim."
        )

    unsupported = (
        set(
            claim.evidence_sentence_ids
        )
        - allowed_sentence_ids
    )

    if unsupported:
        raise ValueError(
            "Consistency observation cites "
            "unsupported evidence sentence IDs: "
            f"{sorted(unsupported)}."
        )


def _validate_guidance_update(
    claim: SynthesisClaim,
    synthesis_input: SynthesisInput,
) -> None:
    if claim.target_period is None:
        raise ValueError(
            "Guidance updates require a "
            "target_period."
        )

    if claim.source_fact_ids:
        raise ValueError(
            "Guidance updates cannot cite "
            "historical financial source facts."
        )

    if claim.evidence_sentence_ids:
        raise ValueError(
            "Guidance updates cannot cite "
            "management narrative evidence IDs."
        )

    guidance_keys = {
        (
            guidance.metric_id,
            guidance.target_period,
        )
        for guidance
        in synthesis_input.guidance_changes
    }

    guidance_keys.update(
        (
            guidance.metric_id,
            guidance.target_period,
        )
        for guidance
        in synthesis_input.guidance_introduced
    )

    guidance_keys.update(
        (
            guidance.metric_id,
            guidance.target_period,
        )
        for guidance
        in synthesis_input.guidance_withdrawn
    )

    key = (
        claim.metric_id,
        claim.target_period,
    )

    if key not in guidance_keys:
        raise ValueError(
            "Guidance update references an "
            "unknown guidance item: "
            f"{key}."
        )


def validate_synthesis_draft(
    synthesis_input: SynthesisInput,
    draft: SynthesisDraft,
) -> None:
    """
    Validate whether an LLM synthesis draft stays
    inside the structured research evidence boundary.

    This validator checks provenance and claim
    eligibility. It deliberately does not treat
    free-form text as trusted merely because a
    citation exists.
    """

    if draft.schema_version != "1.0":
        raise ValueError(
            "Unsupported synthesis draft "
            "schema_version."
        )

    if not draft.title.strip():
        raise ValueError(
            "Synthesis title cannot be empty."
        )

    claim_ids = tuple(
        claim.claim_id
        for claim
        in draft.claims
    )

    if len(claim_ids) != len(
        set(claim_ids)
    ):
        raise ValueError(
            "Synthesis claim_ids must be unique."
        )

    metrics_by_id = {
        metric.metric_id: metric
        for metric
        in synthesis_input.metrics
    }

    for claim in draft.claims:
        if not claim.claim_id.strip():
            raise ValueError(
                "claim_id cannot be empty."
            )

        if not claim.text.strip():
            raise ValueError(
                f"Claim '{claim.claim_id}' "
                "cannot have empty text."
            )

        if not claim.metric_id.strip():
            raise ValueError(
                f"Claim '{claim.claim_id}' "
                "must contain a metric_id."
            )

        if (
            claim.claim_type
            == "guidance_update"
        ):
            _validate_guidance_update(
                claim=claim,
                synthesis_input=(
                    synthesis_input
                ),
            )
            continue

        metric = metrics_by_id.get(
            claim.metric_id
        )

        if metric is None:
            raise ValueError(
                f"Claim '{claim.claim_id}' "
                "references an unknown financial "
                f"metric '{claim.metric_id}'."
            )

        if (
            claim.claim_type
            == "financial_observation"
        ):
            _validate_financial_observation(
                claim,
                metric,
            )

        elif (
            claim.claim_type
            == "management_explanation"
        ):
            _validate_management_explanation(
                claim,
                metric,
            )

        elif (
            claim.claim_type
            == "consistency_observation"
        ):
            _validate_consistency_observation(
                claim,
                metric,
            )

        else:
            raise ValueError(
                "Unsupported synthesis "
                f"claim_type: {claim.claim_type}."
            )
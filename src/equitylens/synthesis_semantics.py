import re
from decimal import Decimal, InvalidOperation

from equitylens.narrative_direction import detect_narrative_direction
from equitylens.synthesis_input import SynthesisInput, SynthesisMetric
from equitylens.synthesis_output import (
    SynthesisClaim,
    SynthesisDraft,
    validate_synthesis_draft,
)

_NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[-+]?\d[\d,]*(?:\.\d+)?"
)

_CONSISTENT_PATTERN = re.compile(
    r"\b(?:consistent|aligned|in line)\b",
    re.IGNORECASE,
)

_TENSION_PATTERN = re.compile(
    (
        r"\b(?:potential tension|tension|conflict|"
        r"inconsistent|contradiction|contradictory)\b"
        r"|\bdoes not align\b"
        r"|\bnot consistent\b"
    ),
    re.IGNORECASE,
)

_GUIDANCE_UNCHANGED_PATTERNS = (
    r"\bguidance\b.{0,120}\bremained\s+(?:broadly\s+)?unchanged\b",
    r"\bguidance\b.{0,120}\b(?:was|is|were|are)\s+(?:broadly\s+)?unchanged\b",
    r"\bguidance\b.{0,120}\bstayed\s+(?:broadly\s+)?unchanged\b",
    r"\bremained\s+(?:broadly\s+)?unchanged\b",
    r"\bstayed\s+(?:broadly\s+)?unchanged\b",
    r"\bunchanged\s+guidance\b",
)

_GUIDANCE_INCREASE_PATTERNS = (
    r"\bguidance\b.{0,120}\b(?:increased|raised|upgraded)\b",
    r"\b(?:increased|raised|upgraded)\s+guidance\b",
)

_GUIDANCE_DECREASE_PATTERNS = (
    r"\bguidance\b.{0,120}\b(?:decreased|lowered|reduced|downgraded)\b",
    r"\b(?:decreased|lowered|reduced|downgraded)\s+guidance\b",
)


def _extract_numbers(
    text: str,
) -> set[Decimal]:
    values: set[Decimal] = set()

    for match in _NUMBER_PATTERN.finditer(
        text
    ):
        token = (
            match.group(0)
            .replace(",", "")
        )

        try:
            value = Decimal(token)
        except InvalidOperation:
            continue

        values.add(value)

    return values


def _add_number_and_absolute(
    values: set[Decimal],
    raw_value: str,
) -> None:
    value = Decimal(raw_value)

    values.add(value)
    values.add(abs(value))


def _financial_allowed_numbers(
    metric: SynthesisMetric,
    claim: SynthesisClaim,
) -> set[Decimal]:
    allowed: set[Decimal] = set()

    for raw_value in (
        metric.from_value,
        metric.to_value,
        metric.absolute_change,
        metric.percentage_change,
    ):
        _add_number_and_absolute(
            allowed,
            raw_value,
        )

    allowed.update(
        _extract_numbers(
            metric.from_period
        )
    )

    allowed.update(
        _extract_numbers(
            metric.to_period
        )
    )

    evidence_by_id = {
        evidence.sentence_id: evidence
        for evidence
        in metric.direct_explanations
    }

    for sentence_id in (
        claim.evidence_sentence_ids
    ):
        evidence = evidence_by_id.get(
            sentence_id
        )

        if evidence is not None:
            allowed.update(
                _extract_numbers(
                    evidence.text
                )
            )

    return allowed


def _validate_supported_numbers(
    claim: SynthesisClaim,
    allowed_numbers: set[Decimal],
) -> None:
    claimed_numbers = _extract_numbers(
        claim.text
    )

    unsupported = sorted(
        claimed_numbers - allowed_numbers
    )

    if unsupported:
        raise ValueError(
            f"Claim '{claim.claim_id}' contains "
            "unsupported numeric values: "
            f"{unsupported}."
        )


def _validate_financial_direction(
    claim: SynthesisClaim,
    metric: SynthesisMetric,
    *,
    require_direction: bool,
) -> None:
    detected = detect_narrative_direction(
        claim.text
    )

    if detected == "mixed":
        raise ValueError(
            f"Claim '{claim.claim_id}' contains "
            "mixed financial directions."
        )

    if detected == "unknown":
        if require_direction:
            raise ValueError(
                f"Claim '{claim.claim_id}' must "
                "state an explicit supported "
                "financial direction."
            )

        return

    if (
        detected
        != metric.financial_direction
    ):
        raise ValueError(
            f"Claim '{claim.claim_id}' states "
            f"financial direction '{detected}', "
            "but the deterministic direction is "
            f"'{metric.financial_direction}'."
        )


def _validate_financial_claim(
    claim: SynthesisClaim,
    metric: SynthesisMetric,
) -> None:
    _validate_financial_direction(
        claim,
        metric,
        require_direction=True,
    )

    _validate_supported_numbers(
        claim,
        _financial_allowed_numbers(
            metric,
            claim,
        ),
    )


def _validate_management_claim(
    claim: SynthesisClaim,
    metric: SynthesisMetric,
) -> None:
    _validate_financial_direction(
        claim,
        metric,
        require_direction=False,
    )

    _validate_supported_numbers(
        claim,
        _financial_allowed_numbers(
            metric,
            claim,
        ),
    )


def _validate_consistency_claim(
    claim: SynthesisClaim,
    metric: SynthesisMetric,
) -> None:
    text = claim.text

    has_consistent_signal = (
        _CONSISTENT_PATTERN.search(
            text
        )
        is not None
    )

    has_tension_signal = (
        _TENSION_PATTERN.search(
            text
        )
        is not None
    )

    if (
        metric.consistency_status
        == "consistent"
    ):
        if (
            not has_consistent_signal
            or has_tension_signal
        ):
            raise ValueError(
                f"Claim '{claim.claim_id}' does "
                "not semantically match consistency "
                "status 'consistent'."
            )

    elif (
        metric.consistency_status
        == "potential_tension"
        and not has_tension_signal
    ):
        raise ValueError(
            f"Claim '{claim.claim_id}' does "
            "not semantically match consistency "
            "status 'potential_tension'."
        )

    _validate_supported_numbers(
        claim,
        _financial_allowed_numbers(
            metric,
            claim,
        ),
    )


def _find_guidance_reference(
    synthesis_input: SynthesisInput,
    claim: SynthesisClaim,
):
    key = (
        claim.metric_id,
        claim.target_period,
    )

    for change in (
        synthesis_input.guidance_changes
    ):
        if (
            change.metric_id,
            change.target_period,
        ) == key:
            return (
                "change",
                change,
            )

    for item in (
        synthesis_input.guidance_introduced
    ):
        if (
            item.metric_id,
            item.target_period,
        ) == key:
            return (
                "introduced",
                item,
            )

    for item in (
        synthesis_input.guidance_withdrawn
    ):
        if (
            item.metric_id,
            item.target_period,
        ) == key:
            return (
                "withdrawn",
                item,
            )

    raise ValueError(
        f"Claim '{claim.claim_id}' references "
        "unknown guidance."
    )


def _guidance_allowed_numbers(
    kind: str,
    guidance,
) -> set[Decimal]:
    allowed: set[Decimal] = set()

    if kind == "change":
        items = (
            guidance.previous,
            guidance.current,
        )
    else:
        items = (
            guidance,
        )

    for item in items:
        allowed.update(
            _extract_numbers(
                item.target_period
            )
        )

        allowed.update(
            _extract_numbers(
                item.statement
            )
        )

        for raw_value in (
            item.numeric_value,
            getattr(
                item,
                "numeric_lower_bound",
                None,
            ),
            getattr(
                item,
                "numeric_upper_bound",
                None,
            ),
        ):
            if raw_value is not None:
                _add_number_and_absolute(
                    allowed,
                    raw_value,
                )

    return allowed


def _contains_pattern(
    text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            re.IGNORECASE,
        )
        is not None
        for pattern in patterns
    )


def _detect_guidance_change_direction(
    text: str,
) -> str:
    """
    Detect how guidance itself changed.

    This deliberately differs from financial narrative
    direction detection. A claim such as
    "production growth guidance remained unchanged at 3%"
    describes unchanged guidance even though the underlying
    guidance target contains the word "growth".
    """

    has_unchanged = _contains_pattern(
        text,
        _GUIDANCE_UNCHANGED_PATTERNS,
    )

    has_increase = _contains_pattern(
        text,
        _GUIDANCE_INCREASE_PATTERNS,
    )

    has_decrease = _contains_pattern(
        text,
        _GUIDANCE_DECREASE_PATTERNS,
    )

    directions_detected = sum(
        (
            has_unchanged,
            has_increase,
            has_decrease,
        )
    )

    if directions_detected == 0:
        return "unknown"

    if directions_detected > 1:
        return "mixed"

    if has_unchanged:
        return "unchanged"

    if has_increase:
        return "increase"

    return "decrease"


def _validate_guidance_claim(
    synthesis_input: SynthesisInput,
    claim: SynthesisClaim,
) -> None:
    kind, guidance = (
        _find_guidance_reference(
            synthesis_input,
            claim,
        )
    )

    if kind == "change":
        expected_direction = {
            "increased": "increase",
            "decreased": "decrease",
            "unchanged": "unchanged",
        }.get(
            guidance.change_type
        )

        detected = (
            _detect_guidance_change_direction(
                claim.text
            )
        )

        if (
            expected_direction is not None
            and detected
            != expected_direction
        ):
            raise ValueError(
                f"Claim '{claim.claim_id}' does "
                "not match guidance change type "
                f"'{guidance.change_type}'."
            )

        if (
            expected_direction is None
            and detected
            in {
                "increase",
                "decrease",
                "unchanged",
            }
        ):
            raise ValueError(
                f"Claim '{claim.claim_id}' assigns "
                "a directional meaning to "
                "non-directional guidance change."
            )

    _validate_supported_numbers(
        claim,
        _guidance_allowed_numbers(
            kind,
            guidance,
        ),
    )


def validate_synthesis_semantics(
    synthesis_input: SynthesisInput,
    draft: SynthesisDraft,
) -> None:
    """
    Validate that accepted synthesis claims also
    semantically agree with deterministic research
    data.

    Provenance and claim eligibility are validated
    first. This layer then checks financial direction,
    numeric values, consistency wording and guidance
    direction.
    """

    validate_synthesis_draft(
        synthesis_input,
        draft,
    )

    metrics_by_id = {
        metric.metric_id: metric
        for metric
        in synthesis_input.metrics
    }

    for claim in draft.claims:
        if (
            claim.claim_type
            == "guidance_update"
        ):
            _validate_guidance_claim(
                synthesis_input,
                claim,
            )
            continue

        metric = metrics_by_id[
            claim.metric_id
        ]

        if (
            claim.claim_type
            == "financial_observation"
        ):
            _validate_financial_claim(
                claim,
                metric,
            )

        elif (
            claim.claim_type
            == "management_explanation"
        ):
            _validate_management_claim(
                claim,
                metric,
            )

        elif (
            claim.claim_type
            == "consistency_observation"
        ):
            _validate_consistency_claim(
                claim,
                metric,
            )
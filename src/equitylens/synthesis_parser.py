import json
from typing import Any

from equitylens.synthesis_output import (
    SynthesisClaim,
    SynthesisClaimType,
    SynthesisDraft,
)

_ROOT_KEYS = {
    "schema_version",
    "title",
    "claims",
    "limitations",
}


_CLAIM_KEYS = {
    "claim_id",
    "claim_type",
    "text",
    "metric_id",
    "target_period",
    "source_fact_ids",
    "evidence_sentence_ids",
}


_ALLOWED_CLAIM_TYPES = {
    "financial_observation",
    "management_explanation",
    "consistency_observation",
    "guidance_update",
}


def _require_object(
    value: Any,
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(
            f"{field_name} must be a JSON object."
        )

    return value


def _require_exact_keys(
    value: dict[str, Any],
    expected_keys: set[str],
    field_name: str,
) -> None:
    actual_keys = set(value)

    missing = sorted(
        expected_keys - actual_keys
    )

    extra = sorted(
        actual_keys - expected_keys
    )

    if missing or extra:
        raise ValueError(
            f"{field_name} has invalid fields. "
            f"Missing: {missing}. Extra: {extra}."
        )


def _require_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string."
        )

    return value


def _require_optional_string(
    value: Any,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _require_string(
        value,
        field_name,
    )


def _require_string_list(
    value: Any,
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError(
            f"{field_name} must be a JSON array."
        )

    result: list[str] = []

    for index, item in enumerate(
        value
    ):
        if not isinstance(item, str):
            raise TypeError(
                f"{field_name}[{index}] "
                "must be a string."
            )

        result.append(item)

    return tuple(result)


def _parse_claim(
    raw_claim: Any,
    index: int,
) -> SynthesisClaim:
    field_name = f"claims[{index}]"

    claim = _require_object(
        raw_claim,
        field_name,
    )

    _require_exact_keys(
        claim,
        _CLAIM_KEYS,
        field_name,
    )

    claim_type_raw = _require_string(
        claim["claim_type"],
        f"{field_name}.claim_type",
    )

    if (
        claim_type_raw
        not in _ALLOWED_CLAIM_TYPES
    ):
        raise ValueError(
            f"{field_name}.claim_type is "
            f"unsupported: {claim_type_raw}."
        )

    claim_type: SynthesisClaimType = (
        claim_type_raw
    )

    return SynthesisClaim(
        claim_id=_require_string(
            claim["claim_id"],
            f"{field_name}.claim_id",
        ),
        claim_type=claim_type,
        text=_require_string(
            claim["text"],
            f"{field_name}.text",
        ),
        metric_id=_require_string(
            claim["metric_id"],
            f"{field_name}.metric_id",
        ),
        target_period=(
            _require_optional_string(
                claim["target_period"],
                f"{field_name}.target_period",
            )
        ),
        source_fact_ids=(
            _require_string_list(
                claim["source_fact_ids"],
                f"{field_name}.source_fact_ids",
            )
        ),
        evidence_sentence_ids=(
            _require_string_list(
                claim[
                    "evidence_sentence_ids"
                ],
                (
                    f"{field_name}."
                    "evidence_sentence_ids"
                ),
            )
        ),
    )


def parse_synthesis_response(
    raw_response: str,
) -> SynthesisDraft:
    """
    Parse an LLM response into the strict
    SynthesisDraft contract.

    The parser accepts JSON only and rejects missing
    fields, unknown fields, unsupported claim types,
    and incorrect JSON value types.
    """

    if not raw_response.strip():
        raise ValueError(
            "Synthesis response cannot be empty."
        )

    try:
        decoded = json.loads(
            raw_response
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Synthesis response must be valid JSON."
        ) from exc

    root = _require_object(
        decoded,
        "response",
    )

    _require_exact_keys(
        root,
        _ROOT_KEYS,
        "response",
    )

    claims_raw = root["claims"]

    if not isinstance(
        claims_raw,
        list,
    ):
        raise TypeError(
            "claims must be a JSON array."
        )

    limitations = _require_string_list(
        root["limitations"],
        "limitations",
    )

    claims = tuple(
        _parse_claim(
            raw_claim,
            index,
        )
        for index, raw_claim
        in enumerate(claims_raw)
    )

    return SynthesisDraft(
        schema_version=_require_string(
            root["schema_version"],
            "schema_version",
        ),
        title=_require_string(
            root["title"],
            "title",
        ),
        claims=claims,
        limitations=limitations,
    )
import json

import pytest

from equitylens.synthesis_parser import (
    parse_synthesis_response,
)


def _valid_payload():
    return {
        "schema_version": "1.0",
        "title": "Equinor Q2 2026 review",
        "claims": [
            {
                "claim_id": "claim-1",
                "claim_type": (
                    "financial_observation"
                ),
                "text": (
                    "Net operating income "
                    "increased from Q1 to Q2."
                ),
                "metric_id": (
                    "net_operating_income"
                ),
                "target_period": None,
                "source_fact_ids": [
                    "fact-q1",
                    "fact-q2",
                ],
                "evidence_sentence_ids": [],
            }
        ],
        "limitations": [
            (
                "No validated direct management "
                "explanation was available."
            )
        ],
    }


def test_valid_response_is_parsed():
    draft = parse_synthesis_response(
        json.dumps(
            _valid_payload()
        )
    )

    assert draft.schema_version == "1.0"

    assert (
        draft.title
        == "Equinor Q2 2026 review"
    )

    assert len(draft.claims) == 1

    claim = draft.claims[0]

    assert claim.claim_id == "claim-1"

    assert (
        claim.claim_type
        == "financial_observation"
    )

    assert (
        claim.metric_id
        == "net_operating_income"
    )

    assert claim.target_period is None

    assert (
        claim.source_fact_ids
        == (
            "fact-q1",
            "fact-q2",
        )
    )


def test_empty_response_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        parse_synthesis_response(
            "   "
        )


def test_invalid_json_is_rejected():
    with pytest.raises(
        ValueError,
        match="must be valid JSON",
    ):
        parse_synthesis_response(
            "{not-json}"
        )


def test_markdown_wrapped_json_is_rejected():
    raw = (
        "```json\n"
        + json.dumps(
            _valid_payload()
        )
        + "\n```"
    )

    with pytest.raises(
        ValueError,
        match="must be valid JSON",
    ):
        parse_synthesis_response(
            raw
        )


def test_root_must_be_object():
    with pytest.raises(
        TypeError,
        match=(
            "response must be a JSON object"
        ),
    ):
        parse_synthesis_response(
            "[]"
        )


def test_missing_root_field_is_rejected():
    payload = _valid_payload()

    del payload["limitations"]

    with pytest.raises(
        ValueError,
        match="invalid fields",
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_extra_root_field_is_rejected():
    payload = _valid_payload()

    payload["analysis"] = (
        "hidden free-form output"
    )

    with pytest.raises(
        ValueError,
        match="invalid fields",
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_claims_must_be_array():
    payload = _valid_payload()

    payload["claims"] = {}

    with pytest.raises(
        TypeError,
        match=(
            "claims must be a JSON array"
        ),
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_extra_claim_field_is_rejected():
    payload = _valid_payload()

    payload["claims"][0][
        "confidence"
    ] = 0.99

    with pytest.raises(
        ValueError,
        match="invalid fields",
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_unknown_claim_type_is_rejected():
    payload = _valid_payload()

    payload["claims"][0][
        "claim_type"
    ] = "price_target"

    with pytest.raises(
        ValueError,
        match="unsupported",
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_target_period_must_be_string_or_null():
    payload = _valid_payload()

    payload["claims"][0][
        "target_period"
    ] = 2026

    with pytest.raises(
        TypeError,
        match=(
            "target_period must be a string"
        ),
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_source_fact_ids_must_be_array():
    payload = _valid_payload()

    payload["claims"][0][
        "source_fact_ids"
    ] = "fact-q1"

    with pytest.raises(
        TypeError,
        match=(
            "source_fact_ids must be "
            "a JSON array"
        ),
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_source_fact_ids_must_contain_strings():
    payload = _valid_payload()

    payload["claims"][0][
        "source_fact_ids"
    ] = [
        "fact-q1",
        123,
    ]

    with pytest.raises(
        TypeError,
        match=(
            r"source_fact_ids\[1\] "
            "must be a string"
        ),
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )


def test_limitations_must_contain_strings():
    payload = _valid_payload()

    payload["limitations"] = [
        "Valid limitation",
        42,
    ]

    with pytest.raises(
        TypeError,
        match=(
            r"limitations\[1\] "
            "must be a string"
        ),
    ):
        parse_synthesis_response(
            json.dumps(payload)
        )
from types import SimpleNamespace

import pytest

from equitylens.synthesis_llm import (
    CLAIM_TYPES,
    DEFAULT_MODEL,
    SYNTHESIS_JSON_SCHEMA,
    OpenAISynthesisClient,
)
from equitylens.synthesis_prompt import SynthesisPrompt


class FakeResponses:
    def __init__(
        self,
        output_text,
    ):
        self.output_text = output_text
        self.calls = []

    def create(
        self,
        **kwargs,
    ):
        self.calls.append(
            kwargs
        )

        return SimpleNamespace(
            output_text=self.output_text
        )


class FakeOpenAI:
    def __init__(
        self,
        output_text=(
            '{"schema_version":"1.0",'
            '"title":"Test",'
            '"claims":[],'
            '"limitations":[]}'
        ),
    ):
        self.responses = FakeResponses(
            output_text
        )


def _prompt():
    return SynthesisPrompt(
        system_message=(
            "Use only supplied research data."
        ),
        user_message=(
            "RESEARCH_DATA_START\n{}\n"
            "RESEARCH_DATA_END"
        ),
    )


def _claim_variants():
    return (
        SYNTHESIS_JSON_SCHEMA[
            "properties"
        ]["claims"]["items"]["anyOf"]
    )


def _claim_variant(
    claim_type,
):
    for variant in _claim_variants():
        allowed_types = (
            variant[
                "properties"
            ]["claim_type"]["enum"]
        )

        if allowed_types == [
            claim_type
        ]:
            return variant

    raise AssertionError(
        f"Missing schema variant for {claim_type}."
    )


def test_default_model_is_luna():
    client = OpenAISynthesisClient(
        client=FakeOpenAI()
    )

    assert (
        client.model
        == DEFAULT_MODEL
    )

    assert (
        client.model
        == "gpt-5.6-luna"
    )


def test_generate_calls_responses_api_with_guarded_prompt():
    fake_client = FakeOpenAI()

    client = OpenAISynthesisClient(
        model="test-model",
        client=fake_client,
    )

    result = client.generate(
        _prompt()
    )

    assert result.model == "test-model"

    assert result.raw_text.startswith(
        "{"
    )

    assert len(
        fake_client.responses.calls
    ) == 1

    call = (
        fake_client.responses.calls[0]
    )

    assert (
        call["model"]
        == "test-model"
    )

    assert (
        call["instructions"]
        == _prompt().system_message
    )

    assert (
        call["input"]
        == _prompt().user_message
    )

    assert (
        call["reasoning"]
        == {
            "effort": "low",
        }
    )


def test_generate_requests_strict_structured_output():
    fake_client = FakeOpenAI()

    client = OpenAISynthesisClient(
        client=fake_client
    )

    client.generate(
        _prompt()
    )

    call = (
        fake_client.responses.calls[0]
    )

    output_format = (
        call["text"]["format"]
    )

    assert (
        output_format["type"]
        == "json_schema"
    )

    assert (
        output_format["name"]
        == "equitylens_synthesis"
    )

    assert (
        output_format["strict"]
        is True
    )

    assert (
        output_format["schema"]
        == SYNTHESIS_JSON_SCHEMA
    )


def test_schema_forbids_unknown_root_fields():
    assert (
        SYNTHESIS_JSON_SCHEMA[
            "additionalProperties"
        ]
        is False
    )


def test_schema_has_one_variant_per_claim_type():
    variants = _claim_variants()

    assert len(
        variants
    ) == len(
        CLAIM_TYPES
    )

    schema_claim_types = {
        variant[
            "properties"
        ]["claim_type"]["enum"][0]
        for variant in variants
    }

    assert schema_claim_types == set(
        CLAIM_TYPES
    )


def test_schema_forbids_unknown_claim_fields():
    for variant in _claim_variants():
        assert (
            variant[
                "additionalProperties"
            ]
            is False
        )


@pytest.mark.parametrize(
    "claim_type",
    [
        "financial_observation",
        "management_explanation",
        "consistency_observation",
    ],
)
def test_historical_claims_require_null_target_period(
    claim_type,
):
    variant = _claim_variant(
        claim_type
    )

    assert (
        variant[
            "properties"
        ]["target_period"]
        == {
            "type": "null",
        }
    )


def test_guidance_claim_requires_string_target_period():
    variant = _claim_variant(
        "guidance_update"
    )

    assert (
        variant[
            "properties"
        ]["target_period"]
        == {
            "type": "string",
        }
    )


def test_empty_model_is_rejected():
    with pytest.raises(
        ValueError,
        match="model cannot be empty",
    ):
        OpenAISynthesisClient(
            model="   ",
            client=FakeOpenAI(),
        )


def test_empty_system_message_is_rejected():
    client = OpenAISynthesisClient(
        client=FakeOpenAI()
    )

    prompt = SynthesisPrompt(
        system_message="   ",
        user_message="data",
    )

    with pytest.raises(
        ValueError,
        match="system_message cannot be empty",
    ):
        client.generate(
            prompt
        )


def test_empty_user_message_is_rejected():
    client = OpenAISynthesisClient(
        client=FakeOpenAI()
    )

    prompt = SynthesisPrompt(
        system_message="instructions",
        user_message="   ",
    )

    with pytest.raises(
        ValueError,
        match="user_message cannot be empty",
    ):
        client.generate(
            prompt
        )


def test_empty_model_output_is_rejected():
    client = OpenAISynthesisClient(
        client=FakeOpenAI(
            output_text="   "
        )
    )

    with pytest.raises(
        RuntimeError,
        match="empty output_text",
    ):
        client.generate(
            _prompt()
        )


def test_non_string_model_output_is_rejected():
    client = OpenAISynthesisClient(
        client=FakeOpenAI(
            output_text=None
        )
    )

    with pytest.raises(
        TypeError,
        match="string output_text",
    ):
        client.generate(
            _prompt()
        )
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
        outcomes,
    ):
        if not isinstance(
            outcomes,
            tuple,
        ):
            outcomes = (
                outcomes,
            )

        self.outcomes = outcomes
        self.calls = []

    def create(
        self,
        **kwargs,
    ):
        self.calls.append(
            kwargs
        )

        index = min(
            len(self.calls) - 1,
            len(self.outcomes) - 1,
        )

        outcome = self.outcomes[
            index
        ]

        if isinstance(
            outcome,
            BaseException,
        ):
            raise outcome

        return SimpleNamespace(
            output_text=outcome
        )


class FakeOpenAI:
    def __init__(
        self,
        outcomes=(
            '{"schema_version":"1.0",'
            '"title":"Test",'
            '"claims":[],'
            '"limitations":[]}'
        ),
    ):
        self.responses = FakeResponses(
            outcomes
        )


class FakeAPIConnectionError(
    Exception,
):
    pass


class FakeAPITimeoutError(
    FakeAPIConnectionError,
):
    pass


class FakeAPIStatusError(
    Exception,
):
    def __init__(
        self,
        status_code,
    ):
        super().__init__(
            f"HTTP {status_code}"
        )

        self.status_code = (
            status_code
        )


class FakeRateLimitError(
    FakeAPIStatusError,
):
    pass


def _patch_provider_errors(
    monkeypatch,
):
    monkeypatch.setattr(
        "equitylens.synthesis_llm."
        "APIConnectionError",
        FakeAPIConnectionError,
    )

    monkeypatch.setattr(
        "equitylens.synthesis_llm."
        "APITimeoutError",
        FakeAPITimeoutError,
    )

    monkeypatch.setattr(
        "equitylens.synthesis_llm."
        "APIStatusError",
        FakeAPIStatusError,
    )

    monkeypatch.setattr(
        "equitylens.synthesis_llm."
        "RateLimitError",
        FakeRateLimitError,
    )


def _valid_response():
    return (
        '{"schema_version":"1.0",'
        '"title":"Test",'
        '"claims":[],'
        '"limitations":[]}'
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


def test_default_openai_client_disables_sdk_retries(
    monkeypatch,
):
    captured = {}

    def fake_openai(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return FakeOpenAI()

    monkeypatch.setattr(
        "equitylens.synthesis_llm.OpenAI",
        fake_openai,
    )

    OpenAISynthesisClient()

    assert (
        captured["max_retries"]
        == 0
    )

    assert (
        captured["timeout"]
        == 60.0
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

    assert (
        result.provider_attempts
        == 1
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


def test_connection_error_retries_then_succeeds(
    monkeypatch,
):
    _patch_provider_errors(
        monkeypatch
    )

    sleeps = []

    fake_client = FakeOpenAI(
        outcomes=(
            FakeAPIConnectionError(
                "connection failed"
            ),
            _valid_response(),
        )
    )

    client = OpenAISynthesisClient(
        client=fake_client,
        sleep_fn=sleeps.append,
    )

    result = client.generate(
        _prompt()
    )

    assert (
        result.provider_attempts
        == 2
    )

    assert len(
        fake_client.responses.calls
    ) == 2

    assert sleeps == [
        0.5,
    ]


def test_timeout_retries_then_succeeds(
    monkeypatch,
):
    _patch_provider_errors(
        monkeypatch
    )

    fake_client = FakeOpenAI(
        outcomes=(
            FakeAPITimeoutError(
                "request timed out"
            ),
            _valid_response(),
        )
    )

    client = OpenAISynthesisClient(
        client=fake_client,
        sleep_fn=lambda _: None,
    )

    result = client.generate(
        _prompt()
    )

    assert (
        result.provider_attempts
        == 2
    )


def test_rate_limit_retries_then_succeeds(
    monkeypatch,
):
    _patch_provider_errors(
        monkeypatch
    )

    fake_client = FakeOpenAI(
        outcomes=(
            FakeRateLimitError(
                429
            ),
            _valid_response(),
        )
    )

    client = OpenAISynthesisClient(
        client=fake_client,
        sleep_fn=lambda _: None,
    )

    result = client.generate(
        _prompt()
    )

    assert (
        result.provider_attempts
        == 2
    )


def test_server_error_retries_then_succeeds(
    monkeypatch,
):
    _patch_provider_errors(
        monkeypatch
    )

    fake_client = FakeOpenAI(
        outcomes=(
            FakeAPIStatusError(
                503
            ),
            _valid_response(),
        )
    )

    client = OpenAISynthesisClient(
        client=fake_client,
        sleep_fn=lambda _: None,
    )

    result = client.generate(
        _prompt()
    )

    assert (
        result.provider_attempts
        == 2
    )


def test_non_retryable_status_error_stops_immediately(
    monkeypatch,
):
    _patch_provider_errors(
        monkeypatch
    )

    fake_client = FakeOpenAI(
        outcomes=FakeAPIStatusError(
            401
        )
    )

    client = OpenAISynthesisClient(
        client=fake_client,
        sleep_fn=lambda _: None,
    )

    with pytest.raises(
        FakeAPIStatusError,
    ):
        client.generate(
            _prompt()
        )

    assert len(
        fake_client.responses.calls
    ) == 1


def test_retryable_error_is_raised_after_attempts_exhausted(
    monkeypatch,
):
    _patch_provider_errors(
        monkeypatch
    )

    fake_client = FakeOpenAI(
        outcomes=FakeAPIStatusError(
            500
        )
    )

    client = OpenAISynthesisClient(
        client=fake_client,
        provider_max_attempts=3,
        provider_retry_delay_seconds=0,
        sleep_fn=lambda _: None,
    )

    with pytest.raises(
        FakeAPIStatusError,
    ):
        client.generate(
            _prompt()
        )

    assert len(
        fake_client.responses.calls
    ) == 3


def test_provider_backoff_is_exponential(
    monkeypatch,
):
    _patch_provider_errors(
        monkeypatch
    )

    sleeps = []

    fake_client = FakeOpenAI(
        outcomes=(
            FakeAPIStatusError(
                500
            ),
            FakeAPIStatusError(
                503
            ),
            _valid_response(),
        )
    )

    client = OpenAISynthesisClient(
        client=fake_client,
        provider_max_attempts=3,
        sleep_fn=sleeps.append,
    )

    result = client.generate(
        _prompt()
    )

    assert (
        result.provider_attempts
        == 3
    )

    assert sleeps == [
        0.5,
        1.0,
    ]


def test_empty_model_is_rejected():
    with pytest.raises(
        ValueError,
        match="model cannot be empty",
    ):
        OpenAISynthesisClient(
            model="   ",
            client=FakeOpenAI(),
        )


def test_provider_max_attempts_below_one_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "provider_max_attempts "
            "must be at least 1"
        ),
    ):
        OpenAISynthesisClient(
            client=FakeOpenAI(),
            provider_max_attempts=0,
        )


def test_negative_provider_retry_delay_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "provider_retry_delay_seconds "
            "cannot be negative"
        ),
    ):
        OpenAISynthesisClient(
            client=FakeOpenAI(),
            provider_retry_delay_seconds=-1,
        )


def test_non_positive_provider_timeout_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "provider_timeout_seconds "
            "must be greater than 0"
        ),
    ):
        OpenAISynthesisClient(
            client=FakeOpenAI(),
            provider_timeout_seconds=0,
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
            outcomes="   "
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
            outcomes=None
        )
    )

    with pytest.raises(
        TypeError,
        match="string output_text",
    ):
        client.generate(
            _prompt()
        )
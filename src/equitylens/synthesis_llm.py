import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from equitylens.synthesis_prompt import SynthesisPrompt

DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT = "low"

DEFAULT_PROVIDER_MAX_ATTEMPTS = 2
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 60.0
DEFAULT_PROVIDER_RETRY_DELAY_SECONDS = 0.5
MAX_PROVIDER_RETRY_DELAY_SECONDS = 4.0

RETRYABLE_STATUS_CODES = {
    408,
    409,
    429,
}

CLAIM_TYPES = (
    "financial_observation",
    "management_explanation",
    "consistency_observation",
    "guidance_update",
)


def _claim_schema(
    claim_type: str,
    target_period_schema: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "claim_id": {
                "type": "string",
            },
            "claim_type": {
                "type": "string",
                "enum": [
                    claim_type,
                ],
            },
            "text": {
                "type": "string",
            },
            "metric_id": {
                "type": "string",
            },
            "target_period": target_period_schema,
            "source_fact_ids": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
            "evidence_sentence_ids": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
        },
        "required": [
            "claim_id",
            "claim_type",
            "text",
            "metric_id",
            "target_period",
            "source_fact_ids",
            "evidence_sentence_ids",
        ],
    }


SYNTHESIS_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "schema_version": {
            "type": "string",
        },
        "title": {
            "type": "string",
        },
        "claims": {
            "type": "array",
            "items": {
                "anyOf": [
                    _claim_schema(
                        "financial_observation",
                        {
                            "type": "null",
                        },
                    ),
                    _claim_schema(
                        "management_explanation",
                        {
                            "type": "null",
                        },
                    ),
                    _claim_schema(
                        "consistency_observation",
                        {
                            "type": "null",
                        },
                    ),
                    _claim_schema(
                        "guidance_update",
                        {
                            "type": "string",
                        },
                    ),
                ],
            },
        },
        "limitations": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "schema_version",
        "title",
        "claims",
        "limitations",
    ],
}


@dataclass(frozen=True)
class SynthesisLLMResponse:
    raw_text: str
    model: str
    provider_attempts: int = 1


def _is_retryable_provider_error(
    error: Exception,
) -> bool:
    if isinstance(
        error,
        (
            APITimeoutError,
            APIConnectionError,
            RateLimitError,
        ),
    ):
        return True

    if isinstance(
        error,
        APIStatusError,
    ):
        status_code = error.status_code

        return (
            status_code in RETRYABLE_STATUS_CODES
            or status_code >= 500
        )

    return False


def _provider_retry_delay(
    failed_attempt: int,
    base_delay_seconds: float,
) -> float:
    delay = (
        base_delay_seconds
        * (2 ** (failed_attempt - 1))
    )

    return min(
        delay,
        MAX_PROVIDER_RETRY_DELAY_SECONDS,
    )


class OpenAISynthesisClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        client: Any | None = None,
        provider_max_attempts: int = DEFAULT_PROVIDER_MAX_ATTEMPTS,
        provider_retry_delay_seconds: float = DEFAULT_PROVIDER_RETRY_DELAY_SECONDS,
        provider_timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        if not model.strip():
            raise ValueError(
                "model cannot be empty."
            )

        if provider_max_attempts < 1:
            raise ValueError(
                "provider_max_attempts must be at least 1."
            )

        if provider_retry_delay_seconds < 0:
            raise ValueError(
                "provider_retry_delay_seconds cannot be negative."
            )

        if provider_timeout_seconds <= 0:
            raise ValueError(
                "provider_timeout_seconds must be greater than 0."
            )

        self._model = model.strip()
        self._provider_max_attempts = (
            provider_max_attempts
        )
        self._provider_retry_delay_seconds = (
            provider_retry_delay_seconds
        )
        self._sleep_fn = sleep_fn

        self._client = (
            client
            if client is not None
            else OpenAI(
                max_retries=0,
                timeout=provider_timeout_seconds,
            )
        )

    @property
    def model(
        self,
    ) -> str:
        return self._model

    def _create_response(
        self,
        prompt: SynthesisPrompt,
    ):
        return self._client.responses.create(
            model=self._model,
            reasoning={
                "effort": (
                    DEFAULT_REASONING_EFFORT
                ),
            },
            instructions=(
                prompt.system_message
            ),
            input=prompt.user_message,
            text={
                "format": {
                    "type": "json_schema",
                    "name": (
                        "equitylens_synthesis"
                    ),
                    "strict": True,
                    "schema": (
                        SYNTHESIS_JSON_SCHEMA
                    ),
                },
            },
        )

    def generate(
        self,
        prompt: SynthesisPrompt,
    ) -> SynthesisLLMResponse:
        if not prompt.system_message.strip():
            raise ValueError(
                "system_message cannot be empty."
            )

        if not prompt.user_message.strip():
            raise ValueError(
                "user_message cannot be empty."
            )

        response = None
        provider_attempts = 0

        for attempt in range(
            1,
            self._provider_max_attempts + 1,
        ):
            provider_attempts = attempt

            try:
                response = self._create_response(
                    prompt
                )
            except (
                APIConnectionError,
                APIStatusError,
            ) as error:
                retryable = (
                    _is_retryable_provider_error(
                        error
                    )
                )

                if (
                    not retryable
                    or attempt
                    >= self._provider_max_attempts
                ):
                    raise

                delay = _provider_retry_delay(
                    failed_attempt=attempt,
                    base_delay_seconds=(
                        self._provider_retry_delay_seconds
                    ),
                )

                self._sleep_fn(
                    delay
                )

                continue

            break

        if response is None:
            raise RuntimeError(
                "Provider retry loop completed "
                "without a response or exception."
            )

        raw_text = response.output_text

        if not isinstance(
            raw_text,
            str,
        ):
            raise TypeError(
                "OpenAI response did not contain "
                "string output_text."
            )

        raw_text = raw_text.strip()

        if not raw_text:
            raise RuntimeError(
                "OpenAI response contained empty "
                "output_text."
            )

        return SynthesisLLMResponse(
            raw_text=raw_text,
            model=self._model,
            provider_attempts=provider_attempts,
        )
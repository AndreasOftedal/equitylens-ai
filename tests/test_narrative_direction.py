import pytest

from equitylens.narrative_direction import (
    detect_narrative_direction,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        (
            (
                "Net operating income increased "
                "compared to the prior quarter."
            ),
            "increase",
        ),
        (
            (
                "Net operating income decreased "
                "compared to the prior quarter."
            ),
            "decrease",
        ),
        (
            (
                "Adjusted operating income remained "
                "at a similar level compared to the "
                "prior quarter."
            ),
            "unchanged",
        ),
        (
            (
                "Adjusted operating income remained "
                "broadly stable compared with the "
                "previous quarter."
            ),
            "unchanged",
        ),
    ),
)
def test_detects_basic_outcome_direction(
    text,
    expected,
):
    assert (
        detect_narrative_direction(
            text
        )
        == expected
    )


def test_driver_direction_does_not_override_outcome():
    text = (
        "Cash flow decreased compared to the "
        "prior quarter due to higher tax payments."
    )

    assert (
        detect_narrative_direction(
            text
        )
        == "decrease"
    )


def test_negative_driver_does_not_override_increase():
    text = (
        "Net operating income increased compared "
        "to the prior quarter due to lower costs."
    )

    assert (
        detect_narrative_direction(
            text
        )
        == "increase"
    )


def test_cause_first_sentence_detects_outcome():
    text = (
        "Higher realised prices led to increased "
        "net operating income."
    )

    assert (
        detect_narrative_direction(
            text
        )
        == "increase"
    )


def test_generated_sentence_detects_outcome():
    text = (
        "Higher production generated increased "
        "cash flow."
    )

    assert (
        detect_narrative_direction(
            text
        )
        == "increase"
    )


def test_mixed_outcome_is_not_forced_into_one_direction():
    text = (
        "Operating performance increased in some "
        "areas but decreased in others."
    )

    assert (
        detect_narrative_direction(
            text
        )
        == "mixed"
    )


def test_sentence_without_direction_is_unknown():
    assert (
        detect_narrative_direction(
            "Management discussed market conditions."
        )
        == "unknown"
    )


def test_empty_text_is_unknown():
    assert (
        detect_narrative_direction(
            "   "
        )
        == "unknown"
    )
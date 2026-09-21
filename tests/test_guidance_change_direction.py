from equitylens.synthesis_semantics import (
    _detect_guidance_change_direction,
)


def test_unchanged_growth_guidance_is_not_mixed():
    text = (
        "FY2026 oil and gas production growth guidance "
        "remained unchanged at around 3% compared with 2025."
    )

    assert (
        _detect_guidance_change_direction(text)
        == "unchanged"
    )


def test_unchanged_guidance_with_growth_word_is_unchanged():
    text = (
        "Oil and gas production guidance remained unchanged "
        "at around 3% growth for FY2026."
    )

    assert (
        _detect_guidance_change_direction(text)
        == "unchanged"
    )


def test_unchanged_ambition_is_detected():
    text = (
        "The ambition for unit production cost position "
        "was unchanged at the top quartile of the peer group."
    )

    assert (
        _detect_guidance_change_direction(text)
        == "unchanged"
    )


def test_increased_guidance_is_detected():
    text = (
        "FY2026 share buyback guidance increased "
        "from USD 1.5 billion to USD 3 billion."
    )

    assert (
        _detect_guidance_change_direction(text)
        == "increase"
    )


def test_decreased_guidance_is_detected():
    text = (
        "FY2026 capital expenditure guidance decreased "
        "from USD 15 billion to USD 13 billion."
    )

    assert (
        _detect_guidance_change_direction(text)
        == "decrease"
    )


def test_conflicting_guidance_change_language_is_mixed():
    text = (
        "FY2026 guidance increased but remained unchanged."
    )

    assert (
        _detect_guidance_change_direction(text)
        == "mixed"
    )


def test_underlying_growth_without_guidance_change_is_unknown():
    text = (
        "Oil and gas production is estimated to grow "
        "around 3% compared with 2025."
    )

    assert (
        _detect_guidance_change_direction(text)
        == "unknown"
    )
import pytest

from equitylens.parser import ParsedPage
from equitylens.text_chunks import (
    chunk_page,
    chunk_pages,
)


def test_short_page_produces_single_chunk():
    page = ParsedPage(
        document_id="report",
        page_number=3,
        text="Management reported stronger operating performance.",
    )

    chunks = chunk_page(
        page=page,
        max_chars=100,
        overlap_chars=20,
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.document_id == "report"
    assert chunk.page_number == 3
    assert chunk.chunk_index == 0
    assert chunk.text == page.text


def test_long_page_produces_multiple_chunks():
    page = ParsedPage(
        document_id="report",
        page_number=4,
        text=" ".join(
            f"word-{index}"
            for index in range(100)
        ),
    )

    chunks = chunk_page(
        page=page,
        max_chars=120,
        overlap_chars=20,
    )

    assert len(chunks) > 1

    assert all(
        chunk.document_id == "report"
        for chunk in chunks
    )

    assert all(
        chunk.page_number == 4
        for chunk in chunks
    )


def test_chunks_preserve_exact_character_provenance():
    page = ParsedPage(
        document_id="report",
        page_number=7,
        text=" ".join(
            f"sentence-{index}"
            for index in range(80)
        ),
    )

    chunks = chunk_page(
        page=page,
        max_chars=150,
        overlap_chars=30,
    )

    for chunk in chunks:
        assert page.text[
            chunk.start_char:chunk.end_char
        ] == chunk.text


def test_chunk_ids_are_deterministic():
    page = ParsedPage(
        document_id="report",
        page_number=2,
        text="A deterministic chunk identifier should be reproducible.",
    )

    first = chunk_page(
        page=page,
        max_chars=100,
        overlap_chars=10,
    )

    second = chunk_page(
        page=page,
        max_chars=100,
        overlap_chars=10,
    )

    assert first[0].chunk_id == second[0].chunk_id


def test_changed_text_changes_chunk_id():
    original = ParsedPage(
        document_id="report",
        page_number=2,
        text="Original management commentary.",
    )

    changed = ParsedPage(
        document_id="report",
        page_number=2,
        text="Changed management commentary.",
    )

    original_chunk = chunk_page(
        page=original,
        max_chars=100,
        overlap_chars=10,
    )[0]

    changed_chunk = chunk_page(
        page=changed,
        max_chars=100,
        overlap_chars=10,
    )[0]

    assert original_chunk.chunk_id != changed_chunk.chunk_id


def test_empty_page_produces_no_chunks():
    page = ParsedPage(
        document_id="report",
        page_number=5,
        text="   ",
    )

    assert chunk_page(page) == ()


def test_chunk_pages_preserves_page_provenance():
    pages = [
        ParsedPage(
            document_id="report",
            page_number=1,
            text="First page narrative.",
        ),
        ParsedPage(
            document_id="report",
            page_number=2,
            text="Second page narrative.",
        ),
    ]

    chunks = chunk_pages(
        pages=pages,
        max_chars=100,
        overlap_chars=10,
    )

    assert len(chunks) == 2

    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2


def test_all_chunks_on_page_receive_same_section_context():
    page = ParsedPage(
        document_id="report",
        page_number=16,
        text=(
            "Marketing, Midstream & Processing\n"
            "Volumes, pricing and revenues\n"
            + " ".join(
                f"word-{index}"
                for index in range(150)
            )
        ),
    )

    chunks = chunk_page(
        page=page,
        max_chars=120,
        overlap_chars=20,
    )

    assert len(chunks) > 1

    assert all(
        chunk.section_context
        == chunks[0].section_context
        for chunk in chunks
    )

    assert (
        "Marketing, Midstream & Processing"
        in chunks[0].section_context
    )


def test_section_context_is_compact_and_normalized():
    page = ParsedPage(
        document_id="report",
        page_number=8,
        text=(
            "Group review\n\n"
            "Operations and financial results\n"
            "Strong production supported results."
        ),
    )

    chunk = chunk_page(page)[0]

    assert chunk.section_context == (
        "Group review Operations and financial results "
        "Strong production supported results."
    )


def test_invalid_chunk_settings_are_rejected():
    page = ParsedPage(
        document_id="report",
        page_number=1,
        text="Some text.",
    )

    with pytest.raises(
        ValueError,
        match="max_chars must be greater than zero",
    ):
        chunk_page(
            page=page,
            max_chars=0,
        )

    with pytest.raises(
        ValueError,
        match="overlap_chars cannot be negative",
    ):
        chunk_page(
            page=page,
            overlap_chars=-1,
        )

    with pytest.raises(
        ValueError,
        match="overlap_chars must be smaller than max_chars",
    ):
        chunk_page(
            page=page,
            max_chars=100,
            overlap_chars=100,
        )
from equitylens.evidence_sentences import (
    split_chunk_into_sentences,
)
from equitylens.text_chunks import TextChunk


def _chunk(
    text: str,
    start_char: int = 100,
) -> TextChunk:
    return TextChunk(
        chunk_id="chunk-1",
        document_id="report",
        page_number=16,
        chunk_index=1,
        text=text,
        start_char=start_char,
        end_char=start_char + len(text),
        section_context=(
            "Marketing, Midstream & Processing "
            "Volumes, pricing and revenues"
        ),
    )


def test_single_sentence_produces_single_evidence_sentence():
    chunk = _chunk(
        "Production increased during the quarter."
    )

    sentences = split_chunk_into_sentences(
        chunk
    )

    assert len(sentences) == 1
    assert sentences[0].text == chunk.text


def test_multiple_sentences_are_split():
    chunk = _chunk(
        
            "Gas sales declined from the previous quarter. "
            "Prices increased compared with the same quarter last year."
        
    )

    sentences = split_chunk_into_sentences(
        chunk
    )

    assert len(sentences) == 2

    assert sentences[0].text == (
        "Gas sales declined from the previous quarter."
    )

    assert sentences[1].text == (
        "Prices increased compared with the same quarter last year."
    )


def test_sentence_provenance_matches_chunk_text():
    chunk = _chunk(
        
            "First sentence. "
            "Second sentence."
        
    )

    sentences = split_chunk_into_sentences(
        chunk
    )

    for sentence in sentences:
        assert chunk.text[
            sentence.chunk_start_char:
            sentence.chunk_end_char
        ] == sentence.text


def test_page_offsets_include_chunk_offset():
    chunk = _chunk(
        text=(
            "First sentence. "
            "Second sentence."
        ),
        start_char=250,
    )

    sentences = split_chunk_into_sentences(
        chunk
    )

    for sentence in sentences:
        assert sentence.page_start_char == (
            250
            + sentence.chunk_start_char
        )

        assert sentence.page_end_char == (
            250
            + sentence.chunk_end_char
        )


def test_sentence_ids_are_deterministic():
    chunk = _chunk(
        
            "First sentence. "
            "Second sentence."
        
    )

    first = split_chunk_into_sentences(
        chunk
    )

    second = split_chunk_into_sentences(
        chunk
    )

    assert tuple(
        sentence.sentence_id
        for sentence in first
    ) == tuple(
        sentence.sentence_id
        for sentence in second
    )


def test_sentence_keeps_source_metadata():
    chunk = _chunk(
        "Results improved."
    )

    sentence = split_chunk_into_sentences(
        chunk
    )[0]

    assert sentence.chunk_id == "chunk-1"
    assert sentence.document_id == "report"
    assert sentence.page_number == 16

    assert sentence.section_context == (
        "Marketing, Midstream & Processing "
        "Volumes, pricing and revenues"
    )


def test_empty_chunk_produces_no_sentences():
    chunk = _chunk("   ")

    assert (
        split_chunk_into_sentences(
            chunk
        )
        == ()
    )


def test_qoq_and_yoy_statements_are_separated():
    chunk = _chunk(
        
            "Gas sales volumes decreased compared to the previous quarter "
            "due to seasonal maintenance. "
            "The realised gas price increased compared to the same quarter "
            "last year due to higher market prices."
        
    )

    sentences = split_chunk_into_sentences(
        chunk
    )

    assert len(sentences) == 2

    assert "previous quarter" in (
        sentences[0].text
    )

    assert "same quarter last year" in (
        sentences[1].text
    )


def test_table_prefix_is_separated_from_following_narrative():
    chunk = _chunk(
        
            "Cash flow\n"
            "Q2 2026\n"
            "Q1 2026\n"
            "Q2 2025\n"
            "Cash flow from operations\n"
            "3 123\n"
            "2 013\n"
            "1 240\n"
            "Cash and cash equivalents\n"
            "2 492\n"
            "1 862\n"
            "2 745\n"
            "Net cash flow from operating activities was USD 3,123 "
            "(2,013) million in the quarter, primarily reflecting "
            "higher income in the quarter and changes in working "
            "capital, partly offset by higher tax payments."
        
    )

    sentences = split_chunk_into_sentences(
        chunk
    )

    assert len(sentences) == 2

    assert sentences[0].text.startswith(
        "Cash flow"
    )

    assert sentences[1].text.startswith(
        "Net cash flow from operating activities"
    )

    assert (
        "primarily reflecting higher income"
        in sentences[1].text
    )

    for sentence in sentences:
        assert chunk.text[
            sentence.chunk_start_char:
            sentence.chunk_end_char
        ] == sentence.text
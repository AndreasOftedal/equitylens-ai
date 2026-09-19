from equitylens.source_manifest import EQUINOR_SOURCES


def test_equinor_source_manifest_is_complete():
    assert len(EQUINOR_SOURCES) == 2

    document_ids = {
        source.document_id
        for source in EQUINOR_SOURCES
    }

    assert document_ids == {
        "equinor-q1-2026-financial-statements-and-review",
        "equinor-q2-2026-financial-statements-and-review",
    }


def test_equinor_sources_have_valid_sha256_fingerprints():
    for source in EQUINOR_SOURCES:
        assert len(source.sha256) == 64
        assert all(
            character in "0123456789abcdef"
            for character in source.sha256
        )
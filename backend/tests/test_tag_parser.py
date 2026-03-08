"""Unit tests for tag_parser.extract_raw_tags().

These test the pure text extraction logic only — no DB calls needed.
resolve_tags() (which does DB lookup) is covered by integration tests.
"""
import pytest

from app.utils.tag_parser import extract_raw_tags, ParsedTag


def test_extracts_single_tag():
    result = extract_raw_tags("This project is #escalated today.")
    assert len(result) == 1
    assert result[0].name == "escalated"
    assert result[0].raw == "#escalated"


def test_extracts_multiple_tags():
    result = extract_raw_tags("Project has #escalated issues and #churnrisk.")
    names = {r.name for r in result}
    assert names == {"escalated", "churnrisk"}


def test_normalizes_to_lowercase():
    result = extract_raw_tags("Customer is #Frustrated and showing #ChurnRisk.")
    names = {r.name for r in result}
    assert names == {"frustrated", "churnrisk"}


def test_no_tags_returns_empty():
    result = extract_raw_tags("No hashtags here at all.")
    assert result == []


def test_empty_string_returns_empty():
    result = extract_raw_tags("")
    assert result == []


def test_duplicate_tags_kept():
    """extract_raw_tags keeps duplicates — dedup happens in process_tags."""
    result = extract_raw_tags("#escalated and #escalated again.")
    assert len(result) == 2
    assert all(r.name == "escalated" for r in result)


def test_ignores_hash_only():
    """A bare '#' with no following word should not produce a tag."""
    result = extract_raw_tags("Price is $100 and # alone.")
    assert result == []


def test_ignores_mid_word_hash():
    """A hash embedded inside a word (no preceding whitespace/boundary) should not match."""
    result = extract_raw_tags("abc#notag should not match.")
    assert result == []


def test_tag_at_start_of_text():
    result = extract_raw_tags("#goodprogress on this project!")
    assert len(result) == 1
    assert result[0].name == "goodprogress"


def test_tag_at_end_of_text():
    result = extract_raw_tags("Everything is on track #customerhappy")
    assert len(result) == 1
    assert result[0].name == "customerhappy"


def test_tag_with_numbers():
    """Tag names can contain numbers after the first letter."""
    result = extract_raw_tags("See ticket #jira123 for details.")
    assert len(result) == 1
    assert result[0].name == "jira123"


def test_tag_with_underscore():
    """Tag names can contain underscores."""
    result = extract_raw_tags("Tagged as #feature_request.")
    assert len(result) == 1
    assert result[0].name == "feature_request"


def test_all_builtin_tags_extractable():
    """Regression: all 11 built-in tag names must be parseable."""
    builtin_tags = [
        "escalated", "blockedbycustomer", "atrisk",
        "customerenhancement", "featurerequest", "productsignal",
        "customerhappy", "goodprogress", "frustrated", "churnrisk", "slowadoption",
    ]
    text = " ".join(f"#{t}" for t in builtin_tags)
    result = extract_raw_tags(text)
    extracted_names = {r.name for r in result}
    assert extracted_names == set(builtin_tags)

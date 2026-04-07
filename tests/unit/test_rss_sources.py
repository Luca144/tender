"""Unit tests for RSS sources connector."""

from unittest.mock import patch, MagicMock

from src.rss_sources import (
    fetch_dtvp,
    fetch_vergabe_nrw,
    fetch_bund,
    fetch_rss_sources,
    _make_id,
)


def _mock_feed(title="Test Feed", entries=None):
    """Create a mock feedparser result."""
    if entries is None:
        entries = [
            MagicMock(
                get=lambda k, d="": {
                    "title": "Test Ausschreibung",
                    "link": "https://example.com/tender/1",
                    "published": "2024-11-15",
                }.get(k, d),
                **{
                    "title": "Test Ausschreibung",
                    "link": "https://example.com/tender/1",
                    "published": "2024-11-15",
                },
            )
        ]
    feed = MagicMock()
    feed.entries = entries
    feed.feed.get.return_value = title
    feed.feed.title = title
    return feed


@patch("src.rss_sources.feedparser.parse")
def test_each_feed_returns_list(mock_parse):
    """Each fetch function returns a list of dicts."""
    mock_parse.return_value = _mock_feed("DTVP")

    result = fetch_dtvp()
    assert isinstance(result, list)
    assert len(result) > 0

    result = fetch_vergabe_nrw()
    assert isinstance(result, list)

    result = fetch_bund()
    assert isinstance(result, list)


@patch("src.rss_sources.feedparser.parse")
def test_failed_feed_doesnt_crash(mock_parse):
    """A failed feed returns empty list without crashing others."""
    mock_parse.side_effect = Exception("Network error")

    result = fetch_dtvp()
    assert result == []

    result = fetch_vergabe_nrw()
    assert result == []

    result = fetch_bund()
    assert result == []


@patch("src.rss_sources.feedparser.parse")
def test_output_format(mock_parse):
    """All required fields are present in output."""
    mock_parse.return_value = _mock_feed("Test Source")

    result = fetch_dtvp()
    assert len(result) > 0

    entry = result[0]
    required_fields = {"id", "title", "buyer", "published", "deadline", "url", "source"}
    assert required_fields.issubset(entry.keys())


def test_id_is_consistent():
    """Same URL produces the same ID."""
    url = "https://example.com/tender/42"
    id1 = _make_id(url)
    id2 = _make_id(url)
    assert id1 == id2
    assert isinstance(id1, str)
    assert len(id1) == 32  # MD5 hex digest

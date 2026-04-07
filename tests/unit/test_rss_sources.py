"""Unit tests for tender source connectors (Bund.de RSS, tender24.de scraping)."""

from unittest.mock import patch, MagicMock

from src.rss_sources import (
    fetch_bund,
    fetch_tender24,
    fetch_rss_sources,
    _make_id,
)


def _mock_bund_feed():
    """Create a mock feedparser result for service.bund.de."""
    entry = MagicMock()
    entry.get = lambda k, d="": {
        "title": "IT-Beratung Energiesektor",
        "link": "https://www.service.bund.de/IMPORTE/Ausschreibungen/12345.html",
        "published": "Mon, 7 Apr 2025 10:00:00 +0200",
        "description": (
            'Vergabestelle: <strong>Stadtwerke Test</strong><br />'
            'Angebotsfrist: <strong>30.04.2025 12:00</strong>'
        ),
    }.get(k, d)
    feed = MagicMock()
    feed.entries = [entry]
    feed.feed.get.return_value = "service.bund.de"
    return feed


MOCK_TENDER24_HTML = """
<html><body>
<table>
<thead><tr><th>Datum</th></tr></thead>
<tr class="tableRow clickable-row publicationDetail" data-oid="abc-123" data-category="InvitationToTender">
  <td>07.04.2025</td>
  <td class="tender">Software-Entwicklung Netzsteuerung</td>
  <td class="tenderAuthority">Max-Planck-Institut</td>
  <td class="tenderType">Offenes Verfahren</td>
  <td class="tenderType">VgV</td>
  <td class="tenderDeadline">30.04.2025</td>
</tr>
<tr class="tableRow clickable-row publicationDetail" data-oid="def-456" data-category="InvitationToTender">
  <td>06.04.2025</td>
  <td class="tender">IT-Beratung Energiewende</td>
  <td class="tenderAuthority">Bundesnetzagentur</td>
  <td class="tenderType">Offenes Verfahren</td>
  <td class="tenderType">VgV</td>
  <td class="tenderDeadline">28.04.2025</td>
</tr>
</table>
</body></html>
"""


@patch("src.rss_sources.feedparser.parse")
def test_bund_returns_list(mock_parse):
    """fetch_bund() returns a list of dicts on success."""
    mock_parse.return_value = _mock_bund_feed()

    result = fetch_bund()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["source"] == "Bund.de"
    assert result[0]["title"] == "IT-Beratung Energiesektor"


@patch("src.rss_sources.feedparser.parse")
def test_bund_extracts_buyer_and_deadline(mock_parse):
    """Buyer and deadline are extracted from RSS description."""
    mock_parse.return_value = _mock_bund_feed()

    result = fetch_bund()
    assert result[0]["buyer"] == "Stadtwerke Test"
    assert result[0]["deadline"] == "30.04.2025 12:00"


@patch("src.rss_sources.requests.get")
def test_tender24_returns_list(mock_get):
    """fetch_tender24() returns a list of dicts on success."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_TENDER24_HTML
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    result = fetch_tender24()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["source"] == "tender24.de"
    assert result[0]["title"] == "Software-Entwicklung Netzsteuerung"
    assert result[0]["buyer"] == "Max-Planck-Institut"


@patch("src.rss_sources.feedparser.parse")
def test_failed_bund_doesnt_crash(mock_parse):
    """A failed Bund.de feed returns empty list."""
    mock_parse.side_effect = Exception("Network error")

    result = fetch_bund()
    assert result == []


@patch("src.rss_sources.requests.get")
def test_failed_tender24_doesnt_crash(mock_get):
    """A failed tender24.de scrape returns empty list."""
    mock_get.side_effect = Exception("Network error")

    result = fetch_tender24()
    assert result == []


@patch("src.rss_sources.feedparser.parse")
def test_bund_output_format(mock_parse):
    """All required fields are present in Bund.de output."""
    mock_parse.return_value = _mock_bund_feed()

    result = fetch_bund()
    assert len(result) > 0
    required_fields = {"id", "title", "buyer", "published", "deadline", "url", "source"}
    assert required_fields.issubset(result[0].keys())


@patch("src.rss_sources.requests.get")
def test_tender24_output_format(mock_get):
    """All required fields are present in tender24.de output."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_TENDER24_HTML
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    result = fetch_tender24()
    assert len(result) > 0
    required_fields = {"id", "title", "buyer", "published", "deadline", "url", "source"}
    assert required_fields.issubset(result[0].keys())


def test_id_is_consistent():
    """Same URL produces the same ID."""
    url = "https://example.com/tender/42"
    id1 = _make_id(url)
    id2 = _make_id(url)
    assert id1 == id2
    assert isinstance(id1, str)
    assert len(id1) == 32  # MD5 hex digest

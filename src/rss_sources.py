"""RSS Feed Connectors for German tender portals.

Fetches tenders from DTVP, Vergabe.NRW, and Bund.de RSS feeds.
Each feed is fetched independently — a failure in one does not affect others.
"""

import hashlib
import logging
from datetime import datetime, timezone

import feedparser

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "DTVP": "https://www.dtvp.de/Center/rss/tender.xml",
    "Vergabe.NRW": "https://www.vergabe.nrw.de/VMPCenter/rss/tender.xml",
    "Bund.de": (
        "https://www.bund.de/SiteGlobals/Functions/RSSFeed/"
        "DE/RSSNewsfeed_Ausschreibungen.xml"
    ),
}


def _make_id(url: str) -> str:
    """Generate a stable ID from a URL using MD5 hash."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def _parse_date(entry) -> str:
    """Extract publication date from a feed entry."""
    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        return raw
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _parse_feed(feed_url: str, source_name: str) -> list[dict]:
    """Parse a single RSS feed and return unified entry dicts."""
    feed = feedparser.parse(feed_url)
    entries = []

    for entry in feed.entries:
        link = entry.get("link", "")
        entries.append({
            "id": _make_id(link),
            "title": entry.get("title", "–"),
            "buyer": feed.feed.get("title", "–") if hasattr(feed, "feed") else "–",
            "published": _parse_date(entry),
            "deadline": "–",
            "url": link,
            "source": source_name,
        })

    return entries


def fetch_dtvp() -> list[dict]:
    """Fetch tenders from DTVP RSS feed."""
    try:
        return _parse_feed(RSS_FEEDS["DTVP"], "DTVP")
    except Exception as e:
        logger.warning("DTVP feed error: %s", e)
        return []


def fetch_vergabe_nrw() -> list[dict]:
    """Fetch tenders from Vergabe.NRW RSS feed."""
    try:
        return _parse_feed(RSS_FEEDS["Vergabe.NRW"], "Vergabe.NRW")
    except Exception as e:
        logger.warning("Vergabe.NRW feed error: %s", e)
        return []


def fetch_bund() -> list[dict]:
    """Fetch tenders from Bund.de RSS feed."""
    try:
        return _parse_feed(RSS_FEEDS["Bund.de"], "Bund.de")
    except Exception as e:
        logger.warning("Bund.de feed error: %s", e)
        return []


def fetch_rss_sources() -> list[dict]:
    """Fetch and merge tenders from all RSS sources."""
    results = []
    results.extend(fetch_dtvp())
    results.extend(fetch_vergabe_nrw())
    results.extend(fetch_bund())
    return results

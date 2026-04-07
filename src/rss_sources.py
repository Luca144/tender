"""Connectors for German tender portals.

Fetches tenders from service.bund.de (RSS) and tender24.de (HTML scraping).
Each source is fetched independently — a failure in one does not affect others.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BUND_RSS_URL = (
    "https://www.service.bund.de/Content/Globals/Functions/RSSFeed/"
    "RSSGenerator_Ausschreibungen.xml"
)

TENDER24_URL = (
    "https://www.tender24.de/NetServer/PublicationSearchControllerServlet"
    "?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender"
)


def _make_id(url: str) -> str:
    """Generate a stable ID from a URL using MD5 hash."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def _extract_deadline_from_description(desc: str) -> str:
    """Extract Angebotsfrist from service.bund.de RSS description HTML."""
    match = re.search(r"Angebotsfrist:\s*<strong>\s*([^<]+)", desc)
    if match:
        return match.group(1).strip()
    return "–"


def _extract_buyer_from_description(desc: str) -> str:
    """Extract Vergabestelle from service.bund.de RSS description HTML."""
    match = re.search(r"Vergabestelle:\s*<strong>\s*([^<]+)", desc)
    if match:
        return match.group(1).strip()
    return "–"


def fetch_bund() -> list[dict]:
    """Fetch tenders from service.bund.de RSS feed."""
    try:
        feed = feedparser.parse(BUND_RSS_URL)
        entries = []

        for entry in feed.entries:
            link = entry.get("link", "")
            desc = entry.get("description", "")
            published_raw = entry.get("published") or entry.get("updated") or ""
            if not published_raw:
                published_raw = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            entries.append({
                "id": _make_id(link),
                "title": entry.get("title", "–"),
                "buyer": _extract_buyer_from_description(desc),
                "published": published_raw,
                "deadline": _extract_deadline_from_description(desc),
                "url": link,
                "source": "Bund.de",
            })

        return entries

    except Exception as e:
        logger.warning("service.bund.de feed error: %s", e)
        return []


def fetch_tender24() -> list[dict]:
    """Fetch tenders from tender24.de by scraping HTML search results."""
    try:
        resp = requests.get(
            TENDER24_URL,
            headers={"User-Agent": "Mozilla/5.0 TenderScout/1.0"},
            timeout=20,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("tr.clickable-row")
        entries = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            date_text = cells[0].get_text(strip=True)
            title = cells[1].get_text(strip=True)
            buyer = cells[2].get_text(strip=True)
            deadline_cell = cells[5] if len(cells) > 5 else None
            deadline = deadline_cell.get_text(strip=True) if deadline_cell else "–"

            oid = row.get("data-oid", "")
            url = (
                f"https://www.tender24.de/NetServer/PublicationControllerServlet"
                f"?function=Detail&Publication={oid}"
            ) if oid else ""

            entries.append({
                "id": _make_id(url or title),
                "title": title or "–",
                "buyer": buyer or "–",
                "published": date_text or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "deadline": deadline or "–",
                "url": url,
                "source": "tender24.de",
            })

        return entries

    except requests.exceptions.Timeout:
        logger.warning("tender24.de Timeout")
        return []
    except Exception as e:
        logger.warning("tender24.de scraping error: %s", e)
        return []


def fetch_rss_sources() -> list[dict]:
    """Fetch and merge tenders from all non-TED sources."""
    results = []
    results.extend(fetch_bund())
    results.extend(fetch_tender24())
    return results

"""Connectors for German tender portals.

Fetches tenders from service.bund.de (RSS) and tender24.de (HTML scraping).
Each source is fetched independently — a failure in one does not affect others.
Results are filtered for IT, energy, and consulting relevance.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# service.bund.de RSS with search filter for IT/Energie/Beratung
BUND_RSS_URLS = [
    (
        "https://www.service.bund.de/Content/DE/Ausschreibungen/Suche/Formular.html"
        "?nn=4641482&type=0&resultsPerPage=100&sortOrder=dateOfIssue_dt+desc"
        "&jobsrss=true&searchString=IT+Software"
    ),
    (
        "https://www.service.bund.de/Content/DE/Ausschreibungen/Suche/Formular.html"
        "?nn=4641482&type=0&resultsPerPage=100&sortOrder=dateOfIssue_dt+desc"
        "&jobsrss=true&searchString=Energie+Beratung"
    ),
]

TENDER24_URL = (
    "https://www.tender24.de/NetServer/PublicationSearchControllerServlet"
    "?function=SearchPublications&Gesetzesgrundlage=All&Category=InvitationToTender"
)

# Keywords for relevance filtering (case-insensitive)
RELEVANCE_KEYWORDS = [
    # IT & Software
    "software", "it-", "it ", "informationstechnik", "informationstechnologie",
    "datenbank", "cloud", "server", "netzwerk", "cyber", "digital",
    "programmierung", "entwicklung", "web", "app", "system",
    "rechenzentrum", "sap", "erp", "helpdesk", "support",
    # Energie
    "energie", "strom", "netz", "smart grid", "smart meter",
    "erneuerbar", "photovoltaik", "windkraft", "solar",
    "stadtwerk", "versorgung", "ladesäule", "elektro",
    "wasserstoff", "kraftwerk", "energiewende",
    # Beratung
    "beratung", "consulting", "unternehmensberatung",
    "managementberatung", "strategieberatung", "projektmanagement",
]


def _is_relevant(title: str) -> bool:
    """Check if a tender title matches IT/energy/consulting keywords."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in RELEVANCE_KEYWORDS)


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
    """Fetch IT/energy tenders from service.bund.de RSS feeds."""
    all_entries = []
    seen_links = set()

    for rss_url in BUND_RSS_URLS:
        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                link = entry.get("link", "")
                if link in seen_links:
                    continue
                seen_links.add(link)

                title = entry.get("title", "–")
                desc = entry.get("description", "")
                published_raw = entry.get("published") or entry.get("updated") or ""
                if not published_raw:
                    published_raw = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                all_entries.append({
                    "id": _make_id(link),
                    "title": title,
                    "buyer": _extract_buyer_from_description(desc),
                    "published": published_raw,
                    "deadline": _extract_deadline_from_description(desc),
                    "url": link,
                    "source": "Bund.de",
                })

        except Exception as e:
            logger.warning("service.bund.de feed error: %s", e)

    return all_entries


def fetch_tender24() -> list[dict]:
    """Fetch IT/energy tenders from tender24.de by scraping HTML search results."""
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

            if not _is_relevant(title):
                continue

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

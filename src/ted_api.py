"""TED Search API V3 Connector.

Queries the TED Europa Search API for relevant energy & IT tenders
matching ReqPOOL's filter criteria (CPV, country, legal basis).
"""

import logging
import requests

logger = logging.getLogger(__name__)

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"

SEARCH_BODY = {
    "query": (
        "cpv-code IN (72000000, 79410000) "
        "AND buyer-country = DEU "
        "AND legal-basis-directive = 32014L0025"
    ),
    "fields": [
        "publication-number",
        "notice-title",
        "buyer-name",
        "publication-date",
        "deadline-date",
        "notice-url",
        "cpv-code",
        "contract-nature",
    ],
    "page": 1,
    "limit": 50,
    "sort": [{"field": "publication-date", "order": "desc"}],
}


def _extract_entry(raw: dict) -> dict:
    """Convert a raw TED API result into our unified entry format."""
    title = raw.get("notice-title", "")
    if isinstance(title, dict):
        title = title.get("de") or title.get("en") or next(iter(title.values()), "–")
    if isinstance(title, list):
        title = title[0] if title else "–"

    buyer = raw.get("buyer-name", "–")
    if isinstance(buyer, list):
        buyer = buyer[0] if buyer else "–"
    if isinstance(buyer, dict):
        buyer = buyer.get("de") or buyer.get("en") or next(iter(buyer.values()), "–")

    return {
        "id": str(raw.get("publication-number", "")),
        "title": str(title),
        "buyer": str(buyer),
        "published": str(raw.get("publication-date", "–")),
        "deadline": str(raw.get("deadline-date", "–")) if raw.get("deadline-date") else "–",
        "url": str(raw.get("notice-url", "")),
        "source": "TED Europa",
    }


def fetch_ted() -> list[dict]:
    """Fetch tenders from TED Search API V3.

    Returns a list of entry dicts. On any error, logs a warning
    and returns an empty list (never crashes).
    """
    try:
        resp = requests.post(
            TED_SEARCH_URL,
            json=SEARCH_BODY,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        notices = data.get("notices") or data.get("results") or []
        if isinstance(data, list):
            notices = data

        return [_extract_entry(n) for n in notices]

    except requests.exceptions.Timeout:
        logger.warning("TED API Timeout – returning empty list")
        return []
    except requests.exceptions.HTTPError as e:
        logger.warning("TED API HTTP Error %s – returning empty list", e)
        return []
    except Exception as e:
        logger.warning("TED API unexpected error: %s – returning empty list", e)
        return []

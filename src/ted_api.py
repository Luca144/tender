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
        "classification-cpv IN (72000000, 79410000) "
        "AND buyer-country = DEU "
        "AND legal-basis = 32014L0025 "
        "SORT BY publication-date DESC"
    ),
    "fields": [
        "publication-number",
        "notice-title",
        "buyer-name",
        "publication-date",
        "deadline-receipt-tender-date-lot",
        "classification-cpv",
        "notice-type",
        "buyer-country",
    ],
    "page": 1,
    "limit": 50,
}


def _extract_entry(raw: dict) -> dict:
    """Convert a raw TED API result into our unified entry format."""
    title = raw.get("notice-title", "")
    if isinstance(title, dict):
        title = title.get("deu") or title.get("eng") or next(iter(title.values()), "–")
    if isinstance(title, list):
        title = title[0] if title else "–"

    buyer = raw.get("buyer-name", "–")
    if isinstance(buyer, dict):
        first_val = buyer.get("deu") or buyer.get("eng") or next(iter(buyer.values()), "–")
        buyer = first_val
    if isinstance(buyer, list):
        buyer = buyer[0] if buyer else "–"

    deadline_raw = raw.get("deadline-receipt-tender-date-lot")
    if isinstance(deadline_raw, list):
        deadline = str(deadline_raw[0]) if deadline_raw else "–"
    elif deadline_raw:
        deadline = str(deadline_raw)
    else:
        deadline = "–"

    # URL from links object (auto-included by API)
    links = raw.get("links", {})
    html_links = links.get("html", {})
    url = html_links.get("DEU") or html_links.get("ENG") or ""
    if not url:
        # Fallback: construct from publication number
        pub_nr = raw.get("publication-number", "")
        if pub_nr:
            url = f"https://ted.europa.eu/en/notice/-/detail/{pub_nr}"

    return {
        "id": str(raw.get("publication-number", "")),
        "title": str(title),
        "buyer": str(buyer),
        "published": str(raw.get("publication-date", "–")).split("+")[0],
        "deadline": deadline.split("+")[0],
        "url": url,
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

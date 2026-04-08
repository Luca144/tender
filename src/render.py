"""HTML Renderer using Jinja2.

Generates a static docs/index.html from tender entries
using the ReqPOOL CI template. Includes relevance scoring
and date normalization for client-side sorting.
"""

import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from jinja2 import Environment, FileSystemLoader

from src.scoring import score_entries

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "templates")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")


def normalize_date_for_sort(date_str: str) -> str:
    """Convert various date formats to ISO 'YYYY-MM-DD HH:MM' for JS sorting.

    Handles:
      - ISO: '2026-04-04' or '2026-04-04+02:00'
      - RFC 2822: 'Tue, 7 Apr 2026 12:53:00 +0200'
      - German: '07.04.2025'
      - Fallback: returns '1970-01-01 00:00' for unparseable input
    """
    if not date_str or date_str == "–":
        return "1970-01-01 00:00"

    # ISO format: 2026-04-04 or 2026-04-04+02:00
    iso_match = re.match(r"(\d{4}-\d{2}-\d{2})", date_str)
    if iso_match:
        date_part = iso_match.group(1)
        time_match = re.search(r"(\d{2}:\d{2})", date_str)
        time_part = time_match.group(1) if time_match else "00:00"
        return f"{date_part} {time_part}"

    # German format: DD.MM.YYYY or DD.MM.YYYY HH:MM
    de_match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", date_str)
    if de_match:
        day, month, year = de_match.groups()
        time_match = re.search(r"(\d{2}:\d{2})", date_str)
        time_part = time_match.group(1) if time_match else "00:00"
        return f"{year}-{month}-{day} {time_part}"

    # RFC 2822: Tue, 7 Apr 2026 12:53:00 +0200
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass

    return "1970-01-01 00:00"


def render_page(
    all_entries: list[dict],
    new_ids: set[str],
    docs_dir: str | None = None,
    template_dir: str | None = None,
    summaries: dict[str, str] | None = None,
) -> str:
    """Render the index.html page with all entries.

    Args:
        all_entries: All tender entries (sorted newest first).
        new_ids: Set of IDs that are new today.
        docs_dir: Output directory (default: docs/).
        template_dir: Template directory (default: templates/).

    Returns:
        Path to the generated HTML file.
    """
    docs = docs_dir or DOCS_DIR
    templates = template_dir or TEMPLATE_DIR

    os.makedirs(docs, exist_ok=True)

    # Score entries for relevance
    score_entries(all_entries)

    # Attach summaries to entries
    _summaries = summaries or {}
    for entry in all_entries:
        entry["summary"] = _summaries.get(entry["id"], "")

    # Normalize dates for client-side sorting
    for entry in all_entries:
        entry["published_iso"] = normalize_date_for_sort(entry.get("published", ""))

    sorted_entries = sorted(
        all_entries,
        key=lambda e: e.get("published_iso", ""),
        reverse=True,
    )

    sources = sorted({e["source"] for e in all_entries})

    now = datetime.now(timezone.utc)
    updated_at = now.strftime("%d.%m.%Y %H:%M Uhr")

    env = Environment(loader=FileSystemLoader(templates), autoescape=True)
    template = env.get_template("index.html.j2")

    html = template.render(
        all_entries=sorted_entries,
        new_ids=new_ids,
        updated_at=updated_at,
        sources=sources,
        total_count=len(all_entries),
        new_count=len(new_ids),
    )

    output_path = os.path.join(docs, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path

"""HTML Renderer using Jinja2.

Generates a static docs/index.html from tender entries
using the ReqPOOL CI template.
"""

import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "templates")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")


def render_page(
    all_entries: list[dict],
    new_ids: set[str],
    docs_dir: str | None = None,
    template_dir: str | None = None,
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

    sorted_entries = sorted(
        all_entries,
        key=lambda e: e.get("published", ""),
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

"""Unit tests for HTML renderer."""

import os

from src.render import render_page

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")


def test_index_html_created(sample_entries, tmp_docs_dir):
    """index.html is created after render_page()."""
    render_page(sample_entries, set(), docs_dir=tmp_docs_dir, template_dir=TEMPLATE_DIR)

    assert os.path.exists(os.path.join(tmp_docs_dir, "index.html"))


def test_contains_title(sample_entries, tmp_docs_dir):
    """The page contains the main title."""
    render_page(sample_entries, set(), docs_dir=tmp_docs_dir, template_dir=TEMPLATE_DIR)

    with open(os.path.join(tmp_docs_dir, "index.html"), encoding="utf-8") as f:
        html = f.read()

    assert "Ausschreibungs-Scout" in html


def test_neu_badge_present(sample_entries, tmp_docs_dir):
    """NEU badge appears for new entries."""
    new_ids = {sample_entries[0]["id"]}
    render_page(sample_entries, new_ids, docs_dir=tmp_docs_dir, template_dir=TEMPLATE_DIR)

    with open(os.path.join(tmp_docs_dir, "index.html"), encoding="utf-8") as f:
        html = f.read()

    assert "NEU" in html


def test_no_badge_for_old(sample_entries, tmp_docs_dir):
    """No NEU badge when no entries are new."""
    render_page(sample_entries, set(), docs_dir=tmp_docs_dir, template_dir=TEMPLATE_DIR)

    with open(os.path.join(tmp_docs_dir, "index.html"), encoding="utf-8") as f:
        html = f.read()

    assert '<span class="badge-neu">' not in html

"""Unit tests for relevance scoring module."""

from src.scoring import score_entry, score_entries


def test_high_relevance_multi_role():
    """Tender matching multiple roles scores high."""
    entry = {
        "title": "SAP Migration Projektmanagement und IT-Beratung",
        "buyer": "Stadtwerke München",
    }
    result = score_entry(entry)
    assert result["score"] >= 40
    assert "IT-Projektmanager" in result["matched_roles"]


def test_zero_for_irrelevant():
    """Completely unrelated tenders score 0."""
    for title in ["Dachinstandsetzung Gymnasium", "LKW mit Kran", "Labornetzteile"]:
        result = score_entry({"title": title, "buyer": "Stadt X"})
        assert result["score"] == 0, f"'{title}' should score 0"
        assert result["matched_roles"] == []


def test_partial_match():
    """Single keyword match gives a moderate score."""
    entry = {"title": "Anforderungsanalyse Netzleitsystem", "buyer": "Netze BW"}
    result = score_entry(entry)
    assert result["score"] > 0
    assert "Requirements Engineer" in result["matched_roles"]


def test_case_insensitive():
    """Keywords match regardless of case."""
    entry1 = {"title": "PROJEKTMANAGEMENT für Energieversorger", "buyer": ""}
    entry2 = {"title": "projektmanagement für energieversorger", "buyer": ""}
    assert score_entry(entry1)["score"] == score_entry(entry2)["score"]


def test_score_capped_at_100():
    """Score never exceeds 100."""
    entry = {
        "title": (
            "SAP Migration Projektmanagement IT-Beratung Digitalisierung "
            "Anforderungsanalyse Prozessoptimierung Scrum Agile Testmanagement "
            "Beschaffung Benchmarking IT-Architektur Cloud Roadmap PMO"
        ),
        "buyer": "Consulting GmbH",
    }
    result = score_entry(entry)
    assert result["score"] <= 100


def test_score_entries_attaches_fields():
    """score_entries() adds relevance_score and matched_roles to every entry."""
    entries = [
        {"title": "IT-Beratung SAP", "buyer": "EnBW"},
        {"title": "Kabelverlegung", "buyer": "Baufirma"},
    ]
    result = score_entries(entries)

    assert result is entries  # mutates in-place
    for e in entries:
        assert "relevance_score" in e
        assert "matched_roles" in e
        assert isinstance(e["relevance_score"], int)
        assert isinstance(e["matched_roles"], list)


def test_matched_roles_correct():
    """Specific keywords map to expected roles."""
    entry = {"title": "Strategische Beschaffung IT-Dienstleistung", "buyer": ""}
    result = score_entry(entry)
    assert "IT-Einkauf" in result["matched_roles"]


def test_empty_title_scores_zero():
    """Entry with empty title gets score 0 or near-zero."""
    result = score_entry({"title": "", "buyer": ""})
    assert result["score"] == 0


def test_buyer_contributes_to_score():
    """Keywords in buyer name also count toward scoring."""
    entry = {"title": "Rahmenvertrag", "buyer": "IT-Beratung Solutions GmbH"}
    result = score_entry(entry)
    assert result["score"] > 0

"""Unit tests for 4-tier relevance scoring system."""

from src.scoring import score_entry, score_entries


# ===== FALSE POSITIVE TESTS (must score 0) =====

class TestFalsePositives:
    """These tenders are NOT relevant for ReqPOOL and must score 0."""

    def test_beschaffung_moebel(self):
        result = score_entry({"title": "Beschaffung von Büromöbeln", "buyer": "Stadt Köln"})
        assert result["score"] == 0

    def test_strasseninfrastruktur(self):
        result = score_entry({"title": "Straßeninfrastruktur Sanierung B42", "buyer": "Bund"})
        assert result["score"] == 0

    def test_gasdruckanlage(self):
        result = score_entry({"title": "Implementierung einer Gasdruckanlage", "buyer": "Stadtwerke X"})
        assert result["score"] == 0

    def test_fahrzeuge(self):
        result = score_entry({"title": "Einführung neuer Fahrzeuge im Fuhrpark", "buyer": "DVB"})
        assert result["score"] == 0

    def test_holzbau(self):
        result = score_entry({"title": "Holzbauarbeiten Turnhalle", "buyer": "Gemeinde Y"})
        assert result["score"] == 0

    def test_financial_controlling(self):
        result = score_entry({"title": "Controlling-Leistungen Haushalt", "buyer": "Landkreis Z"})
        assert result["score"] == 0

    def test_hardware_rollout(self):
        result = score_entry({"title": "Rollout Arbeitsplatz-Hardware", "buyer": "Amt"})
        assert result["score"] == 0

    def test_dachinstandsetzung(self):
        result = score_entry({"title": "Dachinstandsetzung Gymnasium", "buyer": "Stadt X"})
        assert result["score"] == 0

    def test_lkw_mit_kran(self):
        result = score_entry({"title": "LKW mit Kran", "buyer": "Baufirma"})
        assert result["score"] == 0

    def test_reinigung(self):
        result = score_entry({"title": "Reinigungsdienste Bürogebäude", "buyer": "Stadt"})
        assert result["score"] == 0

    def test_kabelverlegung(self):
        result = score_entry({"title": "Kabelverlegung Ortsnetz", "buyer": "Baufirma GmbH"})
        assert result["score"] == 0


# ===== TRUE POSITIVE TESTS (must score > 0) =====

class TestTruePositives:
    """These tenders ARE relevant for ReqPOOL and must score appropriately."""

    def test_rahmenvertrag_it_beratung(self):
        """Framework contract for IT consulting — high score."""
        result = score_entry({
            "title": "Rahmenvertrag IT-Beratung und Projektsteuerung",
            "buyer": "EnBW",
        })
        assert result["score"] >= 40
        assert len(result["matched_roles"]) >= 1

    def test_lastenheft_erp(self):
        """Requirements spec for ERP — strong ReqPOOL fit."""
        result = score_entry({
            "title": "Lastenhefterstellung für ERP-System",
            "buyer": "Bayernwerk",
        })
        assert result["score"] >= 30
        assert "Requirements Engineer" in result["matched_roles"]

    def test_sap_migration_beratung(self):
        """SAP migration consulting — multi-role match."""
        result = score_entry({
            "title": "SAP-Migration Beratungsleistungen und Projektmanagement",
            "buyer": "Stadtwerke München",
        })
        assert result["score"] >= 40

    def test_digitalisierung_beratung(self):
        """Digitalization consulting — IT-Stratege."""
        result = score_entry({
            "title": "Beratungsleistungen Digitalisierung und IT-Strategie",
            "buyer": "RWE",
        })
        assert result["score"] >= 40
        assert "IT-Stratege" in result["matched_roles"]

    def test_softwarebeschaffung(self):
        """Software procurement — IT-Einkauf core service."""
        result = score_entry({
            "title": "Softwarebeschaffung und Softwareauswahl CRM",
            "buyer": "Mainova",
        })
        assert result["score"] >= 30
        assert "IT-Einkauf" in result["matched_roles"]

    def test_testmanagement(self):
        """Test management for software — Testmanager role."""
        result = score_entry({
            "title": "Testmanagement und Qualitätssicherung Software-Einführung",
            "buyer": "50Hertz",
        })
        assert result["score"] >= 20
        assert "Testmanager" in result["matched_roles"]

    def test_scrum_coaching(self):
        """Agile coaching — Scrum Master role."""
        result = score_entry({
            "title": "Scrum Master und Agile Coach für Digitalisierungsprogramm",
            "buyer": "Vattenfall",
        })
        assert result["score"] >= 20
        assert "Scrum Master & Agile Coach" in result["matched_roles"]


# ===== ENERGY SECTOR BONUS TESTS =====

class TestEnergySectorBonus:
    """Known energy buyers should score higher than unknown buyers."""

    def test_energy_buyer_bonus(self):
        """Same title: energy buyer scores higher."""
        entry_energy = {"title": "Software-Beratung Digitalisierung", "buyer": "EnBW"}
        entry_other = {"title": "Software-Beratung Digitalisierung", "buyer": "Stadt Test"}
        assert score_entry(entry_energy)["score"] > score_entry(entry_other)["score"]

    def test_energy_it_keyword_bonus(self):
        """Energy-IT terms in title add bonus."""
        entry_energy = {"title": "IT-Beratung Redispatch Netzleitsystem", "buyer": "Test AG"}
        entry_generic = {"title": "IT-Beratung", "buyer": "Test AG"}
        assert score_entry(entry_energy)["score"] > score_entry(entry_generic)["score"]


# ===== SCORING MECHANICS TESTS =====

class TestScoringMechanics:
    """Verify the scoring formula works correctly."""

    def test_context_gate_blocks(self):
        """No context keyword → score 0 with context=False in breakdown."""
        result = score_entry({"title": "Tiefbauarbeiten Kanal", "buyer": "Baufirma"})
        assert result["score"] == 0
        assert result["score_breakdown"]["context"] is False

    def test_context_gate_passes(self):
        """Context keyword present → context=True in breakdown."""
        result = score_entry({"title": "IT-Beratung Projektmanagement", "buyer": "Test"})
        assert result["score"] > 0
        assert result["score_breakdown"]["context"] is True

    def test_score_capped_at_100(self):
        """Score never exceeds 100."""
        result = score_entry({
            "title": (
                "Rahmenvertrag IT-Beratung Softwarebeschaffung Lastenhefterstellung "
                "Projektmanagement Digitalisierung IT-Strategie Scrum Agile Coach "
                "Testmanagement Qualitätssicherung Anforderungsanalyse Prozessoptimierung "
                "IT-Architektur Cloud-Architektur PMO Programmmanagement"
            ),
            "buyer": "EnBW Energie",
        })
        assert result["score"] <= 100

    def test_case_insensitive(self):
        """Keywords match regardless of case."""
        r1 = score_entry({"title": "PROJEKTMANAGEMENT IT-BERATUNG", "buyer": ""})
        r2 = score_entry({"title": "projektmanagement it-beratung", "buyer": ""})
        assert r1["score"] == r2["score"]

    def test_empty_title_scores_zero(self):
        result = score_entry({"title": "", "buyer": ""})
        assert result["score"] == 0

    def test_score_entries_attaches_fields(self):
        """score_entries() adds relevance_score and matched_roles to every entry."""
        entries = [
            {"title": "IT-Beratung SAP", "buyer": "EnBW"},
            {"title": "Kabelverlegung", "buyer": "Baufirma"},
        ]
        score_entries(entries)
        for e in entries:
            assert "relevance_score" in e
            assert "matched_roles" in e

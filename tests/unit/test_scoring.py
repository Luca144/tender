"""Unit tests for scoring system with context gate + sector gate."""

from src.scoring import score_entry, score_entries


# ===== FALSE POSITIVE TESTS (must score 0) =====

class TestFalsePositives:
    """Tenders NOT relevant for ReqPOOL must score 0."""

    # No IT context
    def test_holzbau(self):
        result = score_entry({"title": "Holzbauarbeiten Turnhalle", "buyer": "Gemeinde Y"})
        assert result["score"] == 0

    def test_dachinstandsetzung(self):
        result = score_entry({"title": "Dachinstandsetzung Gymnasium", "buyer": "Stadt X"})
        assert result["score"] == 0

    def test_kabelverlegung(self):
        result = score_entry({"title": "Kabelverlegung Ortsnetz", "buyer": "Baufirma GmbH"})
        assert result["score"] == 0

    # IT context but WRONG SECTOR
    def test_public_sector_blocked(self):
        """IT tender from municipality — wrong sector for ReqPOOL."""
        result = score_entry({
            "title": "Vergabemanagement IT-Dienstleistungen",
            "buyer": "Landeshauptstadt München",
        })
        assert result["score"] == 0
        assert result["score_breakdown"]["sector"] is False

    def test_university_blocked(self):
        result = score_entry({
            "title": "IT-Beratung Digitalisierung Campus",
            "buyer": "Universität Hamburg",
        })
        assert result["score"] == 0

    def test_transport_blocked(self):
        result = score_entry({
            "title": "Softwareeinführung Fahrgastinformation",
            "buyer": "Münchner Verkehrsgesellschaft",
        })
        assert result["score"] == 0

    def test_federal_agency_blocked(self):
        result = score_entry({
            "title": "IT-Projektmanagement Verwaltung",
            "buyer": "Bundesagentur für Arbeit",
        })
        assert result["score"] == 0

    # Drees & Sommer construction tenders
    def test_drees_sommer_bau(self):
        result = score_entry({
            "title": "Feuerwehrgerätehaus - TWP inkl. Brandschutz",
            "buyer": "Drees & Sommer SE Hamburg - Projektmanagement",
        })
        assert result["score"] == 0

    def test_turnhalle_sanierung(self):
        result = score_entry({
            "title": "ZV - Sanierung Turnhalle - Abbrucharbeiten",
            "buyer": "Stadt Coburg - Beschaffungsamt",
        })
        assert result["score"] == 0

    def test_feuerwehr_rahmenvertrag(self):
        """LT FW = Löschfahrzeug, not IT."""
        result = score_entry({
            "title": "LT FW Rahmenvertrag",
            "buyer": "EnBW Energie Baden-Württemberg AG",
        })
        assert result["score"] == 0


# ===== TRUE POSITIVE TESTS (must score > 0) =====

class TestTruePositives:
    """Tenders relevant for ReqPOOL from target sectors must score > 0."""

    def test_it_beratung_energie(self):
        result = score_entry({
            "title": "Rahmenvertrag IT-Beratung und Projektsteuerung",
            "buyer": "EnBW",
        })
        assert result["score"] >= 40

    def test_lastenheft_erp(self):
        result = score_entry({
            "title": "Lastenhefterstellung für ERP-System",
            "buyer": "Bayernwerk",
        })
        assert result["score"] >= 30
        assert "Requirements Engineer" in result["matched_roles"]

    def test_sap_migration_beratung(self):
        result = score_entry({
            "title": "SAP-Migration Beratungsleistungen und Projektmanagement",
            "buyer": "Stadtwerke München",
        })
        assert result["score"] >= 30

    def test_softwarebeschaffung_energie(self):
        result = score_entry({
            "title": "Softwarebeschaffung und Softwareauswahl CRM",
            "buyer": "Mainova",
        })
        assert result["score"] >= 30
        assert "IT-Einkauf" in result["matched_roles"]

    def test_testmanagement_energie(self):
        result = score_entry({
            "title": "Testmanagement und Qualitätssicherung Software-Einführung",
            "buyer": "50Hertz",
        })
        assert result["score"] >= 20
        assert "Testmanager" in result["matched_roles"]

    def test_telko_it_beratung(self):
        """Telco sector is a target sector."""
        result = score_entry({
            "title": "IT-Projektmanagement Digitalisierung",
            "buyer": "Deutsche Telekom",
        })
        assert result["score"] > 0

    def test_immobilien_it(self):
        """Real estate sector with IT topic."""
        result = score_entry({
            "title": "Softwareeinführung Gebäudeautomation Smart Building",
            "buyer": "Vonovia Immobilien GmbH",
        })
        assert result["score"] > 0

    def test_sector_title_keywords(self):
        """Energy-specific title passes sector gate even with unknown buyer."""
        result = score_entry({
            "title": "IT-Beratung Redispatch Netzleitsystem",
            "buyer": "Unbekanntes Unternehmen",
        })
        assert result["score"] > 0


# ===== SECTOR BONUS TESTS =====

class TestSectorBonus:
    """Known target-sector buyers get bonus points."""

    def test_known_buyer_higher_than_unknown(self):
        """Known energy buyer scores higher than generic sector-keyword buyer."""
        entry_known = {"title": "IT-Beratung Digitalisierung", "buyer": "EnBW"}
        entry_sector = {"title": "IT-Beratung Digitalisierung", "buyer": "Stadtwerk Musterstadt"}
        assert score_entry(entry_known)["score"] >= score_entry(entry_sector)["score"]


# ===== SCORING MECHANICS TESTS =====

class TestScoringMechanics:

    def test_context_gate_blocks(self):
        result = score_entry({"title": "Tiefbauarbeiten Kanal", "buyer": "EnBW"})
        assert result["score"] == 0
        assert result["score_breakdown"]["context"] is False

    def test_sector_gate_blocks(self):
        """IT title but wrong sector buyer."""
        result = score_entry({"title": "IT-Beratung", "buyer": "Stadt Musterstadt"})
        assert result["score"] == 0
        assert result["score_breakdown"]["context"] is True
        assert result["score_breakdown"]["sector"] is False

    def test_both_gates_pass(self):
        result = score_entry({"title": "IT-Beratung Projektmanagement", "buyer": "EnBW"})
        assert result["score"] > 0
        assert result["score_breakdown"]["context"] is True
        assert result["score_breakdown"]["sector"] is True

    def test_score_capped_at_100(self):
        result = score_entry({
            "title": (
                "Rahmenvertrag IT-Beratung Softwarebeschaffung Lastenhefterstellung "
                "Projektmanagement Digitalisierung IT-Strategie Scrum Agile Coach "
                "Testmanagement Qualitätssicherung Anforderungsanalyse Prozessoptimierung "
                "IT-Architektur Cloud-Architektur PMO Programmmanagement Netzleitsystem"
            ),
            "buyer": "EnBW Energie",
        })
        assert result["score"] <= 100

    def test_case_insensitive(self):
        r1 = score_entry({"title": "PROJEKTMANAGEMENT IT-BERATUNG", "buyer": "EnBW"})
        r2 = score_entry({"title": "projektmanagement it-beratung", "buyer": "EnBW"})
        assert r1["score"] == r2["score"]

    def test_empty_title_scores_zero(self):
        result = score_entry({"title": "", "buyer": ""})
        assert result["score"] == 0

    def test_score_entries_attaches_fields(self):
        entries = [
            {"title": "IT-Beratung SAP", "buyer": "EnBW"},
            {"title": "Kabelverlegung", "buyer": "Baufirma"},
        ]
        score_entries(entries)
        for e in entries:
            assert "relevance_score" in e
            assert "matched_roles" in e

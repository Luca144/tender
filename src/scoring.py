"""Relevance scoring for ReqPOOL tender matching.

Four-tier scoring system:
1. Context Gate — Is this an IT/consulting tender at all?
2. Role Matching — Which ReqPOOL roles fit?
3. ReqPOOL Fit Bonus — Direct match to ReqPOOL's core services?
4. Energy Sector Bonus — Is the buyer a known energy company?
"""

import re

# ---------------------------------------------------------------------------
# Tier 1: Context Gate
# At least one of these must match, otherwise score = 0 immediately.
# This eliminates all non-IT/consulting tenders (construction, furniture, etc.)
# ---------------------------------------------------------------------------

_CONTEXT_KEYWORDS_SIMPLE = [
    # IT domain
    "software", "ikt", "edv", "sap", "erp", "crm",
    "digitalisierung", "cloud", "saas", "paas", "iaas",
    "cyber", "informationssicherheit",
    # Consulting domain (specific to IT/management, NOT generic "beratung")
    "it-beratung", "consulting", "managementberatung",
    "unternehmensberatung", "strategieberatung",
    "digitalisierungsberatung",
    # Software project lifecycle
    "softwareprojekt", "softwareeinführung", "softwarebeschaffung",
    "softwareauswahl", "systemeinführung", "systemauswahl",
    "anforderungsmanagement", "anforderungsanalyse",
    "lastenheft", "pflichtenheft",
    "testmanagement", "qualitätssicherung",
    "projektmanagement", "projektsteuerung", "programmmanagement",
    # IT procurement
    "vergabebegleitung", "ausschreibungsberatung", "vergabeberatung",
    "ausschreibungsmanagement",
    "rahmenvertrag", "rahmenvereinbarung",
    # Energy IT specifics
    "marktkommunikation", "redispatch", "netzleitsystem",
    "billing", "abrechnungssystem", "energiedatenmanagement",
    "smart meter", "intelligentes messsystem",
    "mako", "gpke",
]

# Short terms that need word-boundary matching to avoid false positives
_CONTEXT_KEYWORDS_BOUNDARY = ["it", "bi", "ki", "dms", "ecm"]


def _has_context(title: str) -> bool:
    """Check if TITLE contains at least one IT/consulting context keyword.

    Only checks title, not buyer — 'Projektmanagement' in a company name
    like 'Drees & Sommer - Projektmanagement' is not IT context.
    """
    for kw in _CONTEXT_KEYWORDS_SIMPLE:
        if kw in title:
            return True
    for kw in _CONTEXT_KEYWORDS_BOUNDARY:
        if re.search(r'\b' + re.escape(kw) + r'\b', title):
            return True
    return False


# ---------------------------------------------------------------------------
# Tier 2: Role Matching — refined keywords, generics removed
# ---------------------------------------------------------------------------

ROLE_KEYWORDS: dict[str, list[str]] = {
    "IT-Stratege": [
        "it-strategie", "digitalisierungsstrategie",
        "digitale transformation", "it-beratung", "strategieberatung",
        "e-government", "smart city", "it-governance", "it-steuerung",
        "digitalisierungsberatung", "it-masterplan", "it-roadmap",
        "technologieberatung",
    ],
    "PMO & IT-Koordinator": [
        "pmo", "projektsteuerung", "programmmanagement",
        "multiprojektmanagement", "it-koordination", "projektkoordination",
        "projektbüro", "projektportfolio", "projektoffice",
    ],
    "Business-Analyst": [
        "business-analyse", "business analyse", "geschäftsprozessanalyse",
        "wirtschaftlichkeitsanalyse", "kosten-nutzen-analyse",
        "machbarkeitsstudie", "ist-analyse", "soll-konzept",
        "potenzialanalyse", "bedarfsanalyse",
    ],
    "Requirements Engineer": [
        "anforderungsmanagement", "requirements engineering",
        "lastenheft", "pflichtenheft",
        "anforderungsanalyse", "anforderungsspezifikation",
        "fachkonzept", "lastenhefterstellung",
        "anforderungskatalog", "leistungsbeschreibung",
        "pflichtenhefterstellung",
    ],
    "IT-Architekt": [
        "it-architektur", "enterprise-architektur", "systemarchitektur",
        "lösungsarchitektur", "cloud-architektur",
        "microservices", "systemdesign", "datenarchitektur",
        "schnittstellenmanagement",
    ],
    "Prozessmanager": [
        "prozessmanagement", "prozessoptimierung", "prozessdokumentation",
        "prozessautomatisierung", "bpmn", "geschäftsprozessmodellierung",
        "prozessberatung", "prozessanalyse", "prozesslandkarte",
    ],
    "IT-Projektmanager": [
        "it-projektmanagement", "it-projektleitung",
        "projektmanagement", "projektleitung", "projektmanager",
        "projektumsetzung", "systemeinführung", "softwareeinführung",
        "erp-einführung", "it-migration", "sap-einführung",
        "sap-migration",
    ],
    "IT-Cost Controller": [
        "it-kosten", "it-controlling", "it-kostenanalyse",
        "it-benchmarking", "it-budgetierung",
        "softwarekosten", "lizenzmanagement", "lizenzkostenoptimierung",
    ],
    "IT-Einkauf": [
        "it-beschaffung", "softwarebeschaffung", "it-vergabe",
        "ausschreibungsberatung", "beschaffungsberatung", "vergabeberatung",
        "vergabebegleitung", "ausschreibungsmanagement",
        "softwareauswahl", "lieferantenauswahl", "lieferantenbewertung",
    ],
    "Proxy-Product Owner": [
        "product owner", "backlog", "produktmanagement",
        "user story", "product backlog", "proxy-po",
    ],
    "Testmanager": [
        "testmanagement", "qualitätssicherung", "softwaretest",
        "abnahmetest", "testkonzept", "teststrategie",
        "testautomatisierung", "qa-management",
        "release-management", "integrationstests",
    ],
    "Scrum Master & Agile Coach": [
        "scrum", "agile coach", "agile transformation",
        "agile methoden", "scrum master", "kanban",
        "agile projektmethodik", "agiles projektmanagement",
    ],
}

# ---------------------------------------------------------------------------
# Tier 3: ReqPOOL Fit Bonus — terms that directly describe ReqPOOL's services
# ---------------------------------------------------------------------------

_REQPOOL_FIT_KEYWORDS = [
    "beratungsleistungen", "beratungsleistung",
    "managementberatung", "unternehmensberatung",
    "rahmenvertrag", "rahmenvereinbarung",
    "vergabebegleitung", "ausschreibungsmanagement",
    "softwarebeschaffung", "softwareauswahl",
    "lastenhefterstellung", "konzepterstellung",
    "pflichtenhefterstellung",
    "lieferantenauswahl", "lieferantenbewertung",
    "ist-analyse", "soll-konzept",
    "it-governance", "it-steuerung",
    "digitalisierungsberatung",
]

# ---------------------------------------------------------------------------
# Tier 4: Energy Sector Bonus — buyer is energy company or energy-IT terms
# ---------------------------------------------------------------------------

_ENERGY_IT_KEYWORDS = [
    "redispatch", "marktkommunikation", "netzleitsystem",
    "billing", "abrechnungssystem", "energiedatenmanagement",
    "smart meter", "intelligentes messsystem",
    "mako", "gpke", "geli gas", "wim",
    "einspeisemanagement", "engpassmanagement",
    "netzbetrieb", "netzsteuerung", "messwesen",
    "energiewirtschaft", "energieversorger",
    "stadtwerke", "netzbetreiber",
]

# Imported at function level to avoid circular import
_energy_buyers_cache: list[str] | None = None


def _get_energy_buyers() -> list[str]:
    """Lazy-load ENERGY_BUYERS from rss_sources to avoid circular import."""
    global _energy_buyers_cache
    if _energy_buyers_cache is None:
        from src.rss_sources import ENERGY_BUYERS
        _energy_buyers_cache = ENERGY_BUYERS
    return _energy_buyers_cache


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def score_entry(entry: dict) -> dict:
    """Score a single entry for ReqPOOL relevance using 4-tier system.

    Returns dict with 'score' (0-100), 'matched_roles', 'score_breakdown'.
    """
    title_lower = entry.get("title", "").lower()
    text = f"{title_lower} {entry.get('buyer', '')}".lower()

    # Tier 1: Context Gate — only checks TITLE, not buyer name
    if not _has_context(title_lower):
        return {
            "score": 0,
            "matched_roles": [],
            "score_breakdown": {"context": False, "role_score": 0, "fit_bonus": 0, "energy_bonus": 0},
        }

    # Tier 2: Role Matching
    matched_roles = []
    total_keyword_hits = 0
    for role, keywords in ROLE_KEYWORDS.items():
        role_hits = sum(1 for kw in keywords if kw in text)
        if role_hits > 0:
            matched_roles.append(role)
            total_keyword_hits += role_hits

    role_score = min(60, len(matched_roles) * 12 + total_keyword_hits * 4)

    # Tier 3: ReqPOOL Fit Bonus
    fit_hits = sum(1 for kw in _REQPOOL_FIT_KEYWORDS if kw in text)
    fit_bonus = min(25, fit_hits * 8)

    # Tier 4: Energy Sector Bonus
    energy_bonus = 0
    buyer_lower = entry.get("buyer", "").lower()
    if any(eb.lower() in buyer_lower for eb in _get_energy_buyers()):
        energy_bonus += 8
    title_lower = entry.get("title", "").lower()
    if any(ek in title_lower for ek in _ENERGY_IT_KEYWORDS):
        energy_bonus += 7
    energy_bonus = min(15, energy_bonus)

    raw_score = role_score + fit_bonus + energy_bonus
    final_score = min(100, raw_score)

    return {
        "score": final_score,
        "matched_roles": matched_roles,
        "score_breakdown": {
            "context": True,
            "role_score": role_score,
            "fit_bonus": fit_bonus,
            "energy_bonus": energy_bonus,
        },
    }


def score_entries(entries: list[dict]) -> list[dict]:
    """Score all entries and attach relevance fields in-place."""
    for entry in entries:
        result = score_entry(entry)
        entry["relevance_score"] = result["score"]
        entry["matched_roles"] = result["matched_roles"]
    return entries

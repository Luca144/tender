"""Relevance scoring for ReqPOOL tender matching.

Scores each tender entry based on how well it matches ReqPOOL's
service portfolio (12 consulting roles). Uses keyword matching
against tender title and buyer name.
"""

import re

ROLE_KEYWORDS: dict[str, list[str]] = {
    "IT-Stratege": [
        "it-strategie", "digitalisierung", "digitalisierungsstrategie",
        "digitale transformation", "it-beratung", "strategieberatung",
        "e-government", "smart city",
    ],
    "PMO & IT-Koordinator": [
        "pmo", "projektsteuerung", "programmmanagement", "roadmap",
        "multiprojektmanagement", "it-koordination", "projektkoordination",
        "projektbüro", "berichtswesen", "reporting",
    ],
    "Business-Analyst": [
        "business-analyse", "marktanalyse", "wirtschaftlichkeitsanalyse",
        "kosten-nutzen", "machbarkeitsstudie", "geschäftsprozessanalyse",
        "unternehmensanalyse",
    ],
    "Requirements Engineer": [
        "anforderungsmanagement", "requirements", "lastenheft", "pflichtenheft",
        "anforderungsanalyse", "anforderungsspezifikation", "spezifikation",
        "fachkonzept",
    ],
    "IT-Architekt": [
        "it-architektur", "enterprise-architektur", "systemarchitektur",
        "lösungsarchitektur", "microservices", "cloud-architektur",
        "plattform", "datenplattform", "infrastruktur",
    ],
    "Prozessmanager": [
        "prozessmanagement", "prozessoptimierung", "prozessdokumentation",
        "prozessautomatisierung", "bpmn", "workflow", "geschäftsprozess",
        "prozessberatung",
    ],
    "IT-Projektmanager": [
        "projektmanagement", "projektleitung", "projektmanager",
        "projektdurchführung", "projektumsetzung", "implementierung",
        "einführung", "migration", "rollout", "sap",
    ],
    "IT-Cost Controller": [
        "it-kosten", "kostenanalyse", "benchmarking", "controlling",
        "wirtschaftlichkeit", "budgetierung", "kostenbewertung",
    ],
    "IT-Einkauf": [
        "beschaffung", "vergabe", "einkauf", "ausschreibungsberatung",
        "beschaffungsberatung", "vergabeberatung", "strategische beschaffung",
    ],
    "Proxy-Product Owner": [
        "product owner", "backlog", "produktmanagement", "user story",
        "product backlog",
    ],
    "Testmanager": [
        "testmanagement", "qualitätssicherung", "qa", "softwaretest",
        "abnahmetest", "testkonzept", "teststrategie",
    ],
    "Scrum Master & Agile Coach": [
        "scrum", "agile", "kanban", "agile methoden", "scrum master",
        "agile coach", "agile transformation", "devops",
    ],
}

# Bonus keywords that indicate general IT/consulting relevance
_IT_BONUS_KEYWORDS = [
    "it", "software", "beratung", "consulting", "dienstleistung",
    "managementberatung",
]


def score_entry(entry: dict) -> dict:
    """Score a single entry for ReqPOOL relevance.

    Args:
        entry: Unified entry dict with 'title' and 'buyer' fields.

    Returns:
        Dict with 'score' (int 0-100) and 'matched_roles' (list[str]).
    """
    text = f"{entry.get('title', '')} {entry.get('buyer', '')}".lower()

    matched_roles = []
    total_keyword_hits = 0

    for role, keywords in ROLE_KEYWORDS.items():
        role_hits = sum(1 for kw in keywords if kw in text)
        if role_hits > 0:
            matched_roles.append(role)
            total_keyword_hits += role_hits

    base_score = len(matched_roles) * 15 + total_keyword_hits * 5

    # IT bonus — word-boundary match to avoid false positives ("mit" != "it")
    if any(re.search(r'\b' + re.escape(kw) + r'\b', text) for kw in _IT_BONUS_KEYWORDS):
        base_score += 10

    return {
        "score": min(100, base_score),
        "matched_roles": matched_roles,
    }


def score_entries(entries: list[dict]) -> list[dict]:
    """Score all entries and attach relevance fields.

    Mutates entries in-place, adding 'relevance_score' (int)
    and 'matched_roles' (list[str]) to each entry dict.

    Returns the entries list.
    """
    for entry in entries:
        result = score_entry(entry)
        entry["relevance_score"] = result["score"]
        entry["matched_roles"] = result["matched_roles"]
    return entries

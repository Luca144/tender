"""AI-powered Management Summaries via Claude Haiku.

Generates concise German management summaries for high-relevance
tender entries. Summaries describe what is being tendered, the buyer,
and which ReqPOOL consulting role would fit best.
"""

import json
import logging
import os
import time

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5-20251001"
RELEVANCE_THRESHOLD = 20
MAX_RETRIES = 2
RETRY_DELAY = 1.0
BATCH_DELAY = 0.1

SYSTEM_PROMPT = (
    "Du bist ein Senior-Berater bei ReqPOOL (Management-Beratung für Software-Projekte).\n"
    "Antworte NUR mit einem JSON-Objekt. Kein Text davor oder danach.\n"
    "Jedes Feld enthält genau 1 kurzen deutschen Satz:\n\n"
    '{"chance": "Was wird gesucht und warum passt das zu ReqPOOL?",'
    ' "empfehlung": "Welche Rolle(n) anbieten: IT-Projektmanager / Requirements Engineer / '
    "Business-Analyst / IT-Architekt / Prozessmanager / Scrum Master / Testmanager / "
    'IT-Stratege / PMO / IT-Einkauf / Proxy-PO / IT-Cost Controller?",'
    ' "naechster_schritt": "Was konkret tun? z.B. Angebot vorbereiten, Unterlagen anfordern",'
    ' "fit_score": 0-100}\n\n'
    "fit_score: 0=irrelevant, 30=evtl. interessant, 60=guter Fit, 90=sehr guter Fit.\n"
    "WICHTIG: Verteile die Info auf alle 3 Textfelder. Jedes Feld max. 1 Satz."
)


def _get_client():
    """Create Anthropic client. Returns None if API key is missing or package unavailable."""
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except ImportError:
        logger.warning("anthropic package nicht installiert – überspringe Summaries")
        return None
    except Exception as e:
        logger.warning("Anthropic Client-Fehler: %s", e)
        return None


def _build_user_message(entry: dict) -> str:
    """Build the user prompt from an entry's fields."""
    title = entry.get("title", "–")
    buyer = entry.get("buyer", "–")
    deadline = entry.get("deadline", "–")
    roles = ", ".join(entry.get("matched_roles", []))
    return (
        f"Ausschreibung: {title}\n"
        f"Auftraggeber: {buyer}\n"
        f"Frist: {deadline}\n"
        f"Erkannte Rollen: {roles or '–'}"
    )


def _parse_summary_json(text: str) -> dict:
    """Parse the JSON response from Claude into a structured summary dict."""
    try:
        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
            cleaned = cleaned.rsplit("```", 1)[0]
        data = json.loads(cleaned)
        return {
            "chance": str(data.get("chance", "")),
            "empfehlung": str(data.get("empfehlung", "")),
            "naechster_schritt": str(data.get("naechster_schritt", "")),
            "fit_score": int(data.get("fit_score", 0)),
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        # Fallback: treat entire text as unstructured summary
        return {
            "chance": text.strip(),
            "empfehlung": "",
            "naechster_schritt": "",
            "fit_score": 0,
        }


def generate_summary(entry: dict, client) -> str:
    """Generate a management summary for a single entry.

    Returns JSON string with structured summary, or "" on any error.
    """
    if client is None:
        return ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_user_message(entry)}],
            )
            raw = message.content[0].text.strip()
            parsed = _parse_summary_json(raw)
            return json.dumps(parsed, ensure_ascii=False)
        except Exception as e:
            logger.warning(
                "Summary fehlgeschlagen (Versuch %d/%d) für '%s': %s",
                attempt + 1, MAX_RETRIES + 1, entry.get("id", "?"), e,
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return ""


def summarize_entries(
    entries: list[dict], stored_summaries: dict[str, str]
) -> dict[str, str]:
    """Generate summaries for entries with relevance_score >= threshold.

    Skips entries that already have a summary in stored_summaries.

    Returns dict mapping entry ID -> summary (includes both stored and new).
    """
    result = dict(stored_summaries)

    to_summarize = [
        e for e in entries
        if e.get("relevance_score", 0) >= RELEVANCE_THRESHOLD
        and e["id"] not in result
    ]

    if not to_summarize:
        logger.info("Keine neuen Einträge zum Zusammenfassen")
        return result

    client = _get_client()
    if client is None:
        logger.warning("ANTHROPIC_API_KEY nicht gesetzt – überspringe Summaries")
        return result

    logger.info("Generiere %d Management Summaries...", len(to_summarize))

    for i, entry in enumerate(to_summarize):
        summary = generate_summary(entry, client)
        if summary:
            result[entry["id"]] = summary
            logger.info("Summary %d/%d generiert: %s", i + 1, len(to_summarize), entry["id"])
        else:
            logger.warning("Summary %d/%d fehlgeschlagen: %s", i + 1, len(to_summarize), entry["id"])

        if i < len(to_summarize) - 1:
            time.sleep(BATCH_DELAY)

    return result

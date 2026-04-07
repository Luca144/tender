# ReqPOOL Tender Scout

Automatischer Ausschreibungs-Scout für Energie-IT-Projekte.
Täglich aktualisiert, keine manuelle Pflege nötig.

## Was er macht

Durchsucht täglich TED Europa, DTVP, Vergabe.NRW und Bund.de
nach relevanten Energie- & IT-Ausschreibungen und zeigt sie
übersichtlich auf einer Webseite an.

Filterung entspricht der manuellen Suche:
- CPV 72000000 (IT) + 79410000 (Beratung)
- Land: Deutschland
- Rechtsgrundlage: Richtlinie 2014/25/EU

## Setup (einmalig)

```bash
git clone https://github.com/reqpool/tender-scout
cd tender-scout
pip install -r requirements.txt
python main.py
```

Danach `docs/index.html` im Browser öffnen.

## GitHub Pages aktivieren

Settings → Pages → Source: Deploy from branch → Branch: main → /docs

## Manuell auslösen

GitHub → Actions → "Tender Scout" → "Run workflow"

## Tests ausführen

```bash
pytest              # alle Tests
pytest -m smoke     # nur Smoke Tests
pytest -m e2e       # nur E2E Tests
```

## Manuelle Abnahme-Checkliste (nach erstem Deployment)

- [ ] GitHub Actions Workflow läuft grün durch
- [ ] GitHub Pages URL öffnet sich
- [ ] Mindestens eine Quelle liefert Ausschreibungen
- [ ] NEU-Badge erscheint bei frischen Einträgen
- [ ] Quellenfilter funktioniert im Browser
- [ ] Seite ist auf Mobilgerät lesbar

## Geplante Erweiterungen (nach MVP)

- KI-Bewertung der Relevanz via Claude API
- Weitere Quellen (Freelancermap als Sales-Signal)
- E-Mail-Benachrichtigung bei neuen Treffern
- Kundeninformationen anreichern

## Architektur

Siehe [PLANNING.md](PLANNING.md)

# ADR 003 — Single-File-State-Machine beibehalten
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** Decision-Log in progress.md; architecture.md §3.1

## Context
Das gesamte Spiel läuft in **einer** `while running`-Schleife in `main.py` (~600
Zeilen, 8 States, Event-/Update-/Draw-Verzweigung). Mit Rebirth, Waffen und mehr
Inhalt wächst die Datei. Frage: jetzt strukturell aufräumen oder den einfachen
Aufbau halten? Constraints: Anfänger, soll am Spiel arbeiten statt an Architektur,
will den Überblick behalten.

## Decision
Die **Single-File-State-Machine bleibt das Herz**. Ausgelagert werden nur Daten
(`balance.py`) und klar abgrenzbare Helfer — und das nur, wenn eine konkrete Stelle
wirklich unübersichtlich wird.

## Alternatives
- **States schrittweise in eigene Module ziehen** (z. B. `states/playing.py`):
  sauberer bei starkem Wachstum, aber mehr Umbau und neue Konzepte (Modul-Grenzen,
  geteilter Zustand) mitten im Lernen.
- **Größerer Refactor / Szenen-System:** lehrreich, aber hält vom Spielebauen ab
  und ist riskant (viel Bewegung ohne neuen Spielwert).

## Consequences
- **Positiv:** Minimaler Umbau, alles an einem bekannten Ort, niedrige kognitive
  Last für einen Anfänger. Schnelles Vorankommen beim eigentlichen Spiel.
- **Negativ / Bindung:** `main.py` wird groß und muss beobachtet werden. Risiko,
  dass Logik dort „klebt". Gegenmittel: Golden Rule 6 (auslagern, wenn eine Stelle
  wehtut) und die Regel, jeden State in allen drei Phasen zu behandeln (Golden
  Rule 4). Diese Entscheidung kann später durch ein neues ADR abgelöst werden, wenn
  die Datei unhandlich wird.

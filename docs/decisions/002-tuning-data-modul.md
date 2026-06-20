# ADR 002 — Content-Tuning: zentrales Datenmodul jetzt, JSON später
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** Decision-Log in progress.md; architecture.md §6; roadmap.md Phase 1

## Context
Inhalte und Balance-Werte sind aktuell über den Code verstreut (Wellen-Formeln in
`main.py`, Upgrade-Listen in `upgrade_menu.py`/`main_menu.py`). Es ist viel
Inhaltszuwachs geplant (mehr Upgrades, Gegner, Verbesserungen). Häufiges Balancing
wird nötig. Der Entwickler ist Anfänger; neue Technik soll sparsam eingeführt
werden. Frage: Wie trennen wir Tuning-Werte von Logik, ohne uns mit Komplexität zu
überladen?

## Decision
Tuning-Zahlen wandern in **ein zentrales Python-Datenmodul `balance.py`**
(Tabellen/Dicts). Verhalten/Logik bleibt im Code. **Kein JSON** zunächst.

## Alternatives
- **Sofort JSON:** Maximale Trennung Daten/Code, gut für externes Balancing/Modding.
  Verworfen (für jetzt): bringt Lade-, Parse- und Validierungs-Schicht plus
  fehleranfälliges Hand-Editieren ohne Syntax-Check — viel Aufwand und Fehlerquelle
  für wenig Sofortnutzen bei einem Solo-Anfängerprojekt.
- **Alles hartkodiert lassen:** Kein Aufwand, aber Balancing bleibt zäh, weil jede
  Zahlenänderung tief im verstreuten Code liegt.

## Consequences
- **Positiv:** Alle Stellschrauben an einem Ort, mit Syntax-Check und Kommentaren,
  ohne neue Technik. Der Schritt „später nach JSON" ist klein (nur den Inhalt von
  `balance.py` serialisieren), wenn er wirklich gebraucht wird.
- **Negativ / Bindung:** `balance.py` ist weiterhin Code, also kein Balancing durch
  Nicht-Programmierer / kein Hot-Reload ohne Neustart. Disziplin nötig, neue Werte
  konsequent dort einzutragen statt wieder inline (siehe Golden Rule 2).
- JSON-Migration bleibt als Backlog-Option (roadmap.md Part 2).

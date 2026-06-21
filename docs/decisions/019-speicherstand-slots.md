# ADR 019 — Speicherstand-Slots, gewählt vor dem Hauptmenü

- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** architecture.md §3.1 (State-Machine), §Persistenz; progress.md D-Slots; baut auf
  ADR 002/004 (Save-Modell) auf

## Context
Bisher gab es **einen** globalen Spielstand (`save.json`). Der Nutzer wünschte mehrere,
**vor dem Hauptmenü** wählbare Speicherstände (wie Profil-Auswahl beim Spielstart), inkl.
Löschen. Wichtig war, dass die vielen bestehenden `sd.save(save)`-Aufrufe in `main.py` nicht
alle umgeschrieben werden müssen.

## Decision
- **Aktiv-Slot-Modell in `save_data`:** drei Slots `save_slot<N>.json` (`SLOTS=(1,2,3)`). Ein
  modulglobaler `_active_slot` merkt sich den zuletzt geladenen Slot; `save(data)` schreibt
  dorthin → **alle bestehenden `sd.save(save)`-Aufrufe funktionieren unverändert weiter**.
  `load(slot)` setzt den Slot aktiv und lädt ihn; `delete(slot)` entfernt die Datei;
  `slot_summary(slot)` liefert Kurzinfo (Rekord-Welle, Münzen) für die Auswahl.
- **Migration:** Beim ersten Laden von Slot 1 wird eine vorhandene Alt-`save.json` einmalig
  übernommen (keine verlorenen Fortschritte).
- **Neuer State `SLOT_SELECT`** als **Einstiegs-State** (vor `MAIN_MENU`). `SlotSelectMenu`
  zeigt je Slot eine Karte (Rekord/Münzen oder „Leer") + Löschen-Button; ein Klick lädt den
  Slot, lädt dessen Settings ins `OptionsMenu` und geht ins Hauptmenü.
- `save_slot*.json` ist **gitignored** (lokale Spielerdaten, wie `save.json`).

## Alternatives
- **Ein Save mit Slot-Dict darin:** ein File, mehrere Profile als Keys. Verworfen — getrennte
  Dateien sind robuster (Korruption betrifft nur einen Slot) und einfacher zu löschen.
- **Slot-Parameter durch alle `sd.save`-Aufrufe fädeln:** viel Diff, fehleranfällig. Das
  Aktiv-Slot-Modell hält die Aufrufstellen unverändert.

## Consequences
- **Positiv:** Mehrere parallele Spielstände; minimaler Eingriff in `main.py` (nur Lade-/
  Auswahl-Pfad); saubere Migration; Standard-Defaults inkl. `framerate`/`seen_enemies`.
- **Negativ / Bindung:** Globaler `_active_slot` ist Modulzustand (kein Problem bei einem
  Prozess, aber nicht thread-safe). Settings sind **pro Slot** gespeichert → ein Slot-Wechsel
  lädt dessen Settings (gewollt). `SLOT_SELECT` ist ein weiterer State, der in allen drei
  Phasen behandelt werden muss (Golden Rule 4).
- **Verifikation:** headless Render des Slot-Screens (Slot 1 zeigt migrierte Alt-Daten „Welle
  100", Slot 2/3 „Leer"); voller Treiber Slot→Menü→Spiel→Sieg crashfrei.

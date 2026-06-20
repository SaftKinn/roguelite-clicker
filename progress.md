# progress.md

Wo wir stehen, was als Nächstes kommt. Diese Datei ist die laufende Wahrheit über
den Projektzustand — am Ende jeder Session aktualisieren.

---

## Current focus

Phase 0 abgeschlossen: Doc-System aufgesetzt (CLAUDE.md, architecture.md,
roadmap.md, progress.md, docs/decisions/ mit ADR 001–004). Das Spiel selbst ist
unverändert und spielbar.

## Last session

2026-06-20 — Doc-System per Interview eingerichtet. Vision, Scope, Kern-Mechanik,
Architektur, Roadmap und die vier Grundsatz-Entscheidungen durchgesprochen und
festgeschrieben. Noch kein Spiel-Code geändert.

## Next concrete step

**Phase 1 starten:** `game/balance.py` anlegen und die Tuning-Werte dorthin
verschieben — zuerst die `*_for_wave()`-Funktionen + Konstanten aus `main.py`
(`enemies_for_wave`, `enemy_hp_for_wave`, `enemy_speed_for_wave`,
`coin_value_for_wave`, `BASE_SPAWN_INTERVAL`, Kontaktschaden-Wert).
Spielbalance dabei
NICHT ändern, nur verschieben. Danach In-Run-Upgrade-Werte
(`game/upgrade_menu.py`) und permanente Preise (`game/main_menu.py`).

## Open questions

- **Waffen-Mechanik (Part 2):** Arbeitsannahme „Waffe = anderes Schussverhalten"
  (z. B. Schrot/Laser/Bumerang). Noch nicht final bestätigt.
- **Waffen-Upgrades (Part 2):** Wie genau Waffen im Verbesserungsmenü upgradebar
  sind — offen.
- **Wellen-Skalierung (Phase 2):** Welches genaue Schema macht Welle 100
  erreichbar ohne ~300 Gegner gleichzeitig? (Caps? Spawn-Schübe? gestaffelt?)

## Decision log

Trivia-Entscheidungen (echte Abwägungen → ADR in `docs/decisions/`):

- **D1** — Doku-Sprache: Deutsch (Code-Bezeichner bleiben Englisch).
- **D2** — Projektziel: Lernen mit echter Veröffentlichungs-Absicht später.
- **D3** — Zielplattform: Windows-Desktop `.exe` (z. B. itch.io). Browser/Mac/Linux
  Backlog. (Detail-Begründung in ADR 001.)
- **D4** — Typische Session: mittel, 15–30 Min.
- **D5** — Bestehende CLAUDE.md: technischer Inhalt → `architecture.md`, CLAUDE.md
  wird Ritual-Datei.
- **D6** — Repo-Struktur: Laufzeit-Module in ein `game/`-Package verschoben
  (`main.py` bleibt Root-Einstieg), `tools/` (generate_assets) und `media/clips/`
  ausgegliedert, `.gitignore` ergänzt. Umzug während Phase 0 passiert; Audio-Pfade
  (`assets/audio/` vs. altem `Gamesounds/`) noch nicht final konsolidiert.

## Phase → ADR map

- **Phase 0** (Doc-System) → ADR 001, 002, 003, 004 (alle hier festgehalten).
- **Phase 1** (`game/balance.py`) → ADR 002 (Tuning zentral, JSON später).
- **Phase 2** (Welle 100 + Sieg) → ADR 004 (Run-Modell).
- **Phase 3** (Inhalt) → ADR 002 (neue Werte nach `game/balance.py`), ADR 003 (Struktur).
- **Phase 4** (Verpacken) → ADR 001 (Python/Pygame → PyInstaller).
- **Part 2** (Rebirth/Waffen) → ADR 004.

## Phase status

- **Phase 0 — Doc-System:** ✅ Gate erfüllt (2026-06-20). Nachweis: alle Doc-Dateien
  + ADR 001–004 existieren, Ist-Stand mit Code abgeglichen.
- **Phase 1 — `balance.py`:** offen
- **Phase 2 — Welle 100 + Sieg:** offen
- **Phase 3 — Inhaltszuwachs:** offen
- **Phase 4 — Politur & `.exe`:** offen
- **Part 2 — Rebirth/Waffen:** offen (Backlog)

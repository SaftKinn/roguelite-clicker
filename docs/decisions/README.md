# Architecture Decision Records (ADRs)

Hier lebt die Begründung hinter Entscheidungen, die eine **echte Abwägung** hatten
— damit eine künftige Claude-Instanz (oder ich selbst in drei Monaten) nicht fragt
„warum so und nicht anders?".

## Konvention

- **Eine Datei je Entscheidung**, fortlaufend nummeriert: `NNN-kurz-titel.md`.
- **Nummern werden nie wiederverwendet.** Eine abgelöste Entscheidung wird nicht
  gelöscht, sondern bekommt Status `Superseded by ADR NNN` und bleibt als Historie
  stehen.
- Das **höchstnummerierte File ist Pflichtlektüre beim Session-Start** (siehe
  `CLAUDE.md`).
- **Ein ADR nur bei echter Abwägung** — Faustregel: Würde ein neues Modell in drei
  Monaten fragen „warum so?", gehört es hierher. Trivia-Entscheidungen bleiben als
  Einzeiler im Decision-Log von `progress.md`.

## Format

```markdown
# ADR NNN — Titel
- **Status:** Proposed | Accepted | Superseded by ADR NNN
- **Date:** YYYY-MM-DD
- **Refs:** Decision-Log DX in progress.md, optional architecture.md §Y

## Context
Welches Problem? Welche Constraints (Hardware, Stil, Zeit)?

## Decision
Was wurde gewählt — in einem Satz.

## Alternatives
Was war sonst auf dem Tisch, und warum nicht.

## Consequences
Was folgt daraus — positiv und negativ. Was bindet das für spätere Arbeit?
```

## Index

- [ADR 001 — Engine & Sprache: Python + Pygame](001-engine-python-pygame.md)
- [ADR 002 — Content-Tuning: zentrales Datenmodul jetzt, JSON später](002-tuning-data-modul.md)
- [ADR 003 — Single-File-State-Machine beibehalten](003-single-file-state-machine.md)
- [ADR 004 — Run-Modell: Sieg bei Welle 100, Rebirth als Part 2](004-run-modell-rebirth.md)
- [ADR 005 — Gegner belagern den Turm, statt bei Kontakt zu sterben](005-gegner-belagerung-statt-kontakt-tod.md)
- [ADR 006 — Wellen-Skalierung: Hybrid-Cap (Gesamt + Concurrent) für Welle 100](006-wellen-skalierung-hybrid-cap.md)
- [ADR 007 — ~2h-Rebalance + 1.25x Speed + Kamera-Zoom + größere Sprites](007-zweistunden-rebalance-zoom-speed.md)
- [ADR 008 — XP/Level-System ersetzt Karten-pro-Welle + knackiger/tödlicher Rebalance](008-xp-level-system.md)
- [ADR 009 — Auto-Feuer (Halten) + Angriffstempo-Karte + Lifesteal + steileres Gegner-Scaling](009-autofeuer-angriffstempo-lifesteal.md)
- [ADR 010 — Voll-Auto-Feuer + Autoaim (Wende zum Idle-Tower-Defense)](010-vollauto-feuer-autoaim.md)
- [ADR 011 — Elite-Gegner (10 % Chance, 10× HP)](011-elite-gegner.md)
- [ADR 012 — Gegner-HP super-linear skalieren (gegen multiplikative Spielerkraft)](012-gegner-hp-superlinear.md)
- [ADR 013 — Boss-HP-Multiplikatoren senken (×8/×25 → ×2/×3), datengestützt per Modell](013-boss-hp-multiplikatoren-senken.md)
- [ADR 014 — XP pro Kill skaliert mit der Welle (Wurzel-Fix gegen die Endgame-Wand)](014-xp-wellenskalierung.md)
- [ADR 015 — SuperBoss erhält ein statisches Pixel-Art-Drachen-Sprite](015-superboss-drache-pixel-sprite.md) *(abgelöst von ADR 016)*
- [ADR 016 — SuperBoss-Drache: animiert (zunächst fliegend, dann geerdeter Walk-Zyklus)](016-superboss-drache-flug-animation.md)
- [ADR 017 — Drei neue Gegnerklassen: Goblin (Schwarm), OrcBerserker (Brecher), Necromancer (Beschwörer)](017-neue-gegnerklassen.md)
- [ADR 018 — Boss-Wand als Meta-Gate: ~5 Läufe bis Welle 100 (revidiert ADR 013/014)](018-fuenf-laeufe-meta-gate.md)
- [ADR 019 — Speicherstand-Slots, gewählt vor dem Hauptmenü](019-speicherstand-slots.md)
- [ADR 020 — FPS-Regler + Geschwindigkeits-/Zeitraffer-Multiplikator (Update-Loop ×N)](020-fps-regler-und-zeitraffer.md)
- [ADR 021 — SessionStart-Hook: Projekt-Status automatisch einspeisen](021-sessionstart-status-hook.md)
- [ADR 022 — Gestufter Doppelschuss-Shop + begrenzte Angriffsreichweite + Aufgeben behält Gold](022-shop-doppelschuss-stufig-und-angriffsreichweite.md)
- [ADR 023 — Spawn über ein festes Wandzeit-Fenster (10 s/Welle) statt fixem Intervall](023-spawn-fenster-feste-wandzeit.md)
- [ADR 024 — Tier-Roster: 15 reskinnte Gegner (3 Tiers × 5 Rollen) + Welle 150](024-tier-roster-15-gegner-und-welle-150.md)
- [ADR 025 — Karten-Farbgruppen (ROT/BLAU/GOLD/WEISS) + neue Effekt-Karten](025-karten-farbgruppen-neue-effekte.md)
- [ADR 026 — Shop-Ausbau: neue Dauer-Stats, globale Meta-Multiplikatoren, 4-Gruppen-Layout](026-shop-ausbau-vier-gruppen.md)
- [ADR 027 — Fernkämpfer-Geschosse: eigenes Sprite je Schütze + Mündungs-Flash](027-fernkaempfer-eigene-geschosse-muendungs-fx.md)
- [ADR 028 — XP-Kurve quadratisch: Level 100 kostet ~10000 XP (revidiert ADR 008)](028-xp-kurve-quadratisch.md)

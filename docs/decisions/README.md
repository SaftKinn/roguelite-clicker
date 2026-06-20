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

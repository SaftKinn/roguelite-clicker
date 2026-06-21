# ADR 021 — SessionStart-Hook: Projekt-Status automatisch einspeisen
- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** CLAUDE.md (Session-Ritual); `.claude/settings.json`; `tools/session_status.py`

## Context
Das CLAUDE.md-Ritual verlangt zu Beginn jeder Session: `progress.md` + das neueste
ADR lesen und „wo stehen wir / was als Nächstes" zusammenfassen. Das passiert bisher
manuell. Gewünscht (Nutzer): das **automatisch** bei jedem Session-Start, damit der
Status verlässlich im Kontext liegt, ohne dass Dateien erst gelesen werden müssen.

## Decision
Ein **SessionStart-Hook** (`.claude/settings.json`) führt
`python "$CLAUDE_PROJECT_DIR/tools/session_status.py"` aus; dessen **stdout wird als
Session-Kontext eingespeist**. Das Skript ist read-only, ohne Abhängigkeiten, und gibt
knapp aus: `## Current focus` + `## Next concrete step` aus `progress.md` plus das
höchstnummerierte ADR in `docs/decisions/`.

## Alternatives
- **Echten Agent-Tool-Subagent starten:** technisch nicht möglich — ein Hook führt einen
  **Shell-Befehl** aus, er kann keinen Agentic-Subagent spawnen. Der Shell-Weg liefert den
  Status deterministisch und ohne Subagent-Token-Kosten (ursprünglich als „Subagent in jeder
  Session" angefragt; auf das Machbare/Bessere abgebildet).
- **Reine Memory/Preference:** kann keine automatische Aktion bei einem Event auslösen — dafür
  braucht es zwingend einen Hook.
- **Status in den Hook-Befehl inline (grep/awk):** fragil über Plattformen; ein kleines
  Python-Skript (Python ist die Projektsprache) ist robuster und wartbar (`tools/`).

## Consequences
- **Positiv:** jede neue Session beginnt mit dem Ist-Stand im Kontext → Ritual erfüllt, kein
  manuelles Nachlesen; deterministisch, 0 Subagent-Kosten; das Skript ist auch manuell nützlich
  (`python tools/session_status.py`).
- **Negativ / Bindung:** Da `.claude/settings.json` neu angelegt wurde, greift der Hook evtl.
  erst nach einmaligem `/hooks`-Öffnen oder Neustart (Settings-Watcher). Der Status ist nur so
  gut wie `progress.md` gepflegt ist. `$CLAUDE_PROJECT_DIR` muss gesetzt sein (ist es im
  Hook-Kontext).
- **Verifikation:** `settings.json` JSON-valide (Python-Parse); der Hook-Befehl liefert den
  erwarteten Status-Block (mit gesetztem `CLAUDE_PROJECT_DIR` getestet).

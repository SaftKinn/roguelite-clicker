# ADR 023 — Spawn über ein festes Wandzeit-Fenster (10 s/Welle) statt fixem Intervall
- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** ersetzt das Spawn-Floor-Modell aus ADR 007/008; `game/balance.py`, `main.py`

## Context
Nutzerwunsch: „Lass eine Welle 10 Sekunden dauern — bis dahin müssen alle Gegner
gespawnt sein." Bisher war das Spawn-Intervall **fix** (`BASE_SPAWN_INTERVAL = 60`
Ticks + `diff_mod["spawn_bonus"]`), also frame-/tick-basiert. Zwei Probleme:
1. **Nicht FPS-stabil:** Mit dem FPS-Regler (ADR 020, 30–240) wurde dasselbe 60-Tick-
   Intervall real unterschiedlich lang — bei FPS 140 spawnte eine Welle doppelt so
   schnell wie bei FPS 75. Das Fenster war keine echte Wandzeit.
2. **Kein definiertes Fenster:** Die Gesamt-Spawndauer hing an Gegnerzahl × fixem
   Intervall und schwankte je Welle (W5 anders als W99), ohne Ziel-Sekundenwert.

## Decision
Spawn-Intervall wird **dynamisch aus einem Ziel-Wandzeit-Fenster** berechnet:
`spawn_interval_ticks(wave, fps)` in `game/balance.py` gibt
`round(WAVE_SPAWN_SECONDS × fps / enemies_for_wave(wave))` zurück (`WAVE_SPAWN_SECONDS = 10.0`).
- An die **Live-FPS** (`options_menu.fps_value`) gekoppelt → das Fenster bleibt echte
  10 Sekunden, egal wie der FPS-Regler steht. Dieselbe Größe taktet schon `fire_timer`.
- Da der `spawn_timer` bei 0 startet, erscheint der **letzte** der N Gegner bei
  N×Intervall → genau am Fenster-Ende (~10 s); der erste nach 10/N s (~0,3 s bei 30, unmerklich).
- **Bosswellen** (`enemies_for_wave % 10 == 0` → N=1): Sonderfall `n<=1 → 1 Tick`, sonst
  würde der einzelne Boss erst nach 10 s leeren Felds erscheinen.
- `diff_mod["spawn_bonus"]` bleibt als additiver Frame-Nudge je Schwierigkeit erhalten
  (`max(1, … + spawn_bonus)`); auf „Normal" (0) trifft das Fenster exakt 10 s.
- Berechnung in `main.py` in den `if state == "PLAYING"`-Block verschoben (braucht `gs["wave"]`,
  das im Menü `None` ist). `BASE_SPAWN_INTERVAL` ist jetzt nur noch Alt-Doku in `balance.py`.

## Alternatives
- **Fixes Intervall an FPS koppeln** (Ticks = Sekunden×fps, aber Wert pro Spawn fix): hätte
  Problem 1 gelöst, aber nicht das definierte 10-s-Fenster geliefert (Gesamtdauer bliebe
  gegnerzahl-abhängig). Verworfen — Nutzer wollte explizit „die ganze Welle in 10 s".
- **Spawn-Floor als Spielzeit-Rückgrat behalten** (ADR 007): widerspricht dem Wunsch direkt;
  die Lauflänge wird jetzt bewusst von der HP-Kurve × Spielerkraft getragen, nicht von
  gestreckten Spawns.

## Consequences
- **Positiv:** Vorhersagbares, FPS-stabiles Pacing; jede Welle ist nach ~10 s voll auf dem
  Feld; Bosse erscheinen sofort; ein einziger Regler (`WAVE_SPAWN_SECONDS`).
- **Negativ / Bindung:**
  - **Spielzeit-Modell verschoben:** Das in `balance.py` dokumentierte „2-Stunden-Rückgrat"
    (Spawn-Floor) gilt nicht mehr — Lauflänge = wie schnell geräumt wird. Endgame-Balance
    (Welle 100) ist neu zu beobachten; der bisherige Spawn-Floor-Schutz fällt weg.
  - **Concurrent-Cap kann das Fenster dehnen:** `MAX_CONCURRENT_ENEMIES` (30) pausiert Spawns,
    wenn der Spieler nicht schnell genug räumt → dann dauert es länger als 10 s, bis alle
    da sind. Inhärent, dokumentiert im Helper-Docstring.
  - **`spawn_bonus` weitgehend kosmetisch:** ±25–30 Frames sind bei FPS 140 ~0,2 s; die
    Schwierigkeit wirkt fast nur noch über `hp_mult`.
- **Verifikation:** Deterministische Simulation der echten Spawn-Schleife (Timer 0, +1/Tick,
  Spawn bei ≥Intervall) für W1/5/99 bei FPS 75 **und** 140 → letzter Spawn jeweils ~10,0 s,
  alle N gespawnt; Bosswellen ~0,01 s. Voller Treiber-Flow lief crashfrei (NoneType-Fix
  bestätigt). Hinweis: der Headless-Treiber kam diesmal nicht über das Menü hinaus
  (separater, paralleler Menü-Flow-Bruch) — der PLAYING-Pfad wurde daher per Simulation,
  nicht per Screenshot geprüft.

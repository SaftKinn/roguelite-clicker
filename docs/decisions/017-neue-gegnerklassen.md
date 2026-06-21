# ADR 017 — Drei neue Gegnerklassen: Goblin, OrcBerserker, Necromancer
- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** architecture.md §4 (Gegnertypen) + §5 (Spawn-Gewichtung); progress.md D30

## Context
Phase 3 braucht Inhaltszuwachs, und eine offene Frage war „woher kommt der
Gegnerdruck / die Build-Tiefe?" (progress.md, Genre-Identität). Das bestehende
Roster — Warrior/Archer/Lancer/Monk — deckt Standard-Nahkampf, Fernkampf, Tank und
Heiler ab, aber es fehlten **Massendruck** (viele schwache Gegner), ein **reiner
Brecher** (zwingt DPS-Konzentration ohne den Elite-Zufall) und ein **offensiver
Support** als Gegenstück zum Heiler-Monk. Der Nutzer will die Sprites selbst per
Leonardo Phoenix (→ AutoSprite → `assets/custom/`) erzeugen; die Klassen sollen
**vor** den fertigen Sprites stehen und sofort spielbar sein (Golden Rule 5).

## Decision
Drei neue Klassen, jede subklasst `Warrior` mit eigenem `_frames_r/_frames_l`-Cache,
`_load_sprites()` mit `try/except`-Fallback und Einhängung in `spawn_enemy_for_wave()`:

- **`Goblin`** (Spawn-Key „goblin") — Schwarm-Rusher: `speed ×1.6`, `hp ×0.25`,
  `coin_value 1`. Nur Lauf-Animation, kein eigener Angriff (`_atk*`-Listen leer →
  Warrior überspringt den Attack-Zweig, Nahkampf läuft trotzdem über `melee_attack`).
- **`OrcBerserker`** (Spawn-Key „orc") — Brecher: `speed ×0.5`, `hp ×2.5`,
  `coin_value 4`, doppelter Nahkampfschaden über benannte Konstante `DAMAGE_MULT=2`
  (`self.ATTACK_DAMAGE = balance.ATTACK_DAMAGE * DAMAGE_MULT`). Nutzt die schon
  angelegten `orc_warrior`-Loader (run + attack); eine Angriffsanim für beide
  Alternierungs-Slots.
- **`Necromancer`** (Spawn-Key „necro") — Beschwörer: bleibt wie der Monk auf
  `ATTACK_RANGE`-Distanz; `speed ×0.9`, `hp ×0.6`, `coin_value 4`. Ruft alle
  `SUMMON_EVERY` Ticks `SUMMON_COUNT` Goblins, lebenslang gedeckelt durch `SUMMON_MAX`.
  `main.py` holt sie via `pop_summons()` (analog `Archer.pop_shots()`) und hängt sie
  **nach** der Update-Schleife an `gs["enemies"]` an — nie während der Iteration.

Spawn-Gewichtung in `spawn_enemy_for_wave()` welleabhängig erweitert: Goblins ab
Welle 5, Ork-Berserker ab Welle 8, Nekromanten ab Welle 12. Bestehende Spawn-Keys
„rusher"/„tanker" bleiben unverändert (D7).

## Alternatives
- **Pro-Typ-Tuning in `balance.py` statt inline:** Die bestehenden Klassen
  (Lancer ×3.0, Archer ×0.4, Monk ×0.6) halten ihre Multiplikatoren inline im
  `__init__`; rein **behaviorale** Parameter stehen als Klassenkonstanten (wie Monks
  `HEAL_EVERY/_AMOUNT/_COUNT`). Dem Muster gefolgt: HP/Speed-Faktoren inline, das
  Beschwör-Verhalten (`SUMMON_*`) + `DAMAGE_MULT` als benannte Konstanten (Golden
  Rule 2 erfüllt, ohne `balance.py` mit Werten zu fluten, die das Umfeld inline hält).
- **Goblin-Schwarm als Mehrfach-Spawn pro Tick:** `spawn_enemy_for_wave()` gibt genau
  einen Gegner zurück; statt diese Signatur zu brechen, erzeugt eine **hohe
  Spawn-Gewichtung** den Schwarm-Effekt — billiger und respektiert Concurrent-Cap.
- **Necromancer-Summons direkt in `gs["enemies"]` schieben:** würde die Liste während
  der `for e in gs["enemies"]`-Iteration mutieren (Bug). Stattdessen sammeln +
  nachträglich `+=` (gleiches Muster wie Archer-Pfeile).
- **Auf die Sprites warten:** verworfen — der Fallback (Golden Rule 5) macht die
  Klassen sofort spielbar; die Sprites droppt der Nutzer später ohne Code-Änderung rein.

## Consequences
- **Positiv:** drei klar unterscheidbare Rollen (Masse / Brecher / Beschwörer) füllen
  die Druck-/Build-Tiefe-Lücke; jede ist über benannte Konstanten tunebar; das
  Spiel läuft schon vor den Sprites (gezeichnete Fallback-Primitive).
- **Negativ / Bindung:**
  - **Balance ist ungetestet** — die Multiplikatoren (×0.25/×2.5/×0.6) und die
    Spawn-Gewichte sind ein erster Wurf. Insbesondere greift das **Balance-Modell**
    (`tools/balance_model.py`) die neuen Typen/Beschwörungen **noch nicht** auf; der
    echte 1→100-Lauf (next step) muss zeigen, ob die Mischung trägt.
  - **Necromancer-Beschwörungen umgehen `MAX_CONCURRENT_ENEMIES`** (kommen aus der
    Update-Schleife, nicht aus dem Spawn-Gate). Pro Nekromant durch `SUMMON_MAX=6`
    gedeckelt, aber mehrere Nekromanten können die Gegnerzahl über den Cap treiben —
    Perf-/Belagerungs-DPS-Risiko, falls der Necro-Anteil zu hoch wird.
  - **Sprites fehlen noch** — bis die PNGs in `assets/custom/` liegen, rendern alle
    drei als Fallback-Kreise (kein Crash, aber optisch Platzhalter).
- **Verifikation:** `py_compile` aller drei Dateien OK; Headless-Unit-Test bestätigt
  Stats (Goblin hp×0.25/speed×1.6, Orc hp×2.5/dmg=2×, Necro hp×0.6 + Beschwörung
  feuert), Draw-Fallback crashfrei; voller Spiel-Loop (Treiber, Welle 49) crashfrei
  mit aktiver Spawn-Tabelle + Necromancer-Beschwörungen.

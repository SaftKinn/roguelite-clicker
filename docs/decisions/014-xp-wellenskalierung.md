# ADR 014 — XP pro Kill skaliert mit der Welle (Wurzel-Fix gegen die Endgame-Wand)
- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** architecture.md §6, §11; progress.md D27; baut auf ADR 013 (Boss-Multiplikatoren)
  und ADR 008 (XP/Level-System) auf; Werkzeug: `tools/balance_model.py`

## Context
ADR 013 senkte die Boss-Multiplikatoren, ließ aber W60–W100 für frische Spieler hart
(9/10 Bosse über dem Walk-Budget). Das Balance-Modell wies die Wurzel nach: **Kill-XP war
flach.** `gs["xp"] += enemy.coin_value` gab nur die Klassen-Basis (1/3, ×5 Elite),
unabhängig von der Welle — während `xp_to_next` mit Stufe *und* Welle wächst und die
Gegner-HP super-linear (ADR 012) steigt. Folge: Das Hochleveln bremste spät massiv aus,
der Spieler blieb auf Welle 100 bei **~Level 33** mit ~870 Einzelziel-DPS — viel zu wenig
gegen die späten Bosse. (Inkonsequenz: die *Münzen* skalieren längst mit der Welle über
`coin_value_for_wave`, die XP nicht.)

## Decision
- Kill-XP mit der Welle skalieren, analog zu den Münzen, aber **gedämpft**:
  `gs["xp"] += enemy.coin_value * xp_wave_mult(wave)` mit `xp_wave_mult = 1 + wave//XP_WAVE_DIV`
  und `XP_WAVE_DIV = 8` (neue Konstante + Funktion in `balance.py`).
- Gedämpft heißt: schwächer als der Münzfaktor (`coin_value_for_wave = 1 + wave//3`). Der
  volle Münzfaktor hätte den Spieler auf ~Level 164 getrieben (Bosse in 1–2 s tot, Endgame
  trivial). `//8` landet ihn im Modell bei ~Level 98 — **0/10 Bosse über dem Walk-Budget**,
  TTKs knapp darunter (W90 4,3 s / Budget 4,7 s; W100 6,5 s / Budget 8,2 s) = spannend, nicht
  gratis. Welle 1–7 bleibt unverändert (Faktor 1), das frühe Spiel wird nicht angefasst.
- HP-Seite (`ENEMY_HP_PER_WAVE_SQ`) bleibt unverändert — bewusst der **eine** Hebel.

## Alternatives
- **Nur `ENEMY_HP_PER_WAVE_SQ` senken (Lever A):** Modell zeigte, selbst SQ 0,9→0,3 lässt
  5/10 Bosse über Budget und weicht nebenbei das ganze Midgame-Trash auf. Behandelt das
  Symptom (HP), nicht die Wurzel (Spieler-DPS/Level).
- **Voller Münzfaktor (`//3`):** überschießt → Level 164, triviales Endgame.
- **HP-lastige Combos (gedämpftes B + SQ runter):** z. B. `//20 + SQ 0,4` → Endlevel ~61,
  mehr Build-Vielfalt, aber zwei gekoppelte Regler und ein weicheres Midgame. Bewusst
  zugunsten des einfacheren Ein-Hebel-Fixes verworfen.

## Consequences
- **Positiv:** W60–W100 sind für einen frischen 1→100-Spieler fair (alle Bosse im Budget),
  ohne die HP-Kurve oder das frühe Spiel anzufassen. Ein Regler (`XP_WAVE_DIV`).
- **Negativ / Bindung:** **Level-Inflation** — der Spieler endet ~Level 98 statt 33. Bei
  ~97 Kartenpicks bekommt man fast alle Upgrades → die Build-*Entscheidung* verwässert
  (architecture.md §1 nennt Build-Tiefe als Kern). Bewusst akzeptiert für den einfachen Fix;
  falls sich der Lauf zu sehr nach „alles mitnehmen" anfühlt, ist der Gegen-Hebel ein
  HP-lastigeres Re-Tuning (größeres `XP_WAVE_DIV` + niedrigeres `ENEMY_HP_PER_WAVE_SQ`) oder
  mehr DPS *pro* Level statt mehr Level.
- **Zahlen = Modellprognose, nicht gespielt.** Der echte 1→100-Lauf muss bestätigen, dass
  ~Level 98 sich gut anfühlt und die Boss-TTKs real ins Budget passen.
- **Verifikation:** `xp_wave_mult` headless geprüft (W1–7 ×1, W100 ×13); Modell bestätigt
  0/10 Bosse über Budget; voller Headless-Treiber-Flow (Menü→Lauf→F4→Welle 100/SuperBoss→
  Sieg) crashfrei.

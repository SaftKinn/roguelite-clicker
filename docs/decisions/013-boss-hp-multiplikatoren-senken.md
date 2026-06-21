# ADR 013 — Boss-HP-Multiplikatoren senken (×8/×25 → ×2/×3)
- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** architecture.md §6, §11; progress.md D26; revidiert ADR 012 (dort blieben die
  Multiplikatoren bewusst unverändert); Werkzeug: `tools/balance_model.py`

## Context
ADR 012 machte die Gegner-Basis-HP super-linear (quadratischer Term), ließ die Boss-HP-
Multiplikatoren in `enemy.py` (`Boss ×8`, `SuperBoss ×25`) aber **bewusst unverändert** —
mit der Annahme, ein echter Welle-100-Spieler sei „Level ~60+". Diese Annahme wurde nie
gegen den Code geprüft.

Ein read-only Balance-Modell (`tools/balance_model.py`, importiert `game/balance.py` und
spiegelt die Spawn-/Stat-Mechanik) hat zwei Dinge mit Zahlen widerlegt:

1. **Der Spieler erreicht auf W100 nur ~Level 33, nicht 60+.** XP pro Kill ist der
   Klassen-Basiswert `enemy.coin_value` (1/3, ×5 Elite) und skaliert **nicht** mit der
   Welle (`main.py`), während `xp_to_next` mit Stufe *und* Welle wächst → das Hochleveln
   bremst spät massiv. Reale Einzelziel-DPS auf W100 ≈ 870 (fresh).
2. **Der Bosskampf ist ein DPS-Rennen gegen die Anlaufzeit, nicht gegen die HP des
   Spielers.** Bosse one-shotten bei Kontakt (`check_enemy_contact` → `take_damage(max_hp)`)
   und der Turm ist stationär. Walk-Budget Rand→Mitte: ~5 s (Boss) / ~8 s (SuperBoss) bei
   FPS 75. Gegen dieses Budget waren die alten Multiplikatoren brutal: W100-SuperBoss
   255.750 HP → **TTK ~294 s** (fresh), W50-SuperBoss ~140 s. Unfaire Wand schon ab ~W40.

## Decision
- Boss-HP-Multiplikatoren als **benannte Konstanten** nach `game/balance.py` ziehen
  (`BOSS_HP_MULT`, `SUPERBOSS_HP_MULT`; Golden Rule 2 — vorher Magic Numbers in `enemy.py`)
  und von ×8/×25 auf **×2/×3** senken.
- Damit: SuperBoss W100 30.690 HP (war 255.750), Boss W90 16.800 (war 67.200). Die
  super-lineare Basis (ADR 012) bleibt unangetastet; nur der doppelt zählende Boss-Aufschlag
  fällt.

## Alternatives
- **Nur `ENEMY_HP_PER_WAVE_SQ` senken:** trifft auch die normalen Gegner/Elites und lässt
  die Boss-spezifische Doppelzählung stehen. Hier ging es gezielt um die Boss-Wand.
- **XP-Kurve fixen (mehr Level → mehr DPS):** behebt die *Wurzel* (langsames Leveln), ist
  aber ein größerer Eingriff in die Progression. Bewusst für eine spätere Session offen
  gelassen; dieser Change ist der gezielte, risikoarme erste Schritt.
- **Multishot/Durchschlag gegen Einzelziele wirksam machen:** würde mehr Karten zur Boss-
  DPS beitragen lassen (aktuell zählen gegen den Einzel-Boss nur `damage` + `attackspeed`),
  ist aber eine Design-Änderung am Schussverhalten — separat zu entscheiden.

## Consequences
- **Positiv:** Bosse W10–W50 sind wieder im oder nahe am Walk-Budget; die SuperBoss-Wand
  W100 fällt von TTK ~294 s auf ~35 s (fresh) bzw. ~27 s (mit etwas Gear).
- **Negativ / offen:** Das Modell zeigt, dass **W60–W100 für einen *frischen* Spieler
  weiter unfair** bleiben — dort liegt der „faire" Boss-Multiplikator rechnerisch unter 1,
  d.h. der quadratische Basis-HP allein sprengt schon das Budget. Das vollständig fair zu
  machen braucht einen **zweiten Hebel** (`ENEMY_HP_PER_WAVE_SQ` runter und/oder XP-Kurve).
  Bewusst aufgeschoben.
- **Verifikation:** Boss-HP headless gegen die Konstanten geprüft (W100-SuperBoss 30.690 =
  10.230 × 3); voller Headless-Treiber-Flow (Menü → Lauf → F4 → Welle 100/SuperBoss → Sieg)
  läuft crashfrei. Endgültige Balance per echtem 1→100-Playtest offen.

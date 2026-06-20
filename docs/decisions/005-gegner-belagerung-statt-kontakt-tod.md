# ADR 005 — Gegner belagern den Turm, statt bei Kontakt zu sterben
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** Decision-Log in progress.md (D8); architecture.md §4, §5

## Context
Bisher tötete `check_enemy_contact()` einen Gegner beim Berühren des Turms und zog
dem Spieler einmalig Schaden ab (`enemy.alive = False`). Folge: Gegner konnten sich
durch Hineinlaufen **selbst entfernen** — der Spieler musste sie nicht zwingend
erschießen, und eine Welle konnte teils „von allein" leerlaufen. Das widerspricht
dem Tower-Defense-Kern (`architecture.md`: der Spieler ist ein Turm, der Gegner
**abwehren** muss). Gewünscht: Nahkämpfer halten vor dem Turm an, greifen wiederholt
an, und nur die Geschosse des Spielers töten sie.

## Decision
Nahkämpfer (`Warrior`, `Lancer` und die davon erbenden `Boss`/`SuperBoss`) **stoppen
vor dem Turm** (`stop_dist = _PLAYER_RADIUS + self.radius` in `Warrior.update()`) und
**greifen auf Cooldown an** (`melee_attack()` → `ATTACK_DAMAGE` alle `ATTACK_COOLDOWN`
Ticks). **Kontakt tötet den Gegner nicht mehr** — `check_enemy_contact()` setzt kein
`alive = False` mehr; ausschließlich `check_projectile_hits()` tötet Gegner. Eine
Welle gilt damit erst als geräumt, wenn der Spieler alle Gegner erschossen hat.
Boss/SuperBoss bleiben bei Berührung sofort tödlich (One-Hit, aber sie sterben dabei
selbst nicht). Die Fernkämpfer (`Archer`, `Monk`) sind unberührt — sie überschreiben
`update()` und halten bereits bei `ATTACK_RANGE` an.

## Alternatives
- **Kontakt-Tod beibehalten:** minimaler Code, aber kein echter Abwehr-Druck —
  Gegner räumen sich selbst, Zielen wird optional. Verworfen, da gegen die Vision.
- **Schaden über Aura/Damage-over-Time statt diskreter Cooldown-Treffer:** weicher,
  aber schwerer lesbar (kein klarer „Treffer-Takt") und unnötig für den jetzigen
  Bedarf.
- **Schaden an einen Animations-Hit-Frame koppeln** (wie beim Archer-Release):
  visuell exakter, aber mehr Aufwand pro Gegnerklasse. Zurückgestellt — kann später
  nachgezogen werden, ohne diese Entscheidung zu kippen.

## Consequences
- **Positiv:** Echter Tower-Defense-Druck — der Spieler **muss** Gegner töten. Schaden
  skaliert natürlich mit der Zahl der Belagerer (per-Gegner-Cooldown), Wellen enden
  nur durch aktives Spielen.
- **Negativ / Bindung:** Gegner stauen sich jetzt am Turm; Überrenn-Gefahr steigt.
  `ATTACK_DAMAGE`/`ATTACK_COOLDOWN` und die Wellengrößen brauchen Balancing — das
  hängt direkt an der offenen Frage zur Wellen-Skalierung (Phase 2) und die Werte
  gehören perspektivisch nach `game/balance.py` (Phase 1, ADR 002). Bis dahin liegen
  sie als Modulkonstanten in `game/enemy.py` bzw. `MELEE_REACH` in `main.py`.

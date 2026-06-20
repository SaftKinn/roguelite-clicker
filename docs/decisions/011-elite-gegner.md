# ADR 011 — Elite-Gegner (10 % Chance, 10× HP, egal welcher Typ)
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** architecture.md §5; progress.md D21

## Context
Nach der Wende zum passiven Auto-Feuer (ADR 010) fehlte ein Spannungsmoment innerhalb
einer Welle — alle Gegner eines Typs sind gleich zäh und sterben im selben Takt.
Gewünscht: gelegentliche **zähe Brocken**, die den Spieler zwingen, Feuerkraft auf ein
Ziel zu konzentrieren — unabhängig vom Gegnertyp.

## Decision
- **Elite = jeder Nicht-Boss-Gegner mit `ELITE_HP_MULT = 10`-facher HP.** Beim Spawn
  würfelt `spawn_enemy_for_wave()` mit `ELITE_SPAWN_CHANCE = 0.10`; trifft es, wird
  `enemy.max_hp *= 10`, `enemy.hp = max_hp`, `enemy.elite = True`.
- **Typ-relativ:** Die Multiplikation greift **nach** der typ-spezifischen HP-Skalierung
  (Archer ×0.4, Lancer ×3.0, Monk ×0.6, Warrior ×1.0) — ein Lancer-Elite ist also
  deutlich zäher als ein Archer-Elite, „10×" wirkt konsistent pro Typ.
- **Bosse ausgenommen:** Der Würfel sitzt im Nicht-Boss-Zweig (nach den `wave % 10/50`-
  Returns) — Boss/SuperBoss werden nie Elite (deren HP ist ohnehin extrem).
- **Reward skaliert:** `enemy.coin_value *= ELITE_REWARD_MULT` (×5). Da `coin_value`
  sowohl Münzen (`coin_value_for_wave × coin_value × gold_mult`) als auch den XP-Drop
  speist, gibt ein Elite konsistent ×5 Münzen **und** XP — ein Regler für beides.
- **Sichtbar:** roter Ring (`ELITE_COLOR`) um den Gegner in der Draw-Schleife, damit der
  zähe Brocken nicht wie ein Bug („stirbt nicht") wirkt.
- **Robustheit:** `elite = False` ist **Klassenattribut** auf `Warrior` — alle fünf
  Subklassen erben es, ohne dass ein `__init__` angefasst werden muss (Golden Rule 5).

## Alternatives
- **Eigene Elite-Klasse je Gegnertyp:** viel Boilerplate für denselben Effekt. Ein
  Laufzeit-Flag + HP-Faktor ist schlanker und „egal welcher Typ".
- **Elite mit eigenem Sprite/Tint statt Ring:** mehr Render-Arbeit pro Klasse; der Ring
  ist typ-unabhängig und sofort erkennbar. Tint als spätere Politur offen.
- **Reward über die HP linear (×10) skalieren:** gewählt wurde **×5** (`ELITE_REWARD_MULT`),
  nicht ×10 — voller HP-proportionaler XP-Drop würde die Anti-Snowball-XP-Kurve (ADR 010/
  D22) wieder aushebeln. ×5 macht Elites lohnend, ohne das Leveling zu überfüttern.

## Consequences
- **Positiv:** Mikro-Spannung pro Welle ohne neue Gegnertypen; ein einziger Regler
  (`ELITE_SPAWN_CHANCE`) steuert die Häufigkeit, ein zweiter (`ELITE_HP_MULT`) die Härte.
- **Negativ / Bindung:** Reward (×5) vs. HP (×10) ist eine Balance-Wette — zu niedrig
  fühlt sich der Elite nach „Bremsklotz", zu hoch nach XP-Jackpot an, der die
  Anti-Snowball-Kurve aushebelt. `ELITE_REWARD_MULT` ist der Playtest-Regler dafür. Bei
  hoher `attack_speed` + Pierce/Multishot können Elites trotzdem schnell fallen — Härte
  per Playtest gegen die Spieler-DPS kalibrieren.
- **Verifikation:** Headless geprüft — Spawnrate ~0.103 über 4000 Spawns, HP = 10× der
  typ-spezifischen HP, Boss-Wellen elite-frei; Elite-Ring deterministisch gerendert.

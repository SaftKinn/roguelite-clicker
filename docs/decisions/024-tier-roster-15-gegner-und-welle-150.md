# ADR 024 — Tier-Roster: 15 reskinnte Gegner (3 Tiers × 5 Rollen) + Welle 150

- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** `game/enemy.py`, `main.py` (`spawn_enemy_for_wave`, `TIER_ROSTER`),
  `game/sprite_loader.py` (`load_custom_enemy`), `game/main_menu.py` (Lexikon + Scroll),
  `game/balance.py` (`WIN_WAVE`); baut auf ADR 017 (3 Gegnerklassen) + Golden Rule 5 (Asset-Fallback)

## Context
Nutzerwunsch: deutlich mehr Gegner-Optik und das Spiel **bis Welle 150** verlängern
(vorher `WIN_WAVE = 100`). Konkret 15 neue Sprite-PNGs, strukturiert als **3 Wellen-
Abschnitte × 5 Archetypen** mit eskalierendem Thema (Untote → Dämonen → Drachen-Brut)
und einheitlichem Tiny-Swords-Stil (beseitigt den Pixel/Tiny-Swords-Bruch). Die PNGs
werden extern (Leonardo.ai) erzeugt — der Code muss **vor** den Bildern stabil laufen.

Spannungsfeld: 15 vollwertige Gegnerklassen wären viel Code und würden die schon
getunte Rollen-Balance (Spawn-Gewichte, HP-Faktoren, Schuss-/Summon-Mechanik) duplizieren.

## Decision
**Reskin durch Vererbung statt Neuimplementierung.** Die 5 Archetypen erben 1:1 die
Mechanik der bestehenden Rollen-Klassen; pro Tier wird nur Optik + Fallback-Farbe getauscht:

| Rolle | Basisklasse | Tier 1 (Untote) | Tier 2 (Dämonen) | Tier 3 (Drachen) | px |
|---|---|---|---|---|---|
| Nahkampf | `Warrior` | SkeletonWarrior | ImpWarrior | DrakeWarrior | 50 |
| Schwarm | `Goblin` | BoneSwarmling | Hellhound | Wyrmling | 40 |
| Fernkampf | `Archer` | SkeletonArcher | DemonCaster | DrakeArcher | 48 |
| Tank | `OrcBerserker` | BoneColossus | PitBrute | ScaleTitan | 60 |
| Beschwörer | `Necromancer` | Lich | DemonSummoner | DragonPriest | 48 |

- **`_CustomSpriteMixin`** (in `enemy.py`): überschreibt nur `_load_sprites()` →
  `sprite_loader.load_custom_enemy(SPRITE_NAME, SPRITE_PX)` lädt `assets/custom/<name>_run.png`.
  Fehlt das PNG → `except` → leere Frames → gezeichnetes Primitiv in Tier-Farbe (Golden Rule 5).
  Die Sprites entstehen per `tools/animate_walk.py` aus **einem** Standbild (wie der Drache).
- **`TIER_ROSTER`** (in `main.py`): `[{rolle: klasse}, …]` je 50-Wellen-Abschnitt;
  `tier_for_wave(wave) = min((wave-1)//50, 2)`. `spawn_enemy_for_wave` behält die
  **bestehenden Rollen-Gewichte** und wählt nur die konkrete Klasse per Tier — Balance unverändert.
- **`tanker` (Lancer) und `monk` (Monk)** bleiben über alle Tiers ihr Tiny-Swords-Original
  (keine 6./7. Reskin-Achse nötig; passt stilistisch zum Tiny-Swords-Ziel).
- **`Necromancer.SUMMON_CLASS`**-Hook (Default `Goblin`): Beschwörer rufen ihren Tier-Schwarm
  (Lich→BoneSwarmling, DemonSummoner→Hellhound, DragonPriest→Wyrmling).
- **Welle 150:** `WIN_WAVE 100→150`. SuperBoss feuert weiter bei `wave % 50 == 0` (50/100/150).
  Siegestext und Dev-Taste **F4** referenzieren jetzt `WIN_WAVE` statt hartkodierter 100/99.
- **Lexikon-Scroll:** 24 Einträge sprengen den Schirm (8 Reihen) → `BestiaryMenu` bekam
  Mausrad-Scrolling (`scroll()`, Offset in `_card_rect`, Kopf-/Fußband-Maske, Sichtfenster-Cull).

## Alternatives
- **15 eigenständige Gegnerklassen:** maximale Flexibilität, aber dupliziert Mechanik/Balance
  und ~10× mehr Code. Verworfen — die Rollen sind bewährt; gewollt ist Reskin, keine neue Mechanik.
- **Tiers additiv statt ersetzend** (alte + neue Gegner mischen): hätte die thematische
  Abschnitts-Identität verwässert und die Spawn-Gewichte aufgebläht. Verworfen.
- **Lexikon-Layout schrumpfen statt scrollen** (kleinere Karten/4 Spalten): 8 Reihen passen
  trotzdem nicht; Scroll ist die robuste Lösung und skaliert für künftige Gegner.

## Consequences
- **Positiv:** 15 Gegner für ~120 Zeilen; Balance/Mechanik unangetastet; Bild-Erzeugung
  komplett vom Code entkoppelt (Fallback-Kreise sofort spielbar); Welle-100-Inhalte
  bleiben als Tier 2 erhalten, Tier 3 ist neu.
- **Bindung / offen:**
  - **Originale Warrior/Archer/Goblin/Orc/Necro spawnen nicht mehr direkt** (nur noch als
    Basisklassen + via `SUMMON_CLASS`-Default). Sie bleiben im Lexikon, werden aber im
    normalen Lauf nicht mehr „gesehen". Bewusst akzeptiert.
  - **Welle 101–150 ist ungetestet-balanciert:** HP-Formel (quadratischer Term) skaliert
    weiter, `enemies_for_wave` cappt bei 30, Speed bei 2,4 → Tier 3 könnte HP-Wand statt
    DPS-Rennen werden. Gegen-Hebel: `ENEMY_HP_PER_WAVE_SQ` / eine Tier-3-Härte.
  - **15 fehlende PNGs:** bis Leonardo liefert, sind alle Tier-Gegner farbige Kreise
    (Konsolen-Warnungen je fehlendem `_run.png` — harmlos).
- **Verifikation:** `py_compile` aller 5 Dateien ok. Headless-Instanziierung aller 15 Klassen
  → korrekte vererbte Stats (Tank ×25 HP, Schwarm ×2,5/×1,6 Speed, Fernkampf ×0,4) + Summon-
  Hooks. Voller Treiber-Flow crashfrei bis **Sieg „SuperBoss in Welle 150 bezwungen"**.
  Lexikon mit 24 Einträgen oben + ganz unten gerendert: alle erreichbar, Maske sauber.

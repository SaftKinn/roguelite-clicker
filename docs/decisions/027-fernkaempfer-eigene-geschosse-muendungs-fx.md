# ADR 027 — Fernkämpfer-Geschosse: eigenes Sprite je Schütze + Mündungs-Flash

- **Status:** Accepted
- **Date:** 2026-06-22
- **Refs:** `game/enemy.py` (`EnemyProjectile`, `Archer`, `Necromancer`), `game/sprite_loader.py`; baut auf ADR 024 (Tier-Reskins, `SPRITE_NAME`-Konvention) auf

## Context
Bisher feuerten **alle** Fernkämpfer (Archer + Necromancer und ihre 6 Tier-Reskins)
dasselbe `EnemyProjectile` — einen einzigen golden-braunen Tiny-Swords-Pfeil
(`load_arrow(20)`). Optisch war Tier 1/2/3-Fernkampf nicht unterscheidbar (der Lich
„schoss" denselben Pfeil wie der Feuer-Dämon). Der Nutzer wollte je spawnendem
Fernkämpfer ein eigenes, thematisch passendes Geschoss **plus** einen kurzen
Abschuss-/Cast-Flash (Mündungs-FX). Externe PNGs entstehen via Leonardo.ai
(Prompt-Kit im Plan-File `ich-m-chte-f-r-die-twinkling-candy`).

## Decision
1. **Geschoss-Sprite aus `SPRITE_NAME`-Konvention abgeleitet** (kein neues Klassen-
   attribut): Schützen reichen `sprite=getattr(self, "SPRITE_NAME", None)` ans
   `EnemyProjectile`. Die 6 Tier-Reskins haben `SPRITE_NAME` schon (ADR 024) → keine
   Änderung an den Klassen nötig. Dateien analog `<name>_run.png`:
   `assets/custom/<name>_shot.png` (Geschoss, blickt RECHTS, wird zur Flugrichtung
   rotiert) und `<name>_cast.png` (radialer Mündungs-Flash). Loader
   `sprite_loader.load_enemy_shot` / `load_enemy_muzzle` über Helfer `_load_single`
   (Einzel-PNG, auf opake Pixel zugeschnitten — Muster wie `load_cannonball`).
2. **Mündungs-Flash an die Projektil-Lebenszeit gekoppelt** (statt eigener `gs`-FX-
   Liste): `EnemyProjectile` merkt sich Abschussort `_spawn` und Alter `_age`; in
   `draw()` blendet es den Cast-Flash für die ersten `MUZZLE_TICKS` (=7) Frames am
   Abschussort aus (`alpha = 255·(1 − age/MUZZLE_TICKS)`), während das Geschoss
   wegfliegt. **`main.py` bleibt unangetastet** — die bestehende
   `enemy_projectiles`-Schleife zeichnet/updatet alles (Golden Rule 6).
3. **Fallback-Kette** (Golden Rule 5): eigenes Geschoss-Sprite → Standard-Pfeil →
   gezeichnete Kreise. Per-Name-Caches `_shot_cache`/`_muzzle_cache` merken sich
   `False` bei fehlender PNG → kein wiederholtes Lade-Probieren, kein Crash.

## Alternatives
- **Neues `PROJECTILE_SPRITE`-Attribut je Klasse:** redundant — `SPRITE_NAME` ist schon
  da und die `_run`/`_shot`/`_cast`-Namenskonvention ist selbsterklärend.
- **Eigene `gs["muzzle_fx"]`-Liste + FX-Klasse in `fx.py`:** mehr Plumbing (update/draw/
  pop in zwei Gegner-Klassen + `main.py`-Loop) für denselben Effekt; der Flash gehört
  logisch ohnehin zum Schuss → an die Projektil-Lebenszeit gekoppelt ist schlanker.
- **Geschoss-Subklassen je Gegner:** Vererbungs-Explosion ohne Mechanik-Unterschied —
  die Optik ist reine Daten (PNG-Name), eine Klasse mit `sprite`-Parameter reicht.

## Consequences
- **Positiv:** Tier-Fernkampf sofort unterscheidbar, sobald die PNGs da sind; null
  `main.py`-Änderung; 6 Tier-Klassen unverändert; rein additiv (alter Pfeil-Pfad
  unberührt); fehlende PNGs sind unkritisch (Fallback).
- **Negativ / offen:** Die **12 PNGs (6 `_shot` + 6 `_cast`) fehlen noch** — bis dahin
  fliegt überall der Standard-Pfeil. Flash sitzt am Gegner-Mittelpunkt (`self.pos`),
  nicht exakt an der Waffenspitze (akzeptiert, optisch nah genug). Geschoss-Sprites
  werden immer zur Flugrichtung rotiert — radiale Motive (Schädel/Orb) sollten daher
  rotationsunkritisch gezeichnet sein.
- **Verifikation:** Voller Treiber-Flow (Menü → Levelup → Welle 99/100 mit Tier-2-
  Dämonen-Fernkämpfern → Sieg) crashfrei; Geschosse fallen wie erwartet auf den
  Standard-Pfeil zurück (PNGs noch nicht vorhanden). `ast.parse` beider Module sauber.

# ADR 032 — Eigene Boss- & SuperBoss-Sprites pro Tier (frontale Pose)

**Status:** akzeptiert · **Datum:** 2026-06-22

## Kontext

Bis hierher nutzten **alle** regulären Bosse (alle 10 Wellen) denselben Tiny-Swords
Black-Lancer als Platzhalter, und nur der SuperBoss-Drache hatte ein eigenes Sprite —
zudem als **Seitenansicht** (`drache_superboss_walk.png`). `UndeadSuperBoss` (W50) und
`DemonSuperBoss` (W100) fielen mangels PNG auf Fallback-Kreise zurück.

Es wurden via Leonardo.ai sechs eigene Boss-Sprites erzeugt (3 reguläre Tier-Bosse +
3 SuperBosse), durchweg als **frontale Helden-Pose** mit transparentem Hintergrund.

## Entscheidung

1. **`Boss` tier-fähig** (analog dem `SPRITE_NAME`-Reskin der Tier-Gegner, ADR 030):
   neue Felder `SPRITE_NAME`/`SPRITE_PX`; `_load_sprites()` lädt bei gesetztem
   `SPRITE_NAME` ein `assets/custom/<name>_run.png` (und setzt `_lancer_atk=[]`, weil
   das eigene Sprite keine Lancer-Stoß-Animation hat — die Walk-Frames genügen), sonst
   bleibt der Black-Lancer-Pfad als Fallback. Drei Subklassen `Tier1Boss`/`Tier2Boss`/
   `Tier3Boss` mit **eigenem** `_frames_r/_frames_l`-Cache + Tier-Fallback-Farben.
2. **`DragonSuperBoss` bekommt `SPRITE_NAME = "dragon_boss"`** → frontaler Eis-Drache,
   konsistent zu Untotem/Dämon. Der alte Seitenansicht-Drache bleibt über den
   `SPRITE_NAME=None`-Pfad als Fallback erhalten (nicht gelöscht).
3. **Spawn:** `TIER_BOSS = [Tier1Boss, Tier2Boss, Tier3Boss]` in `main.py`, gewählt per
   `tier_for_wave()` — exakt parallel zu `TIER_SUPERBOSS`/`TIER_ROSTER`.

## Abwägung

- **Frontale Pose statt Seitenansicht:** Die generierten Bilder sind imposante
  Frontansichten; reine Seitenprofile waren mit Leonardo nicht zuverlässig hinzubekommen.
  Front-Symmetrie macht das Links/Rechts-Spiegeln (Anmarsch Ost/West) unkritisch. Preis:
  Bosse wirken im horizontalen Anmarsch eher „frontal gleitend" — akzeptiert.
- **Flügel-Cropping gelöst im Prompt, nicht im Code:** Motiv auf ~40–45 % der Leinwand
  geschrumpft + Flügel angelegt → passt ganz ins Bild. Der Loader skaliert proportional
  und blittet zentriert ohne Trim, der leere Rand bleibt erhalten (siehe Memory
  `leonardo-winged-boss-framing`).
- **Animation:** `tools/animate_walk.py` baut aus jedem Standbild einen 8-Frame-Walk;
  geflügelte SuperBosse mit `--fill 0.80-0.82 --tilt 1.2` (extra Rand, wenig Schwanken,
  damit breite Flügel nie an die Zellkante stoßen), reguläre Bosse `--fill 0.86 --tilt 2.0`.

## Konsequenzen

- Alle 6 Endgegner laden je 8 Frames (verifiziert), rendern über den echten `draw()`-Pfad
  korrekt (Render-Montage) und der Live-Flow läuft durch W10/50/150 **crashfrei**.
- Getrackt werden die `*_boss_run.png`; die `*_static.png`-Master bleiben extern
  (Memory `sprite-master-extern-gitignore`).
- Fehlt eines der PNGs, greift weiter der Fallback (Lancer bzw. Kreis) — kein Crash.

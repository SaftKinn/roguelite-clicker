# ADR 016 — SuperBoss-Drache: animiert (zunächst fliegend, dann geerdeter Walk)

- **Status:** Accepted (aktualisiert)
- **Date:** 2026-06-21
- **Refs:** architecture.md §4 (Gegner-Klassen); progress.md D30/D34; **ersetzt ADR 015**
  (statisches Pixel-Art-Standbild)

> **Nachtrag (D34):** Die erste Umsetzung war ein **fliegender** Drache (25-Frame-Strip aus
> dem 5×5-Sheet + Schwebe-Bob). Auf Nutzerwunsch „nicht schweben, laufend" wurde er auf einen
> **geerdeten Walk-Zyklus** umgestellt: detailliertes KI-Bild freigestellt (`key_black_bg` +
> strikter „nur reines Schwarz"-Pass gegen die eingeschlossene Flügel-Tasche), fußverankert
> prozedural animiert → `drache_superboss_walk.png` (8 Frames); `FLY_LIFT`/Bob entfernt. Plus
> eine rein-visuelle Angriffs-Lunge. Die Entscheidung „eigener animierter Drachen-Boss" bleibt;
> nur Fortbewegung (fliegen → laufen) und Quelle (Walk-Sheet → freigestelltes Einzelbild)
> änderten sich.

## Context
Der SuperBoss war seit ADR 015 ein **statisches** Pixel-Art-Standbild des Drachen — er stand
nur am Boden und wirkte leblos. Der Nutzer lieferte eine bessere Quelle: ein sauberes
**5×5-Spritesheet** (25 Frames Lauf-/Flug-Zyklus, AutoSprite, `dragon new-walk-v1.png`) mit
**echtem Alpha-Hintergrund und ohne Wasserzeichen** — und den Wunsch, „ihn etwas fliegen zu
lassen".

(Ein parallel geliefertes Walk-GIF derselben Animation trug ein „Auto Sprite"-Wasserzeichen
und nur weißen Hintergrund — das Spritesheet ist die saubere Quelle und wurde ihm vorgezogen.)

## Decision
- **Asset:** Das 5×5-Sheet (1280², Zelle 256²) deterministisch zu einem **horizontalen
  25-Frame-Strip** verarbeitet: jede Zelle auf eine **gemeinsame** Alpha-Bounding-Box
  (200×144) zugeschnitten → die Animation ist sauber verankert (kein Zittern). Liegt als
  `assets/custom/drache_superboss_fly.png` (5000×144). Kein Hintergrund-/Wasserzeichen-Eingriff
  nötig (Alpha war schon korrekt).
- **Loader:** `load_drache_superboss(target_w=240)` zerlegt den Strip in `_DRACHE_FLY_FRAMES`
  (=25) Frames und skaliert sie mit **`smoothscale`** (glattes Art, nicht Pixel-Art → **kein**
  NEAREST mehr) auf `target_w` Breite, **Höhe proportional** (Seitenverhältnis bleibt; der
  Drache ist breiter als hoch). Roh blickt nach LINKS → `_frames_l`, Flip → `_frames_r`.
- **Animation gratis:** `Warrior.update` cycelt bereits `_anim_frame` durch `_frames_r` —
  mehrere Frames statt einem genügen, der Flügelschlag läuft automatisch. Die alte
  Lancer-Attack-Maschinerie in `SuperBoss` (war via `_lancer_atk=[]` ohnehin tot) wurde
  entfernt.
- **„Fliegen" = rein visuelles Schweben:** in `SuperBoss.draw` ein vertikaler Versatz
  `FLY_LIFT` (konstanter Auftrieb, 18 px) + `sin(tick·FLY_BOB_SPEED)·FLY_BOB_AMP`
  (Auf-und-Ab, 11 px). **`self.pos` bleibt am Boden** → Stop-Distanz, Treffer und Aura-Ringe
  bleiben fair/unverändert; nur die gezeichnete Position (samt Aura) schwebt mit.
- `SPRITE_PX` 170→240 (jetzt Zielbreite statt Quadrat-Kante), `RADIUS` bleibt 60.

## Alternatives
- **Statisches Standbild behalten (ADR 015):** leblos, erfüllt „fliegen" nicht.
- **Hochauflösendes Einzelbild + Bob (ohne Flügelschlag):** schwebt, aber die Flügel stehen
  still — weniger lebendig als der vorhandene 25-Frame-Zyklus.
- **Walk-GIF als Quelle:** trug ein Wasserzeichen + weißen statt transparenten Hintergrund →
  Mehraufwand bei schlechterem Ergebnis als das saubere Spritesheet.
- **`self.pos` wirklich anheben (echtes Fliegen in der Logik):** würde Stop-Distanz/Kollision
  verschieben und das austarierte „DPS-Rennen gegen die Anlaufzeit" (ADR 013) stören — bewusst
  verworfen, der Flug bleibt kosmetisch.

## Consequences
- **Positiv:** Lebendiger, fliegender Endgegner (Flügelschlag + Schweben); minimaler Code
  (Strip-Loader + Bob in `draw`, Animation über den Basis-Mechanismus); saubere Transparenz
  ohne Wasserzeichen.
- **Negativ / Bindung:** Der **Stil-Bruch** aus ADR 015 bleibt bestehen (Drachen-Art vs. glatte
  „Tiny Swords"-Gegner) — bewusst akzeptiert. `FLY_LIFT`/`FLY_BOB_*`/`SPRITE_PX` sind
  Augenmaß-Regler (Playtest). Das alte `drache_superboss.png` wird nicht mehr geladen (bleibt
  als Datei liegen, schadet nicht). Fehlt das neue Asset, greift der gezeichnete
  Primitive-Fallback (Golden Rule 5).
- **Verifikation:** headless Instanz (25 Frames, Frame 240×173, Animation cycelt, HP korrekt) +
  Render auf Terrain (boss-groß, Flugpose, Aura) + voller Treiber-Flow Menü→Welle 100→Sieg
  crashfrei + **Live-Shot Welle 100** (Drache fliegt vom Rand mit Aura/Boss-HP-Bar auf den Turm zu).

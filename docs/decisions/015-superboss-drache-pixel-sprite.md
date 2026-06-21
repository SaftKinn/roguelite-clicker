# ADR 015 — SuperBoss erhält ein statisches Pixel-Art-Drachen-Sprite
- **Status:** Superseded by ADR 016 (animierter, fliegender Drache)
- **Date:** 2026-06-21
- **Refs:** architecture.md §4 (Gegner-Klassen); progress.md D29; ersetzt einen zuvor
  verworfenen, nie committeten Video-Animations-Versuch

## Context
Der SuperBoss (Wellen 50 & 100) nutzte die hochskalierten Lancer-Sprites — kein eigener
Endgegner-Charakter. Ein erster Versuch, ihn als **animierten** Drachen aus einem KI-Video
zu setzen, wurde vom Nutzer optisch verworfen und vollständig zurückgerollt. Stattdessen
sollte ein vom Nutzer ausgewähltes **Pixel-Art-Standbild** des Drachen rein.

## Decision
- Quelle: vorhandenes Drachen-Artwork → deterministisch zu **Pixel-Art** heruntergerechnet
  (verkleinern + Farbpalette reduzieren, Schwarz/eingeschlossene Taschen transparent), final
  **96×96 RGBA**, Seitenansicht, Kopf links. Liegt als `assets/custom/drache_superboss.png`.
- `sprite_loader.load_drache_superboss(target_px)` lädt es **mit NEAREST-Skalierung**
  (`pygame.transform.scale`, nicht `smoothscale`) — sonst verwaschen die Pixel. Roh = links →
  `_frames_l`, Flip → `_frames_r`. Einzel-Frame (statisch).
- `SuperBoss`: lädt dieses Sprite statt der Lancer (`_lancer_atk=[]` schaltet die Lancer-
  Angriffsanimation ab), `RADIUS` 50→60 (Stop-Distanz + Aura-Ringe), `SPRITE_PX=170`. Die
  pulsierenden roten Aura-Ringe der bisherigen Draw-Logik bleiben.
- **Spawn nur Ost/West:** Der Drache betritt das Bild ausschließlich vom linken/rechten Rand
  auf Turm-Höhe (`pos` in `__init__`), damit die Seitenansicht zur Laufrichtung passt.

## Alternatives
- **Animiertes Video-Sprite (Walk-Cycle):** lebendiger, aber vom Nutzer als Optik abgelehnt.
- **Lancer-Sprite behalten:** kein eigener Boss-Charakter.
- **Mit `smoothscale` skalieren:** würde die Pixel glätten und den Pixel-Look zerstören.

## Consequences
- **Positiv:** Eigenständiger, erkennbarer Endgegner; minimaler Code (Sprite-Quelle + Radius +
  Spawn); kein Asset-Animations-Overhead (1 Frame).
- **Negativ / Bindung:** **Stil-Bruch** — der Boss ist Pixel-Art, die übrigen Gegner sind die
  glatten „Tiny Swords"-Cartoon-Sprites. Bewusst akzeptiert (Nutzerwunsch). Zudem glättet der
  Kamera-Zoom (`CAMERA_ZOOM` 1.2, Post-Render-`smoothscale`) das Sprite minimal. Größe/`RADIUS`
  per Augenmaß (Playtest-Regler `SPRITE_PX`/`RADIUS`). Fehlt das Asset, greift der gezeichnete
  Primitive-Fallback (Golden Rule 5).
- **Verifikation:** headless Instanz (Rand-Spawn, Frame 170², Radius 60, HP korrekt) + Render
  auf Terrain (boss-groß, blickt zum Turm, Aura); voller Treiber-Flow bis Welle 100 → Sieg
  crashfrei.

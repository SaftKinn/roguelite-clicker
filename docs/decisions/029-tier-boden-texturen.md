# ADR 029 — Tier-Boden-Texturen: bildschirmfüllender Voll-Hintergrund je Biom

- **Status:** Accepted
- **Date:** 2026-06-22
- **Refs:** `game/terrain.py`, `game/sprite_loader.py`, `main.py`; baut auf Tier-System ADR 024;
  Asset-Stil-Memory `leonardo-terrain-prompts-topdown-seamless`

## Context
Bisher zeigte `Terrain` über alle 150 Wellen denselben Tiny-Swords-Grasboden (eine 64er-Kachel
gekachelt + gestreute Büsche/Felsen). Mit dem Tier-System (ADR 024: Untote/Dämonen/Drachen-Brut
je 50 Wellen) sollte der Boden pro Tier das Biom wechseln. Der Nutzer lieferte drei Leonardo-Texturen
(Top-Down, Tiny-Swords-Stil): Friedhofspflaster, Lava-Basalt, Eis-Schiefer.

## Decision
1. **Voll-Textur statt Kachel-Raster.** Die gelieferten Bilder sind zusammenhängende Top-Down-Szenen
   (~1700²), keine kachelbaren Tilesets. Sie werden **bildschirmfüllend gebacken**, nicht gekachelt:
   `sprite_loader.load_tier_background(tier, size)` skaliert per **COVER** (`max(tw/sw, th/sh)`) und
   schneidet mittig zu → keine Verzerrung, keine sichtbare Naht, der dunkle Rahmen-Rand der Vorlage
   fällt weg. Import auf 1280×1280-PNG vorskaliert (`assets/custom/tier{1,2,3}_ground.png`).
2. **`Terrain(tier=0)`-Parameter.** `Terrain.__init__` lädt die Tier-Textur; greift sie, bringt sie
   eigene Details (Knochen/Lava/Kristalle) mit → **keine Tiny-Swords-Decos** darüber (`self._decos=[]`).
   Fehlt das Asset, bleibt der bisherige Gras-Tile-+-Deco-Pfad (Golden Rule 5, nie crashen).
3. **Biom-Wechsel an der Tier-Grenze.** `start_run()` baut `Terrain(tier_for_wave(gs["wave"]))`;
   im `WAVE_CLEAR`-Block wird nach `gs["wave"] += 1` gegen den **tatsächlich geladenen** `terrain.tier`
   geprüft (`terrain.tier != tier_for_wave(...)`), nicht alte/neue Welle — so greift der Wechsel auch
   nach Dev-Sprüngen (F2–F4). `self.tier` wird auf der Instanz gespeichert.

## Alternatives
- **64er-Tileset-Slicer (`load_tileset` → grid[r][c], eine Vollkachel wiederholt):** zuerst gebaut,
  dann verworfen — die Leonardo-Ausgaben sind kein gleichmäßiges Raster (Rahmen, Fugen, ungleiche
  Kacheln); gekachelt würde das Muster sichtbar wiederholen. Voll-Textur ist für ein
  Festgröße-Top-Down-Spielfeld die einfachere, nahtlose Lösung.
- **Textur strecken (smoothscale direkt auf 1280×720):** 1:1→16:9 verzerrt die Steine. COVER+Crop
  hält die Form.
- **Wave-Vergleich alt→neu für den Wechsel:** bricht bei Dev-Sprüngen, die `gs["wave"]` direkt setzen.
  Vergleich gegen den geladenen Tier ist robust.

## Consequences
- **Positiv:** jedes 50-Wellen-Tier hat eigene Boden-Optik; biom-agnostisch verdrahtet
  (`_TIER_BG_NAMES` + `tier_for_wave`) → weitere Tiers = nur Assets ablegen; nahtlos, kein Kachelmuster;
  voller Fallback auf Gras erhalten.
- **Negativ / offen:** drei 1280²-PNGs (~je wenige MB) im Repo; bei Tier 3 bleibt durch das Cover etwas
  Schneerand sichtbar (wirkt als Arena-Rand, akzeptiert); Decos entfallen im Tier-Modus (Detail kommt
  aus der Textur). HUD-Lesbarkeit auf der dunklen Lava-/Eis-Textur visuell geprüft, ok.
- **Verifikation:** `ground_tier{1,2,3}_*.png` gerendert (decos=0 → Textur aktiv); In-Game
  `02_playing.png` (Turm auf Friedhofspflaster, HUD lesbar); voller Treiber-Flow (Menü→Lauf→Levelup→
  Welle 149→Sieg) crashfrei; Headless-Check: `Terrain(tier=0/1/2)` baut, `tier_for_wave` schaltet
  W51/W101.

# KI-Frame-Pipeline — echte Bewegungs-Animationen für Helden-Motive

Ziel: die prozeduralen Pseudo-Walks (`tools/animate_walk.py`, verbiegt EIN Standbild)
schrittweise durch **echte, einzeln gezeichnete Frames** ersetzen — zuerst für die
sichtbarsten Motive (Turm, 6 Bosse, Signatur-Gegner).

**Der Vertrag:** Der Spiel-Loader `sprite_loader._load_custom_strip` liest einen
**horizontalen Strip quadratischer, transparenter Frames** (`assets/custom/<name>_run.png`,
Frame-Anzahl = Breite ÷ Höhe, nach RECHTS blickend). Solange ein neuer Strip dieses Format
hat, lädt das Spiel ihn **ohne Code-Änderung** — wir tauschen nur die `_run.png`.

## Schritte pro Motiv

1. **Quelle:** vorhandenes `<name>_static.png` (externer Master in
   `Desktop\aselfmade assets\…`; Magenta-BG `#FF00FF`, kein Boden — siehe Memory-Regeln).

2. **Bewegung erzeugen (KI):** kurzen, **loopbaren** Walk-Clip generieren — z. B. Leonardo
   *Motion* / Image-to-Video aus dem Standbild, oder ein anderes Image-to-Video-Tool.
   - Magenta-Hintergrund beibehalten (sauberes Keying), Figur seitlich/leicht frontal,
     nach rechts laufend.
   - Geflügelte Bosse: Motiv klein halten (~40–45 % der Leinwand), Flügel anlegen
     (Memory `leonardo-winged-boss-framing`).
   - Export als **animiertes GIF / WEBP**, **Bilderordner** oder **Video** (mp4).

3. **Frames packen:** mit dem neuen Tool in den Strip wandeln:
   ```bash
   python tools/frames_from_clip.py <clip>  assets/custom/<name>_run.png --frames 8
   ```
   - `--bg magenta|black|white|none` — Hintergrund zum Wegkeyen (Default Magenta; `none`,
     falls der Clip schon transparent ist).
   - `--frames N` — auf N Frames abtasten (Clip hat oft 24–60; 8–12 reichen fürs Spiel).
   - `--grid ZxS` — falls die KI ein Sprite-**Raster**-Standbild statt eines Clips liefert.
   - `--enclosed` — umschlossene BG-Taschen (Körper↔Arm) zusätzlich entfernen.
   - `--cell 256` — Kantenlänge je Frame; `--fill 0.86` — Kopffreiheit.

   Das Tool keyt jeden Frame (Ecken-Flood-Fill wie `key_black_bg.py`), schneidet auf den
   Inhalt zu, skaliert **alle Frames mit EINEM gemeinsamen Faktor** (aus der größten
   Content-Höhe → kein Größen-Springen) und verankert jeden am **Fußpunkt**.

4. **Einsetzen & prüfen:** Datei liegt in `assets/custom/` → `python main.py` starten.
   `_load_custom_strip` zieht die neue Frame-Anzahl automatisch. Kein Code nötig.

## Reihenfolge (Helden zuerst)

1. **Turm** (`player_tower.png` — immer im Bildzentrum). *(Die Idle-/Recoil-Animation aus
   ADR 035 deckt ihn schon teils ab; echte Frames sind optional.)*
2. **6 Bosse/SuperBosse:** `tier{1,2,3}_boss`, `undead/demon/dragon_boss` — je Walk,
   optional Attack.
3. **Signatur-Gegner je Tier** (z. B. `orc_warrior`, `skeleton_archer`, `lich`) — der Rest
   bleibt vorerst beim prozeduralen Walk und wird nach und nach ersetzt.

## Später — echte Attack-/Death-Frames

`Warrior` hat bereits `_atk1/_atk2_frames`. Echte Attack-Keyframes ließen sich über
dieselbe Pipeline in `<name>_atk.png`-Strips packen und in `_load_sprites()` einhängen —
eigene Etappe, nicht im ersten Wurf.

> Video-Input braucht `imageio` (`pip install imageio imageio-ffmpeg`); GIF/WEBP/Ordner
> laufen rein mit Pillow.

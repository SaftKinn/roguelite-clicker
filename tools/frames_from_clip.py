#!/usr/bin/env python3
"""Echten KI-Bewegungsclip → loader-fertiger Frame-Strip (`assets/custom/<name>_run.png`).

Anders als `tools/animate_walk.py` (das EIN Standbild prozedural verbiegt) packt dieses
Tool **echte, einzeln gezeichnete Frames** aus einem KI-Clip (Leonardo Motion / Image-to-
Video etc.) in genau das Format, das der Spiel-Loader `sprite_loader._load_custom_strip`
erwartet: gleich große **quadratische** Frames, lückenlos in EINER horizontalen Reihe,
transparent, nach RECHTS blickend (der Loader spiegelt für links).

Frame-Quellen (auto-erkannt nach Dateityp / `--grid`):
  * **Animiertes Bild** (GIF / animiertes WEBP / APNG)  → alle Einzelbilder.
  * **Ordner**  mit `frame_000.png …`                   → alphabetisch sortiert.
  * **Sprite-Grid** (`--grid ZxS`, ein Standbild)        → Z·S Zellen zeilenweise.
  * **Video** (`.mp4/.mov/.webm`)                        → braucht `imageio` (optional;
    fehlt es, sagt das Tool, wie man es nachinstalliert).

Pipeline je Frame:
  1. **Hintergrund keyen** (`--bg magenta|black|white|none`, Default Magenta `#FF00FF` —
     unsere Prompt-Konvention). Ecken-Flood-Fill wie `tools/key_black_bg.py`: nur
     rand-verbundener BG-Ton fällt weg → innere Outlines bleiben. `none` = Clip ist schon
     transparent, Alpha wird übernommen.
  2. Auf sichtbaren Inhalt zuschneiden (`getbbox`).
Danach über ALLE Frames hinweg:
  3. **Gemeinsame Skalierung** aus der größten Content-Höhe → die Figur springt nicht in
     der Größe (echte Squash-Bewegung bleibt erhalten).
  4. Jeden Frame am **Fußpunkt** auf der Baseline verankern, horizontal zentrieren.
  5. Lückenlos zu `cell·N × cell` packen und speichern.

`--frames N` tastet gleichmäßig N Frames ab (Clip hat oft 24–60; Spiel animiert ~10 fps,
8–12 Frames reichen → sauberer Loop, kleinere Datei).

Aufruf:
    python tools/frames_from_clip.py <clip>  assets/custom/<name>_run.png
        [--frames 8] [--cell 256] [--bg magenta] [--thresh 60] [--enclosed]
        [--fill 0.86] [--grid 4x4]
"""
import argparse
import glob
import os
from PIL import Image, ImageDraw, ImageSequence

_SEED = (255, 0, 255)            # Marker-Farbe für die Flood-Fill (Magenta)
_NAMED_BG = {
    "magenta": (255, 0, 255),
    "black":   (0, 0, 0),
    "white":   (255, 255, 255),
}
_VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def _near(a: tuple, b: tuple, thresh: int) -> bool:
    """Manhattan-Farbabstand ≤ thresh (gleiche Metrik wie key_black_bg)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) <= thresh


# --- 1) Frame-Quellen einlesen -------------------------------------------------------

def _frames_from_dir(path: str) -> list:
    files = sorted(glob.glob(os.path.join(path, "*.png")) +
                   glob.glob(os.path.join(path, "*.webp")) +
                   glob.glob(os.path.join(path, "*.jpg")))
    if not files:
        raise SystemExit(f"Keine Bilder in {path}")
    return [Image.open(f).convert("RGBA") for f in files]


def _frames_from_grid(img: Image.Image, rows: int, cols: int) -> list:
    w, h = img.size
    cw, ch = w // cols, h // rows
    return [img.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)).convert("RGBA")
            for r in range(rows) for c in range(cols)]


def _frames_from_video(path: str, want: int) -> list:
    try:
        import imageio.v3 as iio
    except Exception:
        raise SystemExit("Video-Input braucht `imageio` (+ `imageio-ffmpeg`):\n"
                         "    pip install imageio imageio-ffmpeg\n"
                         "Alternativ den Clip vorab als GIF/Bilderordner exportieren.")
    frames = [Image.fromarray(f).convert("RGBA") for f in iio.imiter(path)]
    if not frames:
        raise SystemExit(f"Keine Frames aus {path} gelesen")
    return frames


def _load_source_frames(src: str, grid: str | None) -> list:
    if os.path.isdir(src):
        return _frames_from_dir(src)
    ext = os.path.splitext(src)[1].lower()
    if ext in _VIDEO_EXT:
        return _frames_from_video(src, want=0)
    img = Image.open(src)
    if grid:
        rows, cols = (int(x) for x in grid.lower().split("x"))
        return _frames_from_grid(img.convert("RGBA"), rows, cols)
    # Animiertes Bild (GIF/WEBP/APNG) → alle Frames; Standbild → genau einer.
    return [fr.convert("RGBA") for fr in ImageSequence.Iterator(img)]


def _resample(frames: list, n: int) -> list:
    """Gleichmäßig n Frames abtasten (ohne den letzten Frame doppelt zu nehmen → Loop)."""
    if n <= 0 or n >= len(frames):
        return frames
    return [frames[round(i * len(frames) / n)] for i in range(n)]


# --- 2) Hintergrund keyen ------------------------------------------------------------

def _key_bg(frame: Image.Image, bg: str, thresh: int, enclosed: bool,
            enclosed_thresh: int) -> Image.Image:
    """Vollflächigen BG transparent machen (Ecken-Flood-Fill). bg='none' → Alpha behalten."""
    if bg == "none":
        return frame                                  # Clip ist bereits freigestellt
    rgb = frame.convert("RGB")
    w, h = rgb.size
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    bg_ref = _NAMED_BG.get(bg) or rgb.getpixel(corners[0])
    for corner in corners:
        ImageDraw.floodfill(rgb, corner, _SEED, thresh=thresh)
    pixels = list(rgb.getdata())
    if enclosed:
        pixels = [_SEED if (px != _SEED and _near(px, bg_ref, enclosed_thresh)) else px
                  for px in pixels]
    out = Image.new("RGBA", (w, h))
    out.putdata([(0, 0, 0, 0) if px == _SEED else (px[0], px[1], px[2], 255)
                 for px in pixels])
    return out


# --- 3-5) zuschneiden, gemeinsam skalieren, fußverankert packen ----------------------

def generate(src: str, dst: str, frames: int = 8, cell: int = 256, bg: str = "magenta",
             thresh: int = 60, enclosed: bool = False, enclosed_thresh: int = 30,
             fill: float = 0.86, grid: str | None = None) -> None:
    raw = _load_source_frames(src, grid)
    raw = _resample(raw, frames)

    # Je Frame: keyen + auf Inhalt zuschneiden.
    cropped = []
    for fr in raw:
        keyed = _key_bg(fr, bg, thresh, enclosed, enclosed_thresh)
        bbox = keyed.getbbox()
        cropped.append(keyed.crop(bbox) if bbox else keyed)

    # Gemeinsame Skalierung aus der GRÖSSTEN Content-Höhe → kein Größen-Springen.
    max_h = max(c.height for c in cropped)
    scale = (cell * fill) / max_h
    baseline_y = cell - round(cell * 0.04)            # Fußlinie (kleiner Rand unten)

    strip = Image.new("RGBA", (cell * len(cropped), cell), (0, 0, 0, 0))
    for i, c in enumerate(cropped):
        rw = max(1, round(c.width * scale))
        rh = max(1, round(c.height * scale))
        sc = c.resize((rw, rh), Image.LANCZOS)
        px = i * cell + round(cell / 2 - rw / 2)      # horizontal zentriert in der Zelle
        py = baseline_y - rh                          # Fuß auf der Baseline
        strip.alpha_composite(sc, (px, py))

    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    strip.save(dst)
    print(f"  {src}  ->  {dst}   ({len(cropped)} Frames, {cell}x{cell} je Frame)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="Clip (GIF/WEBP/APNG/Video), Bilderordner oder Grid-Standbild")
    ap.add_argument("dst", help="Ziel-Strip, z. B. assets/custom/orc_warrior_run.png")
    ap.add_argument("--frames", type=int, default=8, help="auf so viele Frames abtasten")
    ap.add_argument("--cell", type=int, default=256, help="Kantenlänge je quadratischem Frame")
    ap.add_argument("--bg", choices=["magenta", "black", "white", "none"], default="magenta",
                    help="Hintergrundfarbe zum Wegkeyen ('none' = schon transparent)")
    ap.add_argument("--thresh", type=int, default=60, help="Flood-Fill-Farbtoleranz")
    ap.add_argument("--enclosed", action="store_true",
                    help="umschlossene BG-Taschen (Körper↔Arm) zusätzlich entfernen")
    ap.add_argument("--enclosed-thresh", type=int, default=30, dest="enclosed_thresh")
    ap.add_argument("--fill", type=float, default=0.86,
                    help="Anteil der Zellhöhe, den die höchste Figur einnimmt (Kopffreiheit)")
    ap.add_argument("--grid", default=None, help="Standbild als Sprite-Grid lesen, z. B. 4x4")
    a = ap.parse_args()
    generate(a.src, a.dst, a.frames, a.cell, a.bg, a.thresh, a.enclosed,
             a.enclosed_thresh, a.fill, a.grid)

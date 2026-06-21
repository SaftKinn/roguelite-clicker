#!/usr/bin/env python3
"""Vollflächigen Hintergrund eines KI-Charakterbildes transparent machen → Gegner-Sprite.

Pipeline (deterministisch, nur Pillow — kein numpy/scipy nötig):
  1. Flood-Fill von den vier Ecken: nur **mit dem Rand verbundener** Near-BG-Ton wird
     markiert (so bleiben dunkle Outlines INNERHALB der Figur erhalten — ein globaler
     "BG→transparent"-Schwellwert würde da Löcher reißen).
  1b. (optional `--enclosed`) **Eingeschlossene** Hintergrund-Taschen entfernen, die von
     der Figur umschlossen sind und die Ecken-Flut nie erreicht (z. B. der Spalt zwischen
     Körper und Arm). Es werden NUR Pixel sehr nah am gemessenen BG-Ton entfernt
     (`--enclosed-thresh`, bewusst strenger als `--thresh`, um Figur-Outlines zu schonen).
  2. Markierte Pixel → alpha 0, Rest → opak.
  3. Auf den sichtbaren Inhalt zuschneiden (getbbox).
  4. Auf eine **quadratische** Leinwand zentrieren — Pflicht für den Spiel-Loader
     (`_load_custom_strip` macht `subsurface((0,0,height,height))`; bei Hochformat
     läge das Rechteck außerhalb der Fläche → Crash). Quadrat → genau 1 Frame.

Aufruf:
    python tools/key_black_bg.py <input.png> <output.png> [--thresh 60] [--pad 0.06]
        [--enclosed] [--enclosed-thresh 30]

`--thresh`          Farbabstand vom BG-Ton, bis zu dem die Ecken-Flood-Fill füllt (höher =
                    mehr Halo weg, aber Vorsicht vor dunklen Figur-Rändern).
`--pad`             zusätzlicher transparenter Rand als Anteil der Quadratseite (Default 6 %).
`--enclosed`        zusätzlich umschlossene BG-Taschen (Körper↔Arm) global wegkeyen.
`--enclosed-thresh` Toleranz dafür (Default 30, strenger als --thresh → schont Outlines).
"""
import argparse
from PIL import Image, ImageDraw

_SEED = (255, 0, 255)   # Marker-Farbe (kommt im Artwork nicht vor)


def _near(a: tuple, b: tuple, thresh: int) -> bool:
    """Manhattan-Farbabstand ≤ thresh (gleiche Metrik wie Pillows floodfill-thresh-Idee)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) <= thresh


def key_black(src: str, dst: str, thresh: int = 60, pad: float = 0.06,
              enclosed: bool = False, enclosed_thresh: int = 30) -> None:
    img = Image.open(src).convert("RGB")
    w, h = img.size
    # BG-Referenzton aus den Ecken messen (VOR der Flut) — das ist der echte Hintergrund.
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    bg_ref = img.getpixel(corners[0])
    # 1. Hintergrund (rand-verbundener BG-Ton) von allen vier Ecken fluten.
    for corner in corners:
        ImageDraw.floodfill(img, corner, _SEED, thresh=thresh)
    # 1b. Eingeschlossene BG-Taschen: global, aber NUR sehr nah am gemessenen BG-Ton.
    pixels = list(img.getdata())
    if enclosed:
        pixels = [_SEED if (px != _SEED and _near(px, bg_ref, enclosed_thresh)) else px
                  for px in pixels]
    # 2. Marker → transparent, alles andere opak.
    out = Image.new("RGBA", (w, h))
    out.putdata([(0, 0, 0, 0) if px == _SEED else (px[0], px[1], px[2], 255)
                 for px in pixels])
    # 3. Auf den Inhalt zuschneiden.
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    cw, ch = out.size
    # 4. Auf ein zentriertes Quadrat legen (+ optionaler Rand) → loader-sicher (1 Frame).
    side = int(max(cw, ch) * (1 + pad))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(out, ((side - cw) // 2, (side - ch) // 2), out)
    canvas.save(dst)
    print(f"  {src}  ->  {dst}   ({side}x{side}, 1 Frame)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--thresh", type=int, default=60)
    ap.add_argument("--pad", type=float, default=0.06)
    ap.add_argument("--enclosed", action="store_true",
                    help="umschlossene BG-Taschen (Körper↔Arm) zusätzlich entfernen")
    ap.add_argument("--enclosed-thresh", type=int, default=30, dest="enclosed_thresh")
    args = ap.parse_args()
    key_black(args.src, args.dst, args.thresh, args.pad, args.enclosed, args.enclosed_thresh)

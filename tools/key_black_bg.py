#!/usr/bin/env python3
"""Schwarz-Hintergrund eines KI-Charakterbildes transparent machen → Gegner-Sprite.

Pipeline (deterministisch, nur Pillow — kein numpy/scipy nötig):
  1. Flood-Fill von den vier Ecken: nur **mit dem Rand verbundenes** Near-Black wird
     markiert (so bleiben dunkle Outlines INNERHALB der Figur erhalten — ein globaler
     "schwarz→transparent"-Schwellwert würde da Löcher reißen).
  2. Markierte Pixel → alpha 0, Rest → opak.
  3. Auf den sichtbaren Inhalt zuschneiden (getbbox).
  4. Auf eine **quadratische** Leinwand zentrieren — Pflicht für den Spiel-Loader
     (`_load_custom_strip` macht `subsurface((0,0,height,height))`; bei Hochformat
     läge das Rechteck außerhalb der Fläche → Crash). Quadrat → genau 1 Frame.

Aufruf:
    python tools/key_black_bg.py <input.png> <output.png> [--thresh 60] [--pad 0.06]

`--thresh`  Farbabstand vom reinen Schwarz, bis zu dem die Flood-Fill füllt (höher =
            mehr vom dunklen Halo wird entfernt, aber Vorsicht vor dunklen Figur-Rändern).
`--pad`     zusätzlicher transparenter Rand als Anteil der Quadratseite (Default 6 %).
"""
import argparse
from PIL import Image, ImageDraw

_SEED = (255, 0, 255)   # Marker-Farbe (kommt im Artwork nicht vor)


def key_black(src: str, dst: str, thresh: int = 60, pad: float = 0.06) -> None:
    img = Image.open(src).convert("RGB")
    w, h = img.size
    # 1. Hintergrund (rand-verbundenes Schwarz) von allen vier Ecken fluten.
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(img, corner, _SEED, thresh=thresh)
    # 2. Marker → transparent, alles andere opak.
    out = Image.new("RGBA", (w, h))
    out.putdata([(0, 0, 0, 0) if px == _SEED else (px[0], px[1], px[2], 255)
                 for px in img.getdata()])
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
    args = ap.parse_args()
    key_black(args.src, args.dst, args.thresh, args.pad)

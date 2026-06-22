#!/usr/bin/env python3
"""Ein transparentes Geschoss-Standbild waagerecht ausrichten (Pillow-only).

Leonardo malt die Fernkämpfer-Pfeile (`<name>_shot.png`) gern schräg/perspektivisch.
Der Spiel-Code (`EnemyProjectile.draw`) rotiert das Geschoss aber selbst zur
Flugrichtung und nimmt an, das **Roh-Sprite zeigt nach RECHTS (0 Grad)**. Ein schief
gespeicherter Pfeil fliegt deshalb dauerhaft schief. Dieses Tool dreht das Bild einmal
gerade, beschneidet es transparent und speichert es zurück.

Zwei Modi:
  * **Manuell:** Winkel selbst angeben (positiv = gegen den Uhrzeigersinn).
        python tools/rotate_flat.py skeleton_archer_shot.png --deg -30
  * **Auto:** Längsachse per PCA erkennen und waagerecht legen (gut für längliche
    Pfeile/Bolts; braucht numpy). Zeigt der Pfeil danach nach links, `--flip` anhängen.
        python tools/rotate_flat.py skeleton_archer_shot.png --auto
        python tools/rotate_flat.py drake_archer_shot.png --auto --flip

Ohne <dst> wird in dieselbe Datei zurückgeschrieben (in-place). Ein blosser Dateiname
ohne Pfad wird in assets/custom/ gesucht.
"""
import argparse
import math
import os
from PIL import Image

_CUSTOM = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "custom")


def _resolve(path: str) -> str:
    """Blosser Dateiname → assets/custom/<name>; sonst Pfad unveraendert."""
    if os.path.exists(path):
        return path
    cand = os.path.join(_CUSTOM, path)
    return cand if os.path.exists(cand) else path


def _auto_angle(img: Image.Image) -> float:
    """Winkel der Haupt-(Laengs-)achse opaker Pixel via PCA, in Grad (CCW).
    Rueckgabe so, dass rotate(+angle) die Achse waagerecht legt."""
    try:
        import numpy as np
    except ImportError:
        raise SystemExit("--auto braucht numpy:  pip install numpy")
    alpha = np.array(img.split()[-1])
    ys, xs = np.where(alpha > 32)                  # opake Pixel (Alpha-Schwelle)
    if len(xs) < 2:
        return 0.0
    pts = np.vstack([xs.astype(float), ys.astype(float)])
    pts -= pts.mean(axis=1, keepdims=True)
    cov = np.cov(pts)
    eigvals, eigvecs = np.linalg.eigh(cov)         # aufsteigend → letzter = groesste Achse
    vx, vy = eigvecs[:, -1]
    # Bild-y zeigt nach unten; rotate(+) ist CCW → Vorzeichen so, dass Achse flach wird.
    return math.degrees(math.atan2(vy, vx))


def rotate_flat(src: str, dst: str | None = None, deg: float = 0.0,
                auto: bool = False, flip: bool = False) -> None:
    src = _resolve(src)
    dst = src if dst is None else dst
    img = Image.open(src).convert("RGBA")

    angle = _auto_angle(img) if auto else deg
    if abs(angle) > 0.01:
        img = img.rotate(angle, expand=True, resample=Image.BICUBIC)
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    bbox = img.getbbox()                           # transparent zuschneiden
    if bbox:
        img = img.crop(bbox)
    img.save(dst)
    mode = f"auto ({angle:+.1f} Grad)" if auto else f"{angle:+.1f} Grad"
    print(f"  {os.path.basename(src)}  ->  {os.path.basename(dst)}   [{mode}"
          f"{', flip' if flip else ''}]")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="PNG (blosser Name wird in assets/custom/ gesucht)")
    ap.add_argument("dst", nargs="?", default=None, help="Ziel (Default: in-place)")
    ap.add_argument("--deg",  type=float, default=0.0,
                    help="Drehwinkel in Grad, positiv = gegen Uhrzeigersinn")
    ap.add_argument("--auto", action="store_true",
                    help="Laengsachse per PCA erkennen und waagerecht legen (numpy)")
    ap.add_argument("--flip", action="store_true",
                    help="horizontal spiegeln (falls Pfeil nach links zeigt)")
    a = ap.parse_args()
    rotate_flat(a.src, a.dst, a.deg, a.auto, a.flip)

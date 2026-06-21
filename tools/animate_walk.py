#!/usr/bin/env python3
"""Prozeduraler Walk-/Marsch-Zyklus aus EINEM statischen Gegner-Sprite (Pillow-only).

Aus einem transparenten Standbild (z. B. `assets/custom/orc_warrior_run.png` mit nur
1 Frame) wird ein horizontaler **N-Frame-Strip** im Format, das `_load_custom_strip`
erwartet: gleich große, quadratische Frames in EINER Reihe, lückenlos, transparent.

Bewegungsmodell (rein prozedural, kein Rigging — reicht für ~60-px-Gegner):
  * **Bob:** vertikales Auf/Ab, am **Fußpunkt** verankert (Figur wippt am Boden,
    schwebt nicht). `--bounces` Beats pro Zyklus (2 = Marsch mit zwei Schritten,
    1 = sanftes Schweben für Caster).
  * **Squash/Stretch:** auf dem „Stampf"-Beat breiter + kürzer (Gewicht), oben voll
    gestreckt. Über `--squash` (0 = aus, z. B. für schwebende Gegner).
  * **Tilt:** leichtes Links/Rechts-Neigen, einmal pro Zyklus, für Leben.

Anchored am Fuß + feste Zellgröße → kein Zittern, sauberer Loop (Frame N == Frame 0).
`Warrior.update` zählt die Frames im Spiel automatisch durch.

Aufruf:
    python tools/animate_walk.py <in.png> <out.png> [--frames 8] [--cell 256]
        [--bob 0.06] [--squash 0.06] [--tilt 2.5] [--bounces 2] [--fill 0.86]
"""
import argparse
import math
from PIL import Image


def generate(src: str, dst: str, frames: int = 8, cell: int = 256,
             bob: float = 0.06, squash: float = 0.06, tilt: float = 2.5,
             bounces: int = 2, fill: float = 0.86) -> None:
    body = Image.open(src).convert("RGBA")
    bbox = body.getbbox()                      # auf den sichtbaren Inhalt zuschneiden
    if bbox:
        body = body.crop(bbox)
    bw, bh = body.size
    # Auf Zielhöhe skalieren (Kopffreiheit lassen, damit Bob/Rotation nicht clippen).
    scale = (cell * fill) / bh
    body = body.resize((max(1, round(bw * scale)), max(1, round(bh * scale))), Image.LANCZOS)
    bw, bh = body.size
    baseline_y = cell - round(cell * 0.04)     # Fußlinie (kleiner Rand unten)
    two_pi = 2 * math.pi

    frame_imgs = []
    for i in range(frames):
        t       = i / frames                                   # 0..1, loopt
        bounce  = math.cos(two_pi * bounces * t)               # +1 oben .. -1 unten
        top_amt = (bounce + 1) / 2                             # 1 oben .. 0 unten
        comp    = 1 - top_amt                                  # 0 oben .. 1 unten (Stauchung)
        sway    = math.sin(two_pi * t) * tilt                  # Grad, einmal pro Zyklus

        sx = 1 + squash * comp * 0.6                           # unten breiter
        sy = 1 - squash * comp                                 # unten kürzer
        fr = body.resize((max(1, round(bw * sx)), max(1, round(bh * sy))), Image.LANCZOS)
        if abs(sway) > 0.01:
            fr = fr.rotate(sway, expand=True, resample=Image.BICUBIC)
        rw, rh = fr.size

        y_lift = round(bob * cell * top_amt)                   # oben angehoben
        canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        px = round(cell / 2 - rw / 2)                          # horizontal zentriert
        py = round(baseline_y - y_lift - rh)                  # Fuß auf Baseline (minus Lift)
        canvas.alpha_composite(fr, (px, py))
        frame_imgs.append(canvas)

    strip = Image.new("RGBA", (cell * frames, cell), (0, 0, 0, 0))
    for i, f in enumerate(frame_imgs):
        strip.alpha_composite(f, (i * cell, 0))
    strip.save(dst)
    print(f"  {src}  ->  {dst}   ({frames} Frames, {cell}x{cell} je Frame)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--frames",  type=int,   default=8)
    ap.add_argument("--cell",    type=int,   default=256)
    ap.add_argument("--bob",     type=float, default=0.06)
    ap.add_argument("--squash",  type=float, default=0.06)
    ap.add_argument("--tilt",    type=float, default=2.5)
    ap.add_argument("--bounces", type=int,   default=2)
    ap.add_argument("--fill",    type=float, default=0.86)
    a = ap.parse_args()
    generate(a.src, a.dst, a.frames, a.cell, a.bob, a.squash, a.tilt, a.bounces, a.fill)

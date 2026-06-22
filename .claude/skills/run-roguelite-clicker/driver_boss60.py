#!/usr/bin/env python3
"""Einmal-Treiber: Sprung zu Welle 60 (Tier-2-Boss) + Serien-Screenshots der Lauf-Anim."""
import os, sys, time, threading
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
sys.path.insert(0, _ROOT); os.chdir(_ROOT)
import pygame  # noqa: E402
_fake = {"pos": (0, 0)}
pygame.mouse.get_pos = lambda: _fake["pos"]
pygame.mouse.set_visible = lambda *a, **k: None

def shot(name):
    pygame.image.save(pygame.display.get_surface(), os.path.join(_HERE, "shots", name))
    print("  shot ->", name)

def click(x, y):
    _fake["pos"] = (x, y)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y)))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(x, y)))

def key(k):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=""))

from game.main_menu import MainMenu as _MM
_menu = _MM()
START_BTN = _menu.buttons[_menu.button_ids.index("start")].rect.center

def flow():
    t0 = time.time()
    while pygame.display.get_surface() is None and time.time() - t0 < 10:
        time.sleep(0.05)
    time.sleep(0.7)
    click(640, 252)          # Slot 1
    time.sleep(0.6)
    click(*START_BTN)        # Lauf starten
    time.sleep(1.0)
    key(pygame.K_u)          # Unverwundbarkeit an (Boss-Oneshot aus, Turm überlebt)
    key(pygame.K_F3)         # Sprung zu Welle 60 (Tier-2-Boss)
    time.sleep(4.0)          # Wellen-Delay + Intro-Zoom abklingen + Boss läuft rein
    for i in range(12):      # dichte Serie: Lauf-Frames über ~3 s
        shot(f"boss60_{i:02d}.png")
        time.sleep(0.25)
    pygame.event.post(pygame.event.Event(pygame.QUIT))

os.makedirs(os.path.join(_HERE, "shots"), exist_ok=True)
threading.Thread(target=flow, daemon=True).start()
import main as game
try:
    game.main()
except SystemExit:
    pass
print("fertig.")

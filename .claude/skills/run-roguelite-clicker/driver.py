#!/usr/bin/env python3
"""Headless-Treiber für roguelite-clicker (Pygame).

Startet das ECHTE Spiel (`main.main()`) headless über den SDL-Dummy-Treiber und
fährt es von einem Controller-Thread aus: Mausklicks und Tasten werden als
synthetische Pygame-Events in die Schleife gepostet, Screenshots vom lebenden
Display-Surface gespeichert.

Warum der Aufbau so ist (in den Pixeln ausgemessen, nicht geraten):
  * `SDL_VIDEODRIVER=dummy` rendert ohne Fenster/X11 — läuft auf Windows UND Linux.
  * Unter Dummy liefert `pygame.mouse.set_pos()` **nichts** zurück
    (`get_pos()` bleibt (0,0)). Die Klick-Handler in `main.py` lesen aber
    `pygame.mouse.get_pos()` — daher patchen wir `get_pos` auf eine steuerbare
    Position, statt `set_pos` zu nutzen.
  * `main.main()` blockiert (eigene 60-FPS-Schleife) und ruft am Ende `sys.exit()`.
    Es läuft daher auf dem MAIN-Thread (SDL mag das), der Controller im Daemon-Thread.

Aufruf:
    python driver.py                 # voller Flow Menü→Spiel→Upgrade→Welle100→Sieg
    python driver.py --outdir DIR    # Screenshots woandershin
    python driver.py --flow menu     # nur Hauptmenü screenshotten (schnell)

Screenshots landen in <outdir> (Default: ./shots neben diesem Skript).
"""
import os
import sys
import time
import argparse
import threading

# Windows-Konsole (cp1252) sonst Crash auf Umlauten/Pfeilen in print(); UTF-8 erzwingen.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- Headless erzwingen, BEVOR pygame/main importiert werden ---
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Projekt-Root (zwei Ebenen über diesem Skript: .claude/skills/run-…/driver.py)
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)   # main.py lädt Assets relativ zum CWD/__file__

import pygame  # noqa: E402

# --- Maus-Position steuerbar machen (Dummy-Treiber-Workaround) ---
_fake = {"pos": (0, 0)}
pygame.mouse.get_pos = lambda: _fake["pos"]          # type: ignore[assignment]
pygame.mouse.set_visible = lambda *a, **k: None       # type: ignore[assignment]

SCREEN_W, SCREEN_H = 1280, 720


def _wait_surface(timeout=10.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        surf = pygame.display.get_surface()
        if surf is not None:
            return surf
        time.sleep(0.05)
    raise RuntimeError("Display-Surface kam nicht hoch — main() gestartet?")


def shot(name, outdir):
    surf = pygame.display.get_surface()
    path = os.path.join(outdir, name)
    pygame.image.save(surf, path)
    print(f"  screenshot → {os.path.relpath(path, _ROOT)}")


def click(x, y):
    """Setzt die (gepatchte) Mausposition und postet einen vollen Klick."""
    _fake["pos"] = (x, y)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y)))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,   button=1, pos=(x, y)))


def key(k):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=""))


# Button-/Karten-Koordinaten. „Lauf Starten" wird aus dem ECHTEN MainMenu-Layout
# abgeleitet (Rects entstehen nur aus Konstanten — kein Display/Font nötig), damit
# der Treiber nicht bricht, wenn ein Menüpunkt dazukommt (z. B. „Lexikon" → 5 Buttons,
# verschob die feste y=291 in den Spalt zwischen zwei Buttons).
from game.main_menu import MainMenu as _MM   # noqa: E402
_menu = _MM()
START_BTN = _menu.buttons[_menu.button_ids.index("start")].rect.center
CARD0     = (340, 380)   # erste Upgrade-Karte


def flow_full(outdir):
    _wait_surface()
    time.sleep(0.7)
    print("[0] Speicherstand-Auswahl → Slot 1 wählen")
    shot("00_slots.png", outdir)
    click(640, 252)          # Slot-1-Karte (oberste) anklicken → Hauptmenü
    time.sleep(0.6)

    print("[1] Hauptmenü")
    shot("01_menu.png", outdir)

    print("[2] 'Lauf Starten' klicken → PLAYING")
    click(*START_BTN)
    time.sleep(1.0)
    shot("02_playing.png", outdir)

    print("[2b] Leertaste → Overdrive zünden (aktiver Burst, ADR 034)")
    key(pygame.K_SPACE)
    time.sleep(0.4)
    shot("02b_overdrive.png", outdir)

    print("[3] F7 → Levelup → Karten-Auswahl (UPGRADE)")
    key(pygame.K_F7)         # Dev-Levelup liegt jetzt auf F7 (F1–F6 = Boss-Wellen-Sprünge)
    time.sleep(0.8)          # Karten-Fade abwarten (klickbar ab fade≥120)
    shot("03_levelup.png", outdir)

    print("[4] Karte wählen → zurück ins Spiel")
    click(*CARD0)
    time.sleep(0.8)
    shot("04_after_levelup.png", outdir)

    print("[5] F6 → Welle 150 (Drache-SuperBoss), dann F8 (alle töten) → VICTORY")
    key(pygame.K_F6)         # Sprung auf Welle 150
    time.sleep(1.6)          # WAVE_CLEAR_DELAY (70f ≈ 0.9s) + Puffer → Welle 150 spawnt
    key(pygame.K_F8)         # alle Gegner töten → Welle 150 geräumt → Sieg
    time.sleep(0.8)
    shot("05_victory.png", outdir)

    print("[6] beenden (QUIT)")
    pygame.event.post(pygame.event.Event(pygame.QUIT))


def flow_menu(outdir):
    _wait_surface()
    time.sleep(0.7)
    print("[1] Hauptmenü")
    shot("01_menu.png", outdir)
    pygame.event.post(pygame.event.Event(pygame.QUIT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(_HERE, "shots"))
    ap.add_argument("--flow", choices=["full", "menu"], default="full")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    flow = flow_full if args.flow == "full" else flow_menu
    threading.Thread(target=flow, args=(args.outdir,), daemon=True).start()

    import main as game   # importiert NICHT auto-startend (if __name__ == '__main__')
    try:
        game.main()        # blockiert bis QUIT, dann pygame.quit()+sys.exit()
    except SystemExit:
        pass
    print("fertig.")


if __name__ == "__main__":
    main()

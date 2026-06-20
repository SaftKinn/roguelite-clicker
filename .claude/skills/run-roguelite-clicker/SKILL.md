---
name: run-roguelite-clicker
description: Build, launch, drive and screenshot the roguelite-clicker Pygame game headlessly. Use when asked to run, start, launch, play, smoke-test, screenshot, or verify the game (main menu, gameplay, upgrade cards, boss waves, victory screen) without a real display.
---

# Run roguelite-clicker (Pygame, headless)

Ein 2D-Roguelite/Tower-Defense in **Python + Pygame** (Einstieg `main.py`, Spiel-Loop
in `main()`). Es gibt kein Build-System und keine Tests — Verifikation = Spiel laufen
lassen und anschauen.

Treiber ist **`.claude/skills/run-roguelite-clicker/driver.py`**: er startet das *echte*
`main.main()` headless über den SDL-Dummy-Treiber (kein Fenster, kein X11 — läuft auf
Windows **und** Linux) und fährt es von einem Controller-Thread aus mit synthetischen
Maus-/Tasten-Events. Screenshots vom lebenden Display landen in `shots/`.

> Alle Pfade unten sind relativ zum Projekt-Root (`roguelite-clicker/`).

## Prerequisites

Nur Pygame (numpy optional). Bereits vorhanden in dieser Umgebung — Verifikation:

```bash
python -m pip install pygame      # 2.6.1; meldet "already satisfied"
python -c "import pygame; print(pygame.version.ver)"   # -> 2.6.1
```

Kein Build/Bundle nötig.

## Run (Agent-Pfad) — der Treiber

Fährt den vollen Flow **Menü → Lauf starten → Level-up (F5) → Karte wählen →
Welle 99 (F4) → Welle 100, dann Sieg (F1)** und schreibt 5 PNGs nach `shots/`:

```bash
python ".claude/skills/run-roguelite-clicker/driver.py"
```

Erzeugt:
`shots/01_menu.png`, `02_playing.png` (mit XP-Bar), `03_levelup.png`
(„Level Up!"-Karten), `04_after_levelup.png`, `05_victory.png`.
**Bilder danach wirklich ansehen.**

Nur das Hauptmenü (schnell):

```bash
python ".claude/skills/run-roguelite-clicker/driver.py" --flow menu
```

Anderes Zielverzeichnis: `--outdir <DIR>`.

### Wie der Treiber das Spiel fährt (zum Erweitern)
- Headless via `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` (oben im Skript gesetzt,
  **vor** dem Pygame-Import).
- `main.main()` läuft auf dem **Main-Thread** (SDL erwartet das); der Flow läuft im
  Daemon-Thread und postet Events in dieselbe Queue.
- `click(x,y)` setzt die (gepatchte) Mausposition und postet `MOUSEBUTTONDOWN/UP`.
  `key(k)` postet `KEYDOWN`. Screenshots via `pygame.image.save(get_surface(), …)`.
- Eigenen Ablauf: neue Funktion à la `flow_full(outdir)` schreiben (klick-Koordinaten
  aus den Layout-Formeln in `game/main_menu.py` / `game/upgrade_menu.py`) und in
  `main()` als `--flow`-Option eintragen. Dev-Tasten F1–F5 (siehe `CLAUDE.md`)
  springen schnell zu Wellen/Clear bzw. erzwingen einen Levelup (F5).

## Direkte Invocation (nur eine UI-Fläche rendern)

Für PRs, die nur eine `draw_*`-Funktion oder ein Menü-Layout ändern (z. B.
Karten-Größe), ohne den ganzen Loop — Zustand selbst aufbauen und in ein PNG rendern:

```bash
python -c "
import os; os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
import pygame; pygame.init(); pygame.display.set_mode((1280,720))
from game.upgrade_menu import UpgradeMenu, UPGRADES, CARD_W, GAP, CARD_H, OVERLAY_MAX
m=UpgradeMenu(1280,720); m._load(); m.choices=UPGRADES[:3]
sx=(1280-(3*CARD_W+2*GAP))//2; sy=(720-CARD_H)//2+20
m.rects=[pygame.Rect(sx+i*(CARD_W+GAP),sy,CARD_W,CARD_H) for i in range(3)]
m.fade_alpha=OVERLAY_MAX
scr=pygame.display.get_surface(); scr.fill((40,42,60)); m.draw(scr)
pygame.image.save(scr,'.claude/skills/run-roguelite-clicker/shots/render_upgrade.png'); print('OK')
"
```

## Run (Mensch-Pfad)

```bash
python main.py
```

Öffnet ein echtes Fenster. **Headless nutzlos** (läuft, aber niemand sieht/klickt es) —
für die Container-Verifikation immer den Treiber nehmen.

## Gotchas (in dieser Umgebung ausgemessen)

- **`pygame.mouse.set_pos()` wirkt unter dem Dummy-Treiber nicht** — `get_pos()` bleibt
  `(0,0)`. Die Klick-Handler in `main.py` lesen `pygame.mouse.get_pos()` (einmal pro
  Frame, **nicht** `event.pos`). Darum **patcht der Treiber `pygame.mouse.get_pos`** auf
  eine steuerbare Position. Ohne diesen Patch klicken alle Menü-Buttons ins Leere.
- **`Warning: no fast renderer available`** bei `set_mode(…, SCALED)` — harmlos, der
  Dummy-Treiber hat keinen Hardware-Renderer; das Surface wird trotzdem korrekt bemalt.
- **Windows-Konsole (cp1252) crasht auf Umlauten/`→` in `print()`** — der Treiber setzt
  daher `sys.stdout.reconfigure(encoding="utf-8")` ganz oben.
- **`main.main()` ruft am Ende `sys.exit()`** (nach QUIT). Alle Screenshots **vor** dem
  QUIT-Post machen; der Daemon-Thread stirbt mit dem Prozess.
- **Timing ist zeitbasiert, nicht event-synchron:** der Controller `sleep`t zwischen den
  Schritten (z. B. ~0,8 s für den Karten-Fade nach F5, ~1,6 s für `WAVE_CLEAR_DELAY`
  70 Frames + Puffer). Auf langsamer Hardware ggf. die `time.sleep`-Werte erhöhen.
- **`save.json` wird beschrieben:** F4→Sieg bucht `best_wave=100` echt in den Spielstand
  (gitignored). Daher zeigt das Menü danach „Rekord: Welle 100".

## Troubleshooting

| Symptom | Ursache / Fix |
|---|---|
| `UnicodeEncodeError: 'charmap'` in `print` | cp1252-stdout; der `reconfigure`-Block oben im Treiber behebt es — bei eigenen Skripten übernehmen. |
| Menü-Klick passiert nichts, Flow hängt | `get_pos`-Patch fehlt/überschrieben, oder Koordinaten daneben — gegen die Layout-Formeln in `game/main_menu.py` prüfen. |
| `RuntimeError: Display-Surface kam nicht hoch` | `main.main()` startete nicht (Import-/Asset-Fehler) — Treiber-Output über der Meldung lesen. |
| Screenshot ist leer/schwarz | zu früh geschossen oder falscher State — `time.sleep` vor dem `shot()` erhöhen. |

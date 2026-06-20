import os
import random
import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT

_BASE      = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "assets", "Tiny Swords (Free Pack)", "Terrain")
_TILE_SIZE = 64
_GROUND_COL = 1   # Pixel-Analyse: col=1 row=1 ist der uniformste Gras-Tile
_GROUND_ROW = 1


def _load_ground_tile(color_idx: int) -> pygame.Surface:
    path  = os.path.join(_BASE, "Tileset", f"Tilemap_color{color_idx}.png")
    sheet = pygame.image.load(path).convert()
    x     = _GROUND_COL * _TILE_SIZE
    y     = _GROUND_ROW * _TILE_SIZE
    # copy() damit subsurface nicht an das Sheet gebunden bleibt
    return sheet.subsurface((x, y, _TILE_SIZE, _TILE_SIZE)).copy()


def _load_deco_pool() -> list[pygame.Surface]:
    """Lädt alle Busch- und Fels-Sprites als bereite Surfaces."""
    pool = []

    # Büsche: 1024×128 Sprite-Strip, 8 Frames à 128×128
    bush_dir = os.path.join(_BASE, "Decorations", "Bushes")
    for i in range(1, 5):
        path = os.path.join(bush_dir, f"Bushe{i}.png")
        try:
            sheet  = pygame.image.load(path).convert_alpha()
            frame  = sheet.subsurface((0, 0, 128, 128)).copy()
            scaled = pygame.transform.smoothscale(frame, (56, 56))
            pool.append(scaled)
        except Exception:
            pass

    # Felsen: 64×64 Einzelbilder
    rock_dir = os.path.join(_BASE, "Decorations", "Rocks")
    for i in range(1, 5):
        path = os.path.join(rock_dir, f"Rock{i}.png")
        try:
            img    = pygame.image.load(path).convert_alpha()
            scaled = pygame.transform.smoothscale(img, (48, 48))
            pool.append(scaled)
        except Exception:
            pass

    return pool


class Terrain:
    def __init__(self):
        color_idx = random.randint(1, 5)
        tile      = _load_ground_tile(color_idx)

        # Hintergrund einmalig "backen"
        self._bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        cols = SCREEN_WIDTH  // _TILE_SIZE + 1
        rows = SCREEN_HEIGHT // _TILE_SIZE + 1
        for row in range(rows):
            for col in range(cols):
                self._bg.blit(tile, (col * _TILE_SIZE, row * _TILE_SIZE))

        # Dekorationen zufällig verteilen
        pool      = _load_deco_pool()
        cx, cy    = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        excl_r    = 90           # Freiraum um den Turm
        n         = random.randint(14, 22)
        self._decos: list[tuple] = []
        attempts  = 0

        while len(self._decos) < n and attempts < 800:
            attempts += 1
            surf = random.choice(pool)
            # Mindestabstand zum Rand (halbe Sprite-Breite + 4px)
            pad = surf.get_width() // 2 + 4
            x   = random.randint(pad, SCREEN_WIDTH  - pad)
            y   = random.randint(pad, SCREEN_HEIGHT - pad)
            # Turmbereich freihalten (kreisförmig)
            if ((x - cx) ** 2 + (y - cy) ** 2) < excl_r ** 2:
                continue
            # Mindestabstand zwischen Dekorationen (verhindert Stapeln)
            too_close = any(
                ((x - dx) ** 2 + (y - dy) ** 2) < 40 ** 2
                for (_, dx, dy) in self._decos
            )
            if too_close:
                continue
            self._decos.append((surf, x - surf.get_width() // 2,
                                       y - surf.get_height() // 2))

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self._bg, (0, 0))
        for surf, x, y in self._decos:
            screen.blit(surf, (x, y))

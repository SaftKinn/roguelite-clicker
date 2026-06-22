import os
import random
import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT
from . import sprite_loader

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


def _scatter_decos() -> list[tuple]:
    """Verteilt Büsche/Felsen zufällig über den Tiny-Swords-Grasboden, hält den
    Turmbereich (Mitte) frei und verhindert Überlappen. Liste von (surf, x, y)."""
    pool   = _load_deco_pool()
    if not pool:
        return []
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    excl_r = 90           # Freiraum um den Turm
    n      = random.randint(14, 22)
    decos: list[tuple] = []
    attempts = 0
    while len(decos) < n and attempts < 800:
        attempts += 1
        surf = random.choice(pool)
        pad  = surf.get_width() // 2 + 4   # Mindestabstand zum Rand
        x    = random.randint(pad, SCREEN_WIDTH  - pad)
        y    = random.randint(pad, SCREEN_HEIGHT - pad)
        if ((x - cx) ** 2 + (y - cy) ** 2) < excl_r ** 2:
            continue                       # Turmbereich kreisförmig freihalten
        too_close = any(((x - dx) ** 2 + (y - dy) ** 2) < 40 ** 2
                        for (_, dx, dy) in decos)
        if too_close:
            continue
        decos.append((surf, x - surf.get_width() // 2, y - surf.get_height() // 2))
    return decos


class Terrain:
    def __init__(self, tier: int = 0):
        self.tier = tier                    # welches Biom dieser gebackene BG zeigt
        self._bg  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        bg_tex = sprite_loader.load_tier_background(tier, (SCREEN_WIDTH, SCREEN_HEIGHT))
        if bg_tex is not None:
            # Tier-Voll-Textur (Friedhof/Lava/Eis): bildschirmfüllend gebacken. Sie bringt
            # eigene Details (Knochen, Lava, Kristalle) mit → keine Tiny-Swords-Decos drüber.
            self._bg.blit(bg_tex, (0, 0))
            self._decos: list[tuple] = []
        else:
            # Fallback (Golden Rule 5): Tiny-Swords-Gras gekachelt + Büsche/Felsen gestreut.
            tile = _load_ground_tile(random.randint(1, 5))
            cols = SCREEN_WIDTH  // _TILE_SIZE + 1
            rows = SCREEN_HEIGHT // _TILE_SIZE + 1
            for row in range(rows):
                for col in range(cols):
                    self._bg.blit(tile, (col * _TILE_SIZE, row * _TILE_SIZE))
            self._decos = _scatter_decos()

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self._bg, (0, 0))
        for surf, x, y in self._decos:
            screen.blit(surf, (x, y))

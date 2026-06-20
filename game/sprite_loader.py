import os
import pygame
from . import balance

_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "assets", "Tiny Swords (Free Pack)", "Units", "Red Units")


def _px(p: int) -> int:
    """Globale Sprite-Vergrößerung (SPRITE_SCALE, ADR 007) auf eine Ziel-Pixelgröße."""
    return max(1, round(p * balance.SPRITE_SCALE))

def _epx(p: int) -> int:
    """Wie _px, aber zusätzlich um ENEMY_SPRITE_SCALE — für Gegner-Körper (etwas größer als Turm)."""
    return max(1, round(p * balance.SPRITE_SCALE * balance.ENEMY_SPRITE_SCALE))

_ENEMY_PX = 48    # einheitliche Größe für alle normalen Gegner
_BOSS_PX  = 96
_SBOSS_PX = 144


def _load_strip(rel_path: str, frame_size: int, target_px: int) -> list[pygame.Surface]:
    path  = os.path.join(_BASE, rel_path)
    sheet = pygame.image.load(path).convert_alpha()
    n     = sheet.get_width() // frame_size
    return [
        pygame.transform.smoothscale(
            sheet.subsurface((i * frame_size, 0, frame_size, frame_size)),
            (_epx(target_px), _epx(target_px))
        )
        for i in range(n)
    ]


def _both_dirs(frames: list) -> tuple[list, list]:
    return frames, [pygame.transform.flip(f, True, False) for f in frames]


def load_warrior(px: int = _ENEMY_PX):
    return _both_dirs(_load_strip("Warrior/Warrior_Run.png", 192, px))

def load_archer(px: int = _ENEMY_PX):
    return _both_dirs(_load_strip("Archer/Archer_Run.png", 192, px))

def load_pawn(px: int = _ENEMY_PX):
    return _both_dirs(_load_strip("Pawn/Pawn_Run.png", 192, px))

def load_monk(px: int = _ENEMY_PX):
    return _both_dirs(_load_strip("Monk/Run.png", 192, px))

def load_lancer(px: int = _BOSS_PX):
    return _both_dirs(_load_strip("Lancer/Lancer_Run.png", 320, px))


_BLACK_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "assets", "Tiny Swords (Free Pack)", "Units", "Black Units")


def _load_black_strip(rel_path: str, frame_size: int, target_px: int) -> list[pygame.Surface]:
    path  = os.path.join(_BLACK_BASE, rel_path)
    sheet = pygame.image.load(path).convert_alpha()
    n     = sheet.get_width() // frame_size
    return [
        pygame.transform.smoothscale(
            sheet.subsurface((i * frame_size, 0, frame_size, frame_size)),
            (_epx(target_px), _epx(target_px))
        )
        for i in range(n)
    ]


def load_black_archer_run(px: int = 48):
    path  = os.path.join(_BLACK_BASE, "Archer", "Archer_Run.png")
    sheet = pygame.image.load(path).convert_alpha()
    n     = sheet.get_width() // 192
    frames = [
        pygame.transform.smoothscale(
            sheet.subsurface((i * 192, 0, 192, 192)),
            (_epx(px), _epx(px))
        )
        for i in range(n)
    ]
    return _both_dirs(frames)


def load_black_archer_shoot(px: int = 48):
    return _both_dirs(_load_black_strip("Archer/Archer_Shoot.png", 192, px))


def load_arrow(size: int = 20):
    path = os.path.join(_BLACK_BASE, "Archer", "Arrow.png")
    surf = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(surf, (_px(size), _px(size)))


def load_monk_heal(px: int = 44):
    return _both_dirs(_load_black_strip("Monk/Heal.png", 192, px))


def load_heal_effect(size: int = 64):
    path  = os.path.join(_BLACK_BASE, "Monk", "Heal_Effect.png")
    sheet = pygame.image.load(path).convert_alpha()
    n     = sheet.get_width() // 192
    return [
        pygame.transform.smoothscale(
            sheet.subsurface((i * 192, 0, 192, 192)),
            (_px(size), _px(size))
        )
        for i in range(n)
    ]


def load_black_warrior_run(px: int = 48):
    path = os.path.join(_BLACK_BASE, "Warrior", "Warrior_Run.png")
    sheet = pygame.image.load(path).convert_alpha()
    n = sheet.get_width() // 192
    frames = [pygame.transform.smoothscale(sheet.subsurface((i*192, 0, 192, 192)), (_epx(px), _epx(px))) for i in range(n)]
    return _both_dirs(frames)

def load_black_warrior_attack(idx: int, px: int = 48):
    """idx = 1 or 2 (Warrior_Attack1.png / Warrior_Attack2.png)"""
    path = os.path.join(_BLACK_BASE, "Warrior", f"Warrior_Attack{idx}.png")
    sheet = pygame.image.load(path).convert_alpha()
    n = sheet.get_width() // 192
    frames = [pygame.transform.smoothscale(sheet.subsurface((i*192, 0, 192, 192)), (_epx(px), _epx(px))) for i in range(n)]
    return _both_dirs(frames)

_LANCER_ATK_NAMES = [
    "Lancer_Right_Attack.png",
    "Lancer_UpRight_Attack.png",
    "Lancer_Up_Attack.png",
    "Lancer_DownRight_Attack.png",
    "Lancer_Down_Attack.png",
]

def load_black_lancer_run(px: int = 96):
    path = os.path.join(_BLACK_BASE, "Lancer", "Lancer_Run.png")
    sheet = pygame.image.load(path).convert_alpha()
    n = sheet.get_width() // 320
    frames = [pygame.transform.smoothscale(sheet.subsurface((i*320, 0, 320, 320)), (_epx(px), _epx(px))) for i in range(n)]
    return _both_dirs(frames)

def load_black_lancer_attacks(px: int = 96):
    """Returns list of 5 (frames_r, frames_l) tuples: Right, UpRight, Up, DownRight, Down."""
    result = []
    for name in _LANCER_ATK_NAMES:
        path = os.path.join(_BLACK_BASE, "Lancer", name)
        sheet = pygame.image.load(path).convert_alpha()
        n = sheet.get_width() // 320
        frames = [pygame.transform.smoothscale(sheet.subsurface((i*320, 0, 320, 320)), (_epx(px), _epx(px))) for i in range(n)]
        result.append(_both_dirs(frames))
    return result


def load_cannonball(size: int = 20):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "Tiny Swords (Free Pack)", "Cannonball.png")
    surf = pygame.image.load(path).convert_alpha()
    # Falls noch weißer Hintergrund vorhanden: transparent setzen
    try:
        import numpy as np
        arr   = pygame.surfarray.pixels3d(surf)
        alpha = pygame.surfarray.pixels_alpha(surf)
        alpha[(arr[:, :, 0] > 235) & (arr[:, :, 1] > 235) & (arr[:, :, 2] > 235)] = 0
        del arr, alpha
    except ImportError:
        pass
    # Auf opake Pixel zuschneiden → Ball füllt das Geschoss-Quadrat
    bounds = surf.get_bounding_rect(min_alpha=1)
    if bounds.width > 0 and bounds.height > 0:
        surf = surf.subsurface(bounds).copy()
    return pygame.transform.smoothscale(surf, (_px(size), _px(size)))

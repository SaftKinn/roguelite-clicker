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


_DRACHE_WALK_FRAMES = 8   # Frames im horizontalen Walk-Strip (prozedural via tools/animate_walk-Logik)


def load_drache_superboss(target_w: int = 240):
    """SuperBoss-Drache — geerdeter Walk-Zyklus (Seitenansicht, Kopf links).

    Quelle: `assets/custom/drache_superboss_walk.png`, ein horizontaler Strip aus
    `_DRACHE_WALK_FRAMES` gleich breiten Frames. Aus dem freigestellten Standbild
    (`drache_superboss_static.png`) prozedural erzeugt: fußverankertes Wippen +
    Squash/Stretch + leichtes Neigen (der Drache läuft am Boden, schwebt NICHT).
    Glatt schattiertes Art → mit `smoothscale` skaliert; Seitenverhältnis bleibt
    erhalten (auf `target_w` Breite, Höhe proportional).

    Roh-Bild blickt nach LINKS → das ist `_frames_l`, der Flip ergibt `_frames_r`.
    Gibt `(frames_r, frames_l)` zurück; leere Listen, falls das Asset fehlt (Fallback
    auf gezeichnetes Primitiv greift dann in der SuperBoss-Klasse, Golden Rule 5)."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "custom", "drache_superboss_walk.png")
    sheet  = pygame.image.load(path).convert_alpha()
    fw     = sheet.get_width() // _DRACHE_WALK_FRAMES
    fh     = sheet.get_height()
    th     = max(1, round(fh * target_w / fw))   # Höhe proportional zur Zielbreite
    frames_l, frames_r = [], []
    for i in range(_DRACHE_WALK_FRAMES):
        frame = sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh)).copy()
        frame = pygame.transform.smoothscale(frame, (target_w, th))
        frames_l.append(frame)
        frames_r.append(pygame.transform.flip(frame, True, False))
    return frames_r, frames_l


# --- Custom-Gegner aus AutoSprite (eigene Spritesheets in assets/custom/) ----------

_CUSTOM_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "custom")


def _load_custom_strip(filename: str, target_px: int) -> list[pygame.Surface]:
    """Horizontaler Spritesheet-Strip aus assets/custom/ mit quadratischen Frames.

    Die Frame-Breite wird aus der Sheet-Höhe abgeleitet (Frames sind quadratisch) —
    so ist der Loader robust gegen die Frame-Anzahl, die AutoSprite exportiert: egal
    ob 4, 6 oder 8 Frames, n = Breite // Höhe. Skaliert wie die übrigen Gegner via
    _epx. Erwartet ein nach RECHTS blickendes Roh-Sprite."""
    path  = os.path.join(_CUSTOM_BASE, filename)
    sheet = pygame.image.load(path).convert_alpha()
    fs    = sheet.get_height()                 # quadratische Frames: Breite == Höhe
    n     = max(1, sheet.get_width() // fs)
    return [
        pygame.transform.smoothscale(
            sheet.subsurface((i * fs, 0, fs, fs)),
            (_epx(target_px), _epx(target_px))
        )
        for i in range(n)
    ]


def load_orc_warrior_run(px: int = _ENEMY_PX):
    """Orc-Warrior Lauf-Animation (AutoSprite-Sheet: assets/custom/orc_warrior_run.png).
    Roh-Sprite blickt nach RECHTS → _frames_r; der Flip ergibt _frames_l."""
    return _both_dirs(_load_custom_strip("orc_warrior_run.png", px))


def load_orc_warrior_attack(px: int = _ENEMY_PX):
    """Orc-Warrior Angriffs-Animation (assets/custom/orc_warrior_attack.png)."""
    return _both_dirs(_load_custom_strip("orc_warrior_attack.png", px))


def load_goblin_run(px: int = _ENEMY_PX):
    """Goblin Lauf-Animation (AutoSprite-Sheet: assets/custom/goblin_run.png).
    Roh-Sprite blickt nach RECHTS → _frames_r; der Flip ergibt _frames_l."""
    return _both_dirs(_load_custom_strip("goblin_run.png", px))


def load_necromancer_run(px: int = _ENEMY_PX):
    """Nekromant Lauf-Animation (AutoSprite-Sheet: assets/custom/necromancer_run.png).
    Roh-Sprite blickt nach RECHTS → _frames_r; der Flip ergibt _frames_l."""
    return _both_dirs(_load_custom_strip("necromancer_run.png", px))


def load_custom_enemy(name: str, px: int = _ENEMY_PX):
    """Generischer Reskin-Loader: assets/custom/<name>_run.png → (frames_r, frames_l).
    Für die Tier-Gegner (Untote/Dämonen/Drachen-Brut), die per animate_walk.py aus
    EINEM Standbild erzeugt werden. Roh-Sprite blickt nach RECHTS → _frames_r."""
    return _both_dirs(_load_custom_strip(f"{name}_run.png", px))


def _load_single(filename: str, target_px: int) -> pygame.Surface:
    """Eine transparente Einzel-PNG aus assets/custom/ — auf opake Pixel zugeschnitten,
    dann auf Zielgröße skaliert (Muster wie load_cannonball). Für Geschoss-/Cast-VFX
    der Fernkämpfer, die KEINE Lauf-Animation sind (Standbild, kein Strip)."""
    path = os.path.join(_CUSTOM_BASE, filename)
    surf = pygame.image.load(path).convert_alpha()
    bounds = surf.get_bounding_rect(min_alpha=1)
    if bounds.width and bounds.height:
        surf = surf.subsurface(bounds).copy()
    return pygame.transform.smoothscale(surf, (_px(target_px), _px(target_px)))


def load_enemy_shot(name: str, px: int = 18) -> pygame.Surface:
    """Eigenes Geschoss eines Fernkämpfers: assets/custom/<name>_shot.png (nach RECHTS)."""
    return _load_single(f"{name}_shot.png", px)


def load_enemy_muzzle(name: str, px: int = 40) -> pygame.Surface:
    """Abschuss-/Cast-Flash eines Fernkämpfers: assets/custom/<name>_cast.png (radial)."""
    return _load_single(f"{name}_cast.png", px)


# --- Tier-Boden-Texturen (Voll-Hintergrund je Biom, assets/custom/) ----------------

_TIER_BG_NAMES = ["tier1_ground", "tier2_ground", "tier3_ground"]   # 0=Untote 1=Dämonen 2=Drachen


def load_tier_background(tier: int, size: tuple[int, int]) -> pygame.Surface | None:
    """Voll-Bodentextur des Tier-Bioms, bildschirmfüllend per COVER skaliert.

    Quelle: assets/custom/tier{1..3}_ground.png — eine Top-Down-Textur (Leonardo,
    Tiny-Swords-Stil). Wird seitenverhältnis-erhaltend so skaliert, dass sie `size`
    voll abdeckt, dann mittig zugeschnitten (cover + center-crop): keine Verzerrung,
    keine Kachelnaht, der dunkle Rahmen-Rand der Vorlage fällt weg.

    Gibt None zurück, wenn das Asset fehlt oder bricht — der Aufrufer (Terrain) fällt
    dann auf den Tiny-Swords-Gras-Boden zurück (Golden Rule 5, Spiel crasht nie)."""
    if not (0 <= tier < len(_TIER_BG_NAMES)):
        return None
    path = os.path.join(_CUSTOM_BASE, f"{_TIER_BG_NAMES[tier]}.png")
    try:
        surf = pygame.image.load(path).convert()
    except Exception:
        return None
    if surf.get_size() == size:
        return surf                                # bereits exakt Zielgröße → 1:1, kein Resample
    tw, th = size
    sw, sh = surf.get_size()
    scale  = max(tw / sw, th / sh)                 # COVER: füllt beide Achsen, kein Verzerren
    scaled = pygame.transform.smoothscale(surf, (round(sw * scale), round(sh * scale)))
    x = (scaled.get_width()  - tw) // 2
    y = (scaled.get_height() - th) // 2
    return scaled.subsurface((x, y, tw, th)).copy()   # mittig auf Zielgröße zuschneiden


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

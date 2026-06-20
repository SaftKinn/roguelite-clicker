import os
import pygame

_UI_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "Tiny Swords (Free Pack)", "UI Elements", "UI Elements"
)

_img_cache:  dict = {}
_surf_cache: dict = {}

# ---------------------------------------------------------------------------
# Tight source bounds  (transparent padding removed – per pixel scan)
# ---------------------------------------------------------------------------
# Bars: 320×64 source.
# sy/sh = vertical tight crop (removes transparent top/bottom of sprite).
# full_h = original sprite height (used for proportional cap_d calculation).
_BAR_SRC = {
    "Big": {
        "lx": 40, "lw": 24, "mx": 128, "mw": 64, "rx": 256, "rw": 24,
        "sy": 9,  "sh": 51, "full_h": 64,
    },
    "Small": {
        "lx": 49, "lw": 15, "mx": 128, "mw": 64, "rx": 256, "rw": 15,
        "sy": 22, "sh": 19, "full_h": 64,
    },
}

# Labels: 448×640, row height 128 px, horizontal tight content only.
_SWD_SRC = {"lx": 26, "lw": 102, "mx": 192, "mw": 64, "rx": 320, "rw": 80, "rh": 128}
_RIB_SRC = {"lx": 43, "lw": 85,  "mx": 192, "mw": 64, "rx": 320, "rw": 84, "rh": 128}

# Buttons: 320×320, padded 64-px cells at x=0/128/256 (unchanged).
_BTN_L, _BTN_M, _BTN_R = 0, 128, 256
_BTN_CELL = 64


# ---------------------------------------------------------------------------
# Interne Hilfsfunktionen
# ---------------------------------------------------------------------------

def _img(rel: str) -> pygame.Surface:
    if rel not in _img_cache:
        _img_cache[rel] = pygame.image.load(
            os.path.join(_UI_BASE, rel)
        ).convert_alpha()
    return _img_cache[rel]


def _scale(surf: pygame.Surface, w: int, h: int) -> pygame.Surface:
    return pygame.transform.smoothscale(surf, (max(1, w), max(1, h)))


def _3slice(img: pygame.Surface,
            lx: int, lw: int, mx: int, mw: int, rx: int, rw: int,
            src_y: int, src_h: int,
            tw: int, th: int, cap_d: int,
            key: tuple) -> pygame.Surface:
    """
    Universeller 3-Slice-Assembler.
    src_y/src_h = vertikaler Quell-Bereich (Tight-Crop).
    cap_d       = Pixel-Breite jedes Endstücks im Ziel.
    """
    if key in _surf_cache:
        return _surf_cache[key]
    mid_d = max(1, tw - 2 * cap_d)
    surf  = pygame.Surface((tw, th), pygame.SRCALPHA)
    surf.blit(_scale(img.subsurface((lx, src_y, lw, src_h)), cap_d, th), (0, 0))
    surf.blit(_scale(img.subsurface((mx, src_y, mw, src_h)), mid_d, th), (cap_d, 0))
    surf.blit(_scale(img.subsurface((rx, src_y, rw, src_h)), cap_d, th), (tw - cap_d, 0))
    _surf_cache[key] = surf
    return surf


def _tile_fill(screen: pygame.Surface, rect: pygame.Rect,
               fill_img: pygame.Surface, fill_w: int, h: int) -> None:
    """Kachelt fill_img horizontal bis fill_w Pixel in rect."""
    if fill_w <= 0:
        return
    tile_key = ("tile", id(fill_img), h)
    if tile_key not in _surf_cache:
        _surf_cache[tile_key] = _scale(fill_img, 64, h)
    tile      = _surf_cache[tile_key]
    tw        = tile.get_width()
    x         = rect.x
    remaining = fill_w
    while remaining > 0:
        w = min(tw, remaining)
        screen.blit(tile.subsurface((0, 0, w, h)), (x, rect.y))
        x         += w
        remaining -= w


# ---------------------------------------------------------------------------
# HP-Bars  (BigBar_Base/Fill | SmallBar_Base/Fill)
# ---------------------------------------------------------------------------

def draw_bar(screen: pygame.Surface, rect: pygame.Rect,
             ratio: float, big: bool = True) -> None:
    """
    Tiny Swords HP-Bar. ratio 0–1 = Füllstand.

    Vertikaler Tight-Crop am Frame → kein transparenter Rand, kein grüner
    Hintergrund-Durchschein. Horizontaler Tight-Crop → Fill-Alignment exakt.
    """
    prefix = "Big" if big else "Small"
    ratio  = max(0.0, min(1.0, ratio))
    w, h   = rect.width, rect.height
    p      = _BAR_SRC[prefix]

    # cap_d proportional zur tatsächlichen Cap-Content-Breite im Quell-Sprite
    cap_d = max(4, p["lw"] * h // p["full_h"])

    # Rahmen: vertikal und horizontal tight gecroppt → vollständig opak
    frame = _3slice(
        _img(f"Bars/{prefix}Bar_Base.png"),
        p["lx"], p["lw"], p["mx"], p["mw"], p["rx"], p["rw"],
        p["sy"], p["sh"],
        w, h, cap_d, ("bar", prefix, w, h)
    )
    screen.blit(frame, rect.topleft)

    # Füllung nur im inneren Bereich (zwischen den Caps)
    inner_w = max(0, w - 2 * cap_d)
    fill_w  = max(0, int(inner_w * ratio))
    if fill_w > 0 and inner_w > 0:
        inner_rect = pygame.Rect(rect.x + cap_d, rect.y, inner_w, h)
        if big:
            # BigBar: texturierter Tile mit transparenten Rändern (zeigt Holz-Rahmen)
            _tile_fill(screen, inner_rect, _img("Bars/BigBar_Fill.png"), fill_w, h)
        else:
            # SmallBar: SmallBar_Fill hat nur 3px Opazität → sichtbarer Solid Fill
            pygame.draw.rect(screen, (255, 60, 60),
                             pygame.Rect(rect.x + cap_d, rect.y, fill_w, h))


# ---------------------------------------------------------------------------
# Buttons  (BigBlueButton / BigRedButton)
# ---------------------------------------------------------------------------

def _assemble_btn(img: pygame.Surface,
                  target_w: int, target_h: int,
                  cache_key: tuple) -> pygame.Surface:
    src_h = img.get_height()   # 320 px
    return _3slice(img,
                   _BTN_L, _BTN_CELL, _BTN_M, _BTN_CELL, _BTN_R, _BTN_CELL,
                   0, src_h,           # src_y=0, full height
                   target_w, target_h,
                   target_h,           # cap_d = Ziel-Höhe (quadratisch, bewährt)
                   cache_key)


def draw_button(screen: pygame.Surface, rect: pygame.Rect,
                label: str, font: pygame.font.Font,
                hovered: bool, disabled: bool,
                color: str = "Blue") -> None:
    if disabled:
        pygame.draw.rect(screen, (25, 25, 35), rect, border_radius=8)
        pygame.draw.rect(screen, (45, 45, 55), rect, width=1, border_radius=8)
        s = font.render(label, True, (70, 70, 80))
        screen.blit(s, (rect.centerx - s.get_width() // 2,
                        rect.centery - s.get_height() // 2))
        return
    state = "Pressed" if hovered else "Regular"
    surf  = _assemble_btn(
        _img(f"Buttons/Big{color}Button_{state}.png"),
        rect.width, rect.height,
        ("btn", color, hovered, rect.width, rect.height)
    )
    screen.blit(surf, rect.topleft)
    text_col = (255, 255, 220) if hovered else (255, 255, 255)
    s = font.render(label, True, text_col)
    screen.blit(s, (rect.centerx - s.get_width() // 2,
                    rect.centery - s.get_height() // 2))


# ---------------------------------------------------------------------------
# Label-Assembler  (row-basierte Sprites: Swords, BigRibbons)
# ---------------------------------------------------------------------------

def _assemble_label(img_path: str, p: dict, row: int,
                    tw: int, th: int, key: tuple) -> pygame.Surface:
    """
    3-Slice für Zeilen-basierte Label-Sprites.
    Tight-Crop pro Zeile (horizontal) → kein Lücken-Padding zwischen den Stücken.
    """
    if key in _surf_cache:
        return _surf_cache[key]
    src      = _img(img_path)
    row_h    = p["rh"]
    row_surf = src.subsurface((0, row * row_h, src.get_width(), row_h))
    cap_d    = th   # quadratische Endstücke (Cap-Breite = Ziel-Höhe)
    mid_d    = max(1, tw - 2 * cap_d)
    surf     = pygame.Surface((tw, th), pygame.SRCALPHA)
    surf.blit(_scale(row_surf.subsurface((p["lx"], 0, p["lw"], row_h)), cap_d, th), (0, 0))
    surf.blit(_scale(row_surf.subsurface((p["mx"], 0, p["mw"], row_h)), mid_d, th), (cap_d, 0))
    surf.blit(_scale(row_surf.subsurface((p["rx"], 0, p["rw"], row_h)), cap_d, th), (tw - cap_d, 0))
    _surf_cache[key] = surf
    return surf


# ---------------------------------------------------------------------------
# Sword-Label  (Swords.png, für Gegner-Counter)
# ---------------------------------------------------------------------------

def draw_sword_label(screen: pygame.Surface, rect: pygame.Rect,
                     label: str, font: pygame.font.Font,
                     row: int = 0) -> None:
    """Swords.png – Tight-Crop 3-Slice. row 0–4 = Farbvariante."""
    surf = _assemble_label("Swords/Swords.png", _SWD_SRC, row,
                           rect.width, rect.height,
                           ("sword", row, rect.width, rect.height))
    screen.blit(surf, rect.topleft)
    s = font.render(label, True, (60, 40, 20))
    screen.blit(s, (rect.centerx - s.get_width() // 2,
                    rect.centery - s.get_height() // 2))


# ---------------------------------------------------------------------------
# Ribbon-Label  (BigRibbons.png, für Wellen-Counter)
# ---------------------------------------------------------------------------

def draw_ribbon_label(screen: pygame.Surface, rect: pygame.Rect,
                      label: str, font: pygame.font.Font,
                      row: int = 0) -> None:
    """BigRibbons.png – Tight-Crop 3-Slice. row 0=blau, 1=rot, 2=gelb, 3=lila, 4=grau."""
    surf = _assemble_label("Ribbons/BigRibbons.png", _RIB_SRC, row,
                           rect.width, rect.height,
                           ("ribbon", row, rect.width, rect.height))
    screen.blit(surf, rect.topleft)
    s = font.render(label, True, (255, 255, 255))
    screen.blit(s, (rect.centerx - s.get_width() // 2,
                    rect.centery - s.get_height() // 2))


# ---------------------------------------------------------------------------
# Münzen-Icon  (Icon_03.png)
# ---------------------------------------------------------------------------

def draw_coin_icon(screen: pygame.Surface,
                   cx: int, cy: int, size: int = 32) -> None:
    """Coin-Icon zentriert an (cx, cy) in size×size."""
    key = ("coin", size)
    if key not in _surf_cache:
        _surf_cache[key] = _scale(_img("Icons/Icon_03.png"), size, size)
    icon = _surf_cache[key]
    screen.blit(icon, (cx - size // 2, cy - size // 2))


# ---------------------------------------------------------------------------
# Paper/Panel  (für Menü-Slots)
# ---------------------------------------------------------------------------

def draw_paper(screen: pygame.Surface, rect: pygame.Rect,
               special: bool = False) -> None:
    name = "SpecialPaper" if special else "RegularPaper"
    key  = ("paper", name, rect.width, rect.height)
    if key not in _surf_cache:
        raw = pygame.image.load(
            os.path.join(_UI_BASE, f"Papers/{name}.png")
        ).convert_alpha()
        _surf_cache[key] = _scale(raw, rect.width, rect.height)
    screen.blit(_surf_cache[key], rect.topleft)

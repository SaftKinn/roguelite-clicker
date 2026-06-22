"""Zentrales UI-Theme: wiederverwendbare „Glass"-Primitive + Palette.

Eine Quelle für den Look aller Screens (Hauptmenü, Shop, Karten, HUD …). Statt
in jedem Screen rohe `pygame.draw.rect`-Aufrufe mit hartkodierten Farben zu
streuen, ruft jeder Screen diese Helfer — so hebt sich der ganze Look an einer
Stelle. Alles Teure (Verläufe, Schatten, Glows, Panel-Füllungen) wird nach Form
gecacht und nur noch geblittet.

Gruppen-Farben (Rot/Blau/Gold/Weiß) bleiben in `balance.py` — hier liegt nur die
neutrale UI-Palette.
"""

import os
import pygame

# ---------------------------------------------------------------------------
# Palette — neutrale UI-Töne (Gruppen-Akzente kommen aus balance.GROUP_COLORS)
# ---------------------------------------------------------------------------
INK         = (10, 12, 20)      # tiefster Hintergrund (Vignette-Rand)
BACKDROP_HI = (26, 28, 44)      # Backdrop-Verlauf oben
BACKDROP_LO = (12, 13, 22)      # Backdrop-Verlauf unten

PANEL_HI    = (44, 48, 68)      # Panel-Verlauf oben (heller)
PANEL_LO    = (24, 26, 40)      # Panel-Verlauf unten (dunkler)
PANEL_SOFT  = (32, 35, 52)      # ruhiges Panel (Slots) oben
PANEL_SOFT_LO = (20, 22, 34)    # ruhiges Panel unten

STROKE      = (66, 70, 96)      # Standard-Rahmen
STROKE_SOFT = (48, 52, 72)      # dezenter Rahmen (inaktiv)

TEXT        = (236, 239, 250)   # Haupttext
TEXT_DIM    = (158, 162, 188)   # Sekundärtext
TEXT_FAINT  = (108, 112, 140)   # Hinweise/leise
GOLD        = (255, 214, 84)    # Akzent-Gold (Titel, Münzen)
GOLD_DIM    = (188, 156, 52)

SHADOW_ALPHA = 110              # Standard-Deckkraft Schlagschatten
PANEL_RADIUS = 14               # Standard-Eckenradius Panels

# ---------------------------------------------------------------------------
# Display-Font (optional): erste TTF aus assets/fonts/ wird für Titel genutzt,
# sonst Fallback auf Arial. So bleibt der Build risikolos ohne gebündelte Font.
# ---------------------------------------------------------------------------
_FONTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")


def _find_display_font() -> str | None:
    try:
        for fn in sorted(os.listdir(_FONTS_DIR)):
            if fn.lower().endswith((".ttf", ".otf")):
                return os.path.join(_FONTS_DIR, fn)
    except OSError:
        pass
    return None


_DISPLAY_FONT_FILE = _find_display_font()
_font_cache: dict = {}


def font(size: int, bold: bool = False, display: bool = False) -> pygame.font.Font:
    """Gecachter Font. `display=True` nutzt die gebündelte Titel-TTF (Fallback Arial)."""
    key = (size, bold, display)
    f = _font_cache.get(key)
    if f is None:
        if display and _DISPLAY_FONT_FILE:
            try:
                f = pygame.font.Font(_DISPLAY_FONT_FILE, size)
            except Exception:
                f = pygame.font.SysFont("Arial", size, bold=bold)
        else:
            f = pygame.font.SysFont("Arial", size, bold=bold)
        _font_cache[key] = f
    return f


# ---------------------------------------------------------------------------
# Verläufe & Blur (intern, gecacht)
# ---------------------------------------------------------------------------
_grad_cache:   dict = {}
_fill_cache:   dict = {}
_shadow_cache: dict = {}
_glow_cache:   dict = {}


def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def vgradient(w: int, h: int, top: tuple, bottom: tuple) -> pygame.Surface:
    """Vertikaler Verlauf als deckende SRCALPHA-Surface (gecacht)."""
    key = (w, h, top, bottom)
    surf = _grad_cache.get(key)
    if surf is None:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        denom = max(1, h - 1)
        for y in range(h):
            r, g, b = _lerp(top, bottom, y / denom)
            pygame.draw.line(surf, (r, g, b, 255), (0, y), (w, y))
        _grad_cache[key] = surf
    return surf


def _blur(surf: pygame.Surface, factor: int) -> pygame.Surface:
    """Billiger Blur via Down-/Upscale (smoothscale verschmiert weich)."""
    w, h = surf.get_size()
    sw, sh = max(1, w // factor), max(1, h // factor)
    small = pygame.transform.smoothscale(surf, (sw, sh))
    return pygame.transform.smoothscale(small, (w, h))


# ---------------------------------------------------------------------------
# Backdrop — voller Bildschirm-Hintergrund (Verlauf + Vignette), einmal gebacken
# ---------------------------------------------------------------------------
_backdrop_surf: pygame.Surface | None = None


def backdrop(screen: pygame.Surface) -> None:
    """Ersetzt screen.fill(BG_COLOR): dunkler Verlauf + weiche Vignette."""
    global _backdrop_surf
    w, h = screen.get_size()
    if _backdrop_surf is None or _backdrop_surf.get_size() != (w, h):
        base = vgradient(w, h, BACKDROP_HI, BACKDROP_LO).copy()
        # Vignette: dunkler Rahmen, der zur Mitte ausblendet (geblurrtes Rechteck-Loch).
        vig = pygame.Surface((w, h), pygame.SRCALPHA)
        vig.fill((*INK, 165))
        inner = pygame.Rect(0, 0, int(w * 0.82), int(h * 0.82))
        inner.center = (w // 2, h // 2)
        pygame.draw.rect(vig, (0, 0, 0, 0), inner,
                         border_radius=min(inner.w, inner.h) // 3)
        vig = _blur(vig, 8)
        base.blit(vig, (0, 0))
        _backdrop_surf = base
    screen.blit(_backdrop_surf, (0, 0))


def backdrop_region(screen: pygame.Surface, rect: pygame.Rect) -> None:
    """Blittet nur den Backdrop-Ausschnitt `rect` neu — als nahtlose Maske (Scroll-Kopf/Fuß)."""
    if _backdrop_surf is not None:
        screen.blit(_backdrop_surf, rect.topleft, area=rect)


# ---------------------------------------------------------------------------
# Panel — Glass-Karte: Verlaufs-Füllung + Top-Highlight + Rahmen (+ Schatten)
# ---------------------------------------------------------------------------
def _panel_fill(w: int, h: int, radius: int, top: tuple, bottom: tuple) -> pygame.Surface:
    """Abgerundete Verlaufs-Füllung mit eingebackenem Oberkante-Highlight (gecacht)."""
    key = (w, h, radius, top, bottom)
    out = _fill_cache.get(key)
    if out is None:
        grad = vgradient(w, h, top, bottom).copy()
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Glas-Glanz: zwei feine helle Linien direkt unter der Oberkante.
        pygame.draw.line(grad, (255, 255, 255, 42), (radius, 1), (w - radius, 1))
        pygame.draw.line(grad, (255, 255, 255, 18), (radius, 2), (w - radius, 2))
        out = grad
        _fill_cache[key] = out
    return out


def _shadow(w: int, h: int, radius: int, spread: int, alpha: int) -> pygame.Surface:
    key = (w, h, radius, spread, alpha)
    out = _shadow_cache.get(key)
    if out is None:
        pad = spread * 2
        base = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(base, (0, 0, 0, alpha), (pad, pad, w, h),
                         border_radius=radius + spread // 2)
        out = _blur(base, max(2, spread))
        _shadow_cache[key] = out
    return out


def drop_shadow(screen: pygame.Surface, rect: pygame.Rect, radius: int = PANEL_RADIUS,
                spread: int = 12, alpha: int = SHADOW_ALPHA, dy: int = 6) -> None:
    """Weicher Schlagschatten unter ein Rect (Tiefe / „schwebende Karte")."""
    pad = spread * 2
    surf = _shadow(rect.w, rect.h, radius, spread, alpha)
    screen.blit(surf, (rect.x - pad, rect.y - pad + dy))


def _glow(w: int, h: int, radius: int, color: tuple, spread: int, alpha: int) -> pygame.Surface:
    key = (w, h, radius, color, spread, alpha)
    out = _glow_cache.get(key)
    if out is None:
        pad = spread * 2
        base = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(base, (*color, alpha), (pad, pad, w, h),
                         border_radius=radius + spread // 2)
        out = _blur(base, max(2, spread))
        _glow_cache[key] = out
    return out


def accent_glow(screen: pygame.Surface, rect: pygame.Rect, color: tuple,
                radius: int = PANEL_RADIUS, spread: int = 14, alpha: int = 120) -> None:
    """Farbiger Außen-Glow hinter/um ein Rect (Hover/Aktiv)."""
    pad = spread * 2
    surf = _glow(rect.w, rect.h, radius, tuple(color), spread, alpha)
    screen.blit(surf, (rect.x - pad, rect.y - pad))


def panel(screen: pygame.Surface, rect: pygame.Rect, radius: int = PANEL_RADIUS,
          accent: tuple | None = None, hovered: bool = False,
          top: tuple = PANEL_HI, bottom: tuple = PANEL_LO,
          shadow: bool = True, stroke: bool = True) -> None:
    """Glass-Panel: Schatten + Verlaufs-Füllung + Highlight + Rahmen.

    `accent` färbt den Rahmen; `hovered` macht ihn breiter. Kapselt das frühere
    „Body + Rahmen + Kopfband"-Muster aller Screens.
    """
    if shadow:
        drop_shadow(screen, rect, radius)
    screen.blit(_panel_fill(rect.w, rect.h, radius, top, bottom), rect.topleft)
    if stroke:
        col = accent if accent else STROKE
        screen.blit(  # Rahmen über kleine SRCALPHA-Surface, damit Akzent leicht leuchtet
            _stroke_surf(rect.w, rect.h, radius, col, 2 if hovered else 1), rect.topleft)


_stroke_cache: dict = {}


def _stroke_surf(w: int, h: int, radius: int, color: tuple, width: int) -> pygame.Surface:
    key = (w, h, radius, tuple(color), width)
    out = _stroke_cache.get(key)
    if out is None:
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(out, (*color, 235), (0, 0, w, h), width=width, border_radius=radius)
        _stroke_cache[key] = out
    return out


def header_band(screen: pygame.Surface, rect: pygame.Rect, color: tuple,
                radius: int = PANEL_RADIUS) -> None:
    """Farbiges Kopfband oben in einem Panel (Gruppen-Akzent), als sanfter Verlauf."""
    band = _panel_fill(rect.w, rect.h, radius, _lerp(color, (255, 255, 255), 0.18),
                       _lerp(color, INK, 0.35))
    clip = screen.get_clip()
    # nur die obere Rundung zeigen: untere Ecken durch volle Höhe ohnehin gerundet,
    # daher Band-Surface ist genau rect-groß und schon korrekt gerundet.
    screen.blit(band, rect.topleft)
    screen.set_clip(clip)


# ---------------------------------------------------------------------------
# Text mit Schatten
# ---------------------------------------------------------------------------
def text(screen: pygame.Surface, f: pygame.font.Font, s: str, pos: tuple,
         color: tuple = TEXT, shadow: bool = True,
         shadow_color: tuple = (0, 0, 0)) -> pygame.Rect:
    """Text mit 1px-Schatten zeichnen. Gibt das Ziel-Rect zurück."""
    if shadow:
        sh = f.render(s, True, shadow_color)
        screen.blit(sh, (pos[0] + 1, pos[1] + 1))
    surf = f.render(s, True, color)
    return screen.blit(surf, pos)


def text_center(screen: pygame.Surface, f: pygame.font.Font, s: str, center: tuple,
                color: tuple = TEXT, shadow: bool = True,
                shadow_color: tuple = (0, 0, 0)) -> pygame.Rect:
    """Horizontal/vertikal zentrierter Text mit Schatten."""
    surf = f.render(s, True, color)
    pos = (center[0] - surf.get_width() // 2, center[1] - surf.get_height() // 2)
    return text(screen, f, s, pos, color, shadow, shadow_color)


def pill(screen: pygame.Surface, rect: pygame.Rect, accent: tuple | None = None,
         hovered: bool = False) -> None:
    """Stark gerundetes Mini-Panel (Münz-/Rekord-Anzeige, Header-Chips)."""
    panel(screen, rect, radius=rect.height // 2, accent=accent, hovered=hovered,
          top=PANEL_SOFT, bottom=PANEL_SOFT_LO, shadow=True)

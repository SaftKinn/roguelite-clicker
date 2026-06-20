import random
import pygame
from . import ui_loader
from .constants import BG_COLOR

UPGRADES = [
    {"id": "damage",    "name": "Mehr Schaden",    "desc": "+10 Schaden pro Kugel",   "icon": "Icon_05", "btn": "Red"},
    {"id": "speed",     "name": "Schnelle Kugeln", "desc": "+3 Kugelgeschwindigkeit",  "icon": "Icon_05", "btn": "Red"},
    {"id": "size",      "name": "Große Kugeln",    "desc": "+4 Kugelradius",           "icon": "Icon_06", "btn": "Blue"},
    {"id": "multishot", "name": "Dreifachschuss",  "desc": "3 Kugeln pro Klick",      "icon": "Icon_05", "btn": "Red"},
    {"id": "pierce",    "name": "Durchschlag",     "desc": "Kugeln treffen mehrere",  "icon": "Icon_05", "btn": "Red"},
    {"id": "max_hp",    "name": "Max HP",           "desc": "+25 Maximale HP",         "icon": "Icon_06", "btn": "Blue"},
]

CARD_W, CARD_H  = 200, 260
GAP             = 30
FADE_SPEED      = 10
OVERLAY_MAX     = 190
CARDS_THRESHOLD = 120

_ICON_SIZE  = 52
_ICON_Y     = 16
_NAME_Y     = 82
_DESC_Y     = 114
_HINT_Y     = 200


class UpgradeMenu:
    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w   = screen_w
        self.screen_h   = screen_h
        self.choices:list = []
        self.rects:  list = []
        self.fade_alpha  = 0
        self._overlay    = pygame.Surface((screen_w, screen_h))
        self._overlay.fill((0, 0, 0))
        self._ready      = False

    def _load(self) -> None:
        if self._ready:
            return
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_name  = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_desc  = pygame.font.SysFont("Arial", 14)
        self.font_hint  = pygame.font.SysFont("Arial", 12)
        # Button-Backgrounds (skaliert auf Kartengröße)
        self._btns = {}
        for color in ("Red", "Blue"):
            raw = ui_loader._img(f"Buttons/Small{color}SquareButton_Regular.png")
            self._btns[color] = pygame.transform.smoothscale(raw, (CARD_W, CARD_H))
        # Icons
        self._icons = {}
        for icon_id in ("Icon_05", "Icon_06"):
            raw = ui_loader._img(f"Icons/{icon_id}.png")
            self._icons[icon_id] = pygame.transform.smoothscale(raw, (_ICON_SIZE, _ICON_SIZE))
        self._ready = True

    def roll(self, obtained: set) -> None:
        one_time_owned = {u["id"] for u in UPGRADES
                          if u["id"] in obtained and u["id"] in {"multishot", "pierce"}}
        pool = [u for u in UPGRADES if u["id"] not in one_time_owned]
        self.choices = random.sample(pool, min(3, len(pool)))

        total_w = len(self.choices) * CARD_W + (len(self.choices) - 1) * GAP
        start_x = (self.screen_w - total_w) // 2
        start_y = (self.screen_h - CARD_H)  // 2 + 20
        self.rects = [
            pygame.Rect(start_x + i * (CARD_W + GAP), start_y, CARD_W, CARD_H)
            for i in range(len(self.choices))
        ]
        self.fade_alpha = 0

    def tick(self) -> None:
        if self.fade_alpha < OVERLAY_MAX:
            self.fade_alpha = min(OVERLAY_MAX, self.fade_alpha + FADE_SPEED)

    def handle_click(self, pos: tuple) -> str | None:
        if self.fade_alpha < CARDS_THRESHOLD:
            return None
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(pos):
                return self.choices[i]["id"]
        return None

    def draw(self, screen: pygame.Surface) -> None:
        self._load()
        mouse_pos = pygame.mouse.get_pos()

        self._overlay.set_alpha(int(self.fade_alpha))
        screen.blit(self._overlay, (0, 0))

        if self.fade_alpha < CARDS_THRESHOLD:
            return

        card_progress = (self.fade_alpha - CARDS_THRESHOLD) / (OVERLAY_MAX - CARDS_THRESHOLD)
        card_alpha    = int(card_progress * 255)

        title = self.font_title.render("Wähle ein Upgrade", True, (255, 220, 60))
        title.set_alpha(card_alpha)
        screen.blit(title, (self.screen_w // 2 - title.get_width() // 2,
                             self.screen_h // 4))

        for upgrade, rect in zip(self.choices, self.rects):
            hovered = rect.collidepoint(mouse_pos) and self.fade_alpha >= OVERLAY_MAX

            # Karten-Surface (nicht-SRCALPHA → set_alpha funktioniert für Fade)
            card = pygame.Surface((CARD_W, CARD_H))
            card.fill(BG_COLOR)   # Fallback-Hintergrund für transparente Ecken

            # Button-Hintergrund
            card.blit(self._btns[upgrade["btn"]], (0, 0))

            # Hover-Aufhellung
            if hovered:
                bright = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
                pygame.draw.rect(bright, (255, 255, 255, 35),
                                 (0, 0, CARD_W, CARD_H), border_radius=8)
                card.blit(bright, (0, 0))

            # Icon
            icon_surf = self._icons[upgrade["icon"]]
            card.blit(icon_surf, (CARD_W // 2 - _ICON_SIZE // 2, _ICON_Y))

            # Name + Beschreibung
            name_s = self.font_name.render(upgrade["name"], True, (255, 255, 255))
            desc_s = self.font_desc.render(upgrade["desc"], True, (210, 210, 230))
            card.blit(name_s, (CARD_W // 2 - name_s.get_width() // 2, _NAME_Y))
            card.blit(desc_s, (CARD_W // 2 - desc_s.get_width() // 2, _DESC_Y))

            # Hover-Hint
            if hovered:
                hint_s = self.font_hint.render("Klicken zum Wählen", True, (255, 240, 120))
                card.blit(hint_s, (CARD_W // 2 - hint_s.get_width() // 2, _HINT_Y))

            card.set_alpha(card_alpha)
            screen.blit(card, rect.topleft)

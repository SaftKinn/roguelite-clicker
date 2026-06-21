import random
import pygame
from . import ui_loader
from . import balance
from .constants import FPS

# Karten-Farbgruppen (ADR 025): ROT=Schaden, BLAU=Verteidigung, GOLD=Geld, WEISS=XP.
# `group` steuert die Akzentfarbe (balance.GROUP_COLORS). Beschreibungs-Zahlen kommen aus
# balance.py — eine Quelle der Wahrheit (Effekt + Text bleiben synchron).
_R, _B, _G, _W = balance.GROUP_RED, balance.GROUP_BLUE, balance.GROUP_GOLD, balance.GROUP_WHITE
UPGRADES = [
    # ROT — Schaden
    {"id": "damage",      "group": _R, "name": "Mehr Schaden",   "desc": f"+{balance.UPGRADE_DAMAGE} Schaden pro Kugel",          "icon": "Icon_05"},
    {"id": "attackspeed", "group": _R, "name": "Angriffstempo",  "desc": f"+{balance.UPGRADE_ATTACK_SPEED}/s Angriffstempo",      "icon": "Icon_05"},
    {"id": "speed",       "group": _R, "name": "Schnelle Kugeln","desc": f"+{balance.UPGRADE_BULLET_SPEED} Kugelgeschwindigkeit", "icon": "Icon_05"},
    {"id": "size",        "group": _R, "name": "Große Kugeln",   "desc": f"+{balance.UPGRADE_BULLET_SIZE} Kugelradius",           "icon": "Icon_06"},
    {"id": "multishot",   "group": _R, "name": "Dreifachschuss", "desc": f"{len(balance.MULTISHOT_ANGLES)} Schuss pro Klick",     "icon": "Icon_05"},
    {"id": "pierce",      "group": _R, "name": "Durchschlag",    "desc": "Kugeln treffen mehrere",                               "icon": "Icon_05"},
    {"id": "lifesteal_pct", "group": _R, "name": "Lebensraub",   "desc": f"+{int(balance.UPGRADE_LIFESTEAL_PCT*100)}% Schaden als HP/Treffer", "icon": "Icon_05"},
    {"id": "lifesteal_flat","group": _R, "name": "Vampirschlag", "desc": f"+{balance.UPGRADE_LIFESTEAL_FLAT} HP pro Treffer",     "icon": "Icon_05"},
    # BLAU — Verteidigung
    {"id": "max_hp",   "group": _B, "name": "Max HP",        "desc": f"+{balance.UPGRADE_MAX_HP} Maximale HP",                       "icon": "Icon_06"},
    {"id": "armor",    "group": _B, "name": "Rüstung",       "desc": f"-{int(balance.UPGRADE_ARMOR_PCT*100)}% Schaden (max {int(balance.ARMOR_CAP*100)}%)", "icon": "Icon_06"},
    {"id": "hp_regen", "group": _B, "name": "Regeneration",  "desc": f"+{balance.UPGRADE_HP_REGEN:.0f} HP pro Sekunde",              "icon": "Icon_06"},
    {"id": "thorns",   "group": _B, "name": "Dornen",        "desc": f"Nahkämpfer nehmen {int(balance.UPGRADE_THORNS_PCT*100)}% zurück", "icon": "Icon_06"},
    {"id": "dodge",    "group": _B, "name": "Ausweichen",    "desc": f"{int(balance.UPGRADE_DODGE_PCT*100)}% Chance, Treffer zu vermeiden", "icon": "Icon_06"},
    # GOLD — Geld (diesen Lauf)
    {"id": "coin_boost", "group": _G, "name": "Goldgier",    "desc": f"+{int(balance.UPGRADE_COIN_PCT*100)}% Münzen diesen Lauf",    "icon": "Icon_05"},
    # WEISS — XP (diesen Lauf)
    {"id": "xp_boost", "group": _W, "name": "Gelehrsamkeit", "desc": f"+{int(balance.UPGRADE_XP_PCT*100)}% XP diesen Lauf",          "icon": "Icon_06"},
    {"id": "reroll",   "group": _W, "name": "Neuwurf",       "desc": f"+{balance.UPGRADE_REROLL_CHARGES} Karten-Neuwurf",            "icon": "Icon_06"},
]

# Nur diese Karten sind one-time (max. 1× pro Lauf); alle anderen sind stapelbar.
_ONE_TIME_CARDS = {"multishot", "pierce"}

CARD_W, CARD_H  = 270, 260
GAP             = 30
FADE_SPEED      = 10
OVERLAY_MAX     = 190
CARDS_THRESHOLD = 120

_ICON_SIZE  = 52
_ICON_Y     = 14
_BAND_H     = 72     # farbiges Kopfband in der Gruppen-Akzentfarbe
_NAME_Y     = 88
_DESC_Y     = 122
_HINT_Y     = 200

# Getöntes Rundrechteck statt Button-Asset (Gold/Weiß haben keine PNGs, ADR 025) → das
# Textfeld ist nun fast kartenbreit, daher _TEXT_MAX_W großzügiger als beim alten roten Button.
_NAME_SIZE  = 20
_DESC_SIZE  = 14
_MIN_FONT   = 9
_TEXT_MAX_W = int(CARD_W * 0.86) - 16

_BODY_COLOR = (26, 28, 40)      # dunkler Kartengrund
_BORDER_W   = 3

# Reroll-Button (WEISS, ADR 025)
_REROLL_W, _REROLL_H = 230, 46
_REROLL_GAP_Y        = 26       # Abstand unter den Karten


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
        self._fonts:dict = {}   # (size, bold) -> Font, Cache statt Neuerzeugung pro Frame
        self._input_lock = 0    # Frames Klick-Sperre nach Levelup (ADR 009)
        self._count      = balance.DEFAULT_CARD_COUNT   # gemerkt für Reroll (gleiche Anzahl)

    def _font(self, size: int, bold: bool) -> pygame.font.Font:
        key = (size, bold)
        f = self._fonts.get(key)
        if f is None:
            f = pygame.font.SysFont("Arial", size, bold=bold)
            self._fonts[key] = f
        return f

    def _fit_render(self, text: str, size: int, bold: bool, color: tuple) -> pygame.Surface:
        """Verkleinert die Schrift, bis der Text in _TEXT_MAX_W passt, dann rendert er."""
        while size > _MIN_FONT and self._font(size, bold).size(text)[0] > _TEXT_MAX_W:
            size -= 1
        return self._font(size, bold).render(text, True, color)

    def _load(self) -> None:
        if self._ready:
            return
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_hint  = pygame.font.SysFont("Arial", 12)
        self.font_btn   = pygame.font.SysFont("Arial", 18, bold=True)
        # Icons (mit Fallback, falls ein Asset fehlt — Golden Rule 5)
        self._icons = {}
        for icon_id in ("Icon_05", "Icon_06"):
            try:
                raw = ui_loader._img(f"Icons/{icon_id}.png")
                self._icons[icon_id] = pygame.transform.smoothscale(raw, (_ICON_SIZE, _ICON_SIZE))
            except Exception:
                self._icons[icon_id] = None
        self._ready = True

    def roll(self, obtained: set, count: int = None) -> None:
        if count is not None:
            self._count = count
        one_time_owned = {u["id"] for u in UPGRADES
                          if u["id"] in obtained and u["id"] in _ONE_TIME_CARDS}
        pool = [u for u in UPGRADES if u["id"] not in one_time_owned]
        self.choices = random.sample(pool, min(self._count, len(pool)))

        total_w = len(self.choices) * CARD_W + (len(self.choices) - 1) * GAP
        start_x = (self.screen_w - total_w) // 2
        start_y = (self.screen_h - CARD_H)  // 2 + 20
        self.rects = [
            pygame.Rect(start_x + i * (CARD_W + GAP), start_y, CARD_W, CARD_H)
            for i in range(len(self.choices))
        ]
        self.fade_alpha = 0
        self._input_lock = round(balance.LEVELUP_INPUT_LOCK_S * FPS)   # 0.75 s Klick-Sperre

    def tick(self) -> None:
        if self.fade_alpha < OVERLAY_MAX:
            self.fade_alpha = min(OVERLAY_MAX, self.fade_alpha + FADE_SPEED)
        if self._input_lock > 0:
            self._input_lock -= 1

    def _clickable(self) -> bool:
        return self._input_lock <= 0 and self.fade_alpha >= CARDS_THRESHOLD

    def handle_click(self, pos: tuple) -> str | None:
        if not self._clickable():
            return None
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(pos):
                return self.choices[i]["id"]
        return None

    def reroll_button_rect(self) -> pygame.Rect:
        start_y = (self.screen_h - CARD_H) // 2 + 20
        y = start_y + CARD_H + _REROLL_GAP_Y
        return pygame.Rect(self.screen_w // 2 - _REROLL_W // 2, y, _REROLL_W, _REROLL_H)

    def handle_reroll_click(self, pos: tuple) -> bool:
        """True, wenn der Reroll-Button geklickt wurde (Aufrufer prüft/zieht die Charge)."""
        if not self._clickable():
            return False
        return self.reroll_button_rect().collidepoint(pos)

    def draw(self, screen: pygame.Surface, rerolls: int = 0) -> None:
        self._load()
        mouse_pos = pygame.mouse.get_pos()

        self._overlay.set_alpha(int(self.fade_alpha))
        screen.blit(self._overlay, (0, 0))

        if self.fade_alpha < CARDS_THRESHOLD:
            return

        card_progress = (self.fade_alpha - CARDS_THRESHOLD) / (OVERLAY_MAX - CARDS_THRESHOLD)
        card_alpha    = int(card_progress * 255)

        title = self.font_title.render("Level Up!  Wähle eine Karte", True, (255, 220, 60))
        title.set_alpha(card_alpha)
        screen.blit(title, (self.screen_w // 2 - title.get_width() // 2,
                             self.screen_h // 4))

        for upgrade, rect in zip(self.choices, self.rects):
            hovered = rect.collidepoint(mouse_pos) and self.fade_alpha >= OVERLAY_MAX
            accent  = balance.GROUP_COLORS[upgrade["group"]]

            # Getöntes Rundrechteck: dunkler Körper + farbiges Kopfband + Akzent-Rahmen.
            card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            pygame.draw.rect(card, (*_BODY_COLOR, 240), (0, 0, CARD_W, CARD_H), border_radius=12)
            pygame.draw.rect(card, (*accent, 255), (0, 0, CARD_W, _BAND_H),
                             border_top_left_radius=12, border_top_right_radius=12)
            pygame.draw.rect(card, (*accent, 255), (0, 0, CARD_W, CARD_H),
                             width=_BORDER_W, border_radius=12)

            if hovered:
                pygame.draw.rect(card, (255, 255, 255, 40), (0, 0, CARD_W, CARD_H), border_radius=12)

            # Icon (im Kopfband)
            icon_surf = self._icons.get(upgrade["icon"])
            if icon_surf is not None:
                card.blit(icon_surf, (CARD_W // 2 - _ICON_SIZE // 2, _ICON_Y))

            # Name + Beschreibung (Schrift schrumpft bei Bedarf)
            name_s = self._fit_render(upgrade["name"], _NAME_SIZE, True,  (255, 255, 255))
            desc_s = self._fit_render(upgrade["desc"], _DESC_SIZE, False, (215, 215, 230))
            card.blit(name_s, (CARD_W // 2 - name_s.get_width() // 2, _NAME_Y))
            card.blit(desc_s, (CARD_W // 2 - desc_s.get_width() // 2, _DESC_Y))

            if hovered and self._input_lock <= 0:
                hint_s = self.font_hint.render("Klicken zum Wählen", True, (255, 240, 120))
                card.blit(hint_s, (CARD_W // 2 - hint_s.get_width() // 2, _HINT_Y))

            card.set_alpha(card_alpha)
            screen.blit(card, rect.topleft)

        # Reroll-Button (nur wenn Charges vorhanden), unter den Karten
        if rerolls > 0:
            br = self.reroll_button_rect()
            bhov = br.collidepoint(mouse_pos) and self.fade_alpha >= OVERLAY_MAX
            accent = balance.GROUP_COLORS[balance.GROUP_WHITE]
            btn = pygame.Surface((br.width, br.height), pygame.SRCALPHA)
            pygame.draw.rect(btn, (*_BODY_COLOR, 240), (0, 0, br.width, br.height), border_radius=10)
            pygame.draw.rect(btn, (*accent, 255), (0, 0, br.width, br.height),
                             width=_BORDER_W, border_radius=10)
            if bhov:
                pygame.draw.rect(btn, (255, 255, 255, 40), (0, 0, br.width, br.height), border_radius=10)
            label = self.font_btn.render(f"Neu würfeln  ({rerolls})", True, (255, 255, 255))
            btn.blit(label, (br.width // 2 - label.get_width() // 2,
                             br.height // 2 - label.get_height() // 2))
            btn.set_alpha(card_alpha)
            screen.blit(btn, br.topleft)

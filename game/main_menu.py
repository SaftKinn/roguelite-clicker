import os
import pygame
from . import save_data as sd
from . import ui_loader
from . import balance
from . import theme
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR

BTN_W   = 270
BTN_H   = 52
BTN_GAP = 14

COLOR_BTN_BG     = (30, 30, 45)
COLOR_BTN_HOVER  = (50, 50, 70)
COLOR_BTN_BORDER = (70, 70, 95)

DIFFICULTIES = ["Leicht", "Normal", "Schwer"]
DIFF_MODIFIERS = {
    "Leicht": {"hp_mult": 0.7,  "spawn_bonus": 30},
    "Normal": {"hp_mult": 1.0,  "spawn_bonus": 0},
    "Schwer": {"hp_mult": 1.4,  "spawn_bonus": -25},
}

# Farbgruppen (ADR 025/026): jede Karte/jeder Kauf trägt eine `group`; die Farbe kommt
# zentral aus balance.GROUP_COLORS (eine Quelle für Karten + Shop). Der Shop ist nach diesen
# vier Gruppen in Spalten gegliedert (Schaden/Verteidigung/Geld/XP).
_R, _B, _G, _W = balance.GROUP_RED, balance.GROUP_BLUE, balance.GROUP_GOLD, balance.GROUP_WHITE

# Gestufte Käufe (capped, eigene Kostenliste je Stufe)
_TIERED = [
    {"id": "doppelschuss", "group": _R, "name": "Doppelschuss",
     "tiers": ["+1 Schuss (2 gesamt)", "+2 Schuss (3 gesamt)"],
     "costs": [balance.COST_DOPPELSCHUSS, balance.COST_DREIFACHSCHUSS]},
]

# Einmalige Käufe (Preise/Effekte zentral in balance.py)
_ONE_TIME = [
    {"id": "gold_boost", "group": _G, "name": "Goldene Kugeln", "desc": f"+{int((balance.GOLD_BOOST_MULT - 1) * 100)}% Münzen aus Kills", "cost": balance.COST_GOLD_BOOST},
    {"id": "extra_card", "group": _W, "name": "Vierte Karte",   "desc": f"Levelup zeigt {balance.EXTRA_CARD_COUNT} statt {balance.DEFAULT_CARD_COUNT} Karten", "cost": balance.COST_EXTRA_CARD},
]

# Unendlich steigerbare Upgrades (Preise/Effekte zentral in balance.py)
_INFINITE = [
    {"id": "start_damage",       "group": _R, "name": "Startschaden",      "per_level": f"+{balance.PERMANENT_DAMAGE_PER_LEVEL} Schaden",       "base_cost": balance.COST_START_DAMAGE},
    {"id": "start_attack_speed", "group": _R, "name": "Start-Tempo",       "per_level": f"+{balance.PERMANENT_ATTACK_SPEED_PER_LEVEL}/s Tempo",  "base_cost": balance.COST_START_ATTACK_SPEED},
    {"id": "start_bullet_size",  "group": _R, "name": "Start-Kugelgröße",  "per_level": f"+{balance.PERMANENT_BULLET_SIZE_PER_LEVEL} Radius",    "base_cost": balance.COST_START_BULLET_SIZE},
    {"id": "start_lifesteal",    "group": _R, "name": "Start-Lebensraub",  "per_level": f"+{balance.PERMANENT_LIFESTEAL_PER_LEVEL} HP/Treffer",  "base_cost": balance.COST_START_LIFESTEAL},
    {"id": "start_hp",           "group": _B, "name": "Start-HP",          "per_level": f"+{balance.PERMANENT_HP_PER_LEVEL} HP",                 "base_cost": balance.COST_START_HP},
    {"id": "coin_mult",          "group": _G, "name": "Münz-Meister",      "per_level": f"+{int(balance.PERMANENT_COIN_MULT_PER_LEVEL*100)}% Münzen (immer)", "base_cost": balance.COST_COIN_MULT},
    {"id": "xp_mult",            "group": _W, "name": "Weisheit",          "per_level": f"+{int(balance.PERMANENT_XP_MULT_PER_LEVEL*100)}% XP (immer)",       "base_cost": balance.COST_XP_MULT},
    {"id": "free_rerolls",       "group": _W, "name": "Glückshand",        "per_level": f"+{balance.PERMANENT_FREE_REROLLS_PER_LEVEL} Reroll/Lauf",            "base_cost": balance.COST_FREE_REROLLS},
]
_COST_MULT = balance.COST_MULT   # Preismultiplikator pro Stufe

# Spaltenreihenfolge des Shops (eine Spalte je Farbgruppe)
_GROUP_ORDER = (_R, _B, _G, _W)


def _shop_entries():
    """Alle Käufe als (kind, entry) — kind ∈ {'infinite','tiered','one_time'}."""
    return ([("infinite", e) for e in _INFINITE]
            + [("tiered", e)  for e in _TIERED]
            + [("one_time", e) for e in _ONE_TIME])

# Rückwärtskompatibilität für main.py-Import
IMPROVEMENTS = _ONE_TIME + _TIERED + [{"id": i["id"]} for i in _INFINITE]


def upgrade_cost(base_cost: int, level: int) -> int:
    return int(base_cost * (_COST_MULT ** level))


# ---------------------------------------------------------------------------
# Wiederverwendbare Button-Klasse
# ---------------------------------------------------------------------------

class Button:
    def __init__(self, rect: pygame.Rect, label: str, accent: tuple):
        self.rect   = rect
        self.label  = label
        self.accent = accent

    def is_hovered(self, mouse_pos: tuple) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font,
             mouse_pos: tuple, disabled: bool = False) -> None:
        r = self.rect
        if disabled:
            theme.panel(screen, r, radius=10, top=(24, 25, 34), bottom=(18, 19, 27),
                        stroke=True, shadow=False)
            theme.text_center(screen, font, self.label, r.center,
                              color=theme.TEXT_FAINT, shadow=False)
            return

        hovered = self.is_hovered(mouse_pos)
        if hovered:
            theme.accent_glow(screen, r, self.accent, radius=10, spread=14, alpha=95)
        theme.panel(screen, r, radius=10, accent=self.accent if hovered else None,
                    hovered=hovered)
        if hovered:
            # dünner Akzentstreifen links als „aktiv"-Marker
            bar = pygame.Rect(r.x + 6, r.y + 8, 4, r.height - 16)
            pygame.draw.rect(screen, self.accent, bar, border_radius=2)
        theme.text_center(screen, font, self.label, r.center,
                          color=theme.TEXT if hovered else theme.TEXT_DIM)


# ---------------------------------------------------------------------------
# Speicherstand-Auswahl (vor dem Hauptmenü)
# ---------------------------------------------------------------------------

class SlotSelectMenu:
    """Auswahl eines Speicherstands (Slot) VOR dem Hauptmenü. Zeigt je Slot eine
    Kurzinfo (Rekord-Welle, Münzen) oder „Leer"; ein gewählter Slot wird geladen."""
    _CARD_W, _CARD_H, _GAP = 620, 96, 22
    _DEL_W = 96

    def __init__(self):
        self._fonts_ready = False

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title = theme.font(46, bold=True, display=True)
            self.font_sub   = theme.font(16)
            self.font_name  = theme.font(24, bold=True)
            self.font_info  = theme.font(16)
            self._fonts_ready = True

    def _card_rect(self, i: int) -> pygame.Rect:
        n  = len(sd.SLOTS)
        total_h = n * self._CARD_H + (n - 1) * self._GAP
        sx = SCREEN_WIDTH // 2 - self._CARD_W // 2
        sy = SCREEN_HEIGHT // 2 - total_h // 2 + 10
        return pygame.Rect(sx, sy + i * (self._CARD_H + self._GAP),
                           self._CARD_W, self._CARD_H)

    def _del_rect(self, card: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(card.right - self._DEL_W - 12,
                           card.centery - 18, self._DEL_W, 36)

    def handle_click(self, pos: tuple, summaries: list):
        """Gibt ('pick', slot) | ('delete', slot) | None zurück."""
        for i, slot in enumerate(sd.SLOTS):
            card = self._card_rect(i)
            if summaries[i] is not None and self._del_rect(card).collidepoint(pos):
                return ("delete", slot)
            if card.collidepoint(pos):
                return ("pick", slot)
        return None

    def draw(self, screen: pygame.Surface, mouse_pos: tuple, summaries: list) -> None:
        self._load_fonts()
        theme.backdrop(screen)
        cx = SCREEN_WIDTH // 2
        theme.text_center(screen, self.font_title, "Speicherstand wählen",
                          (cx, SCREEN_HEIGHT // 5 + 24), color=theme.GOLD)

        accent = balance.GROUP_COLORS[balance.GROUP_BLUE]
        for i, slot in enumerate(sd.SLOTS):
            card    = self._card_rect(i)
            summary = summaries[i]
            hovered = card.collidepoint(mouse_pos)
            if hovered:
                theme.accent_glow(screen, card, accent, radius=theme.PANEL_RADIUS, spread=12, alpha=80)
            theme.panel(screen, card, radius=theme.PANEL_RADIUS,
                        accent=accent if hovered else None, hovered=hovered)
            theme.text(screen, self.font_name, f"Speicherstand {slot}",
                       (card.x + 22, card.y + 16), color=theme.TEXT)
            if summary is None:
                theme.text(screen, self.font_info, "Leer — neuer Lauf",
                           (card.x + 22, card.y + 52), color=(120, 180, 130), shadow=False)
            else:
                theme.text(screen, self.font_info,
                           f"Rekord: Welle {summary['best_wave']}   ·   Münzen: {summary['total_coins']}",
                           (card.x + 22, card.y + 52), color=theme.TEXT_DIM, shadow=False)
                # Löschen-Button
                dr = self._del_rect(card)
                dhov = dr.collidepoint(mouse_pos)
                red = (200, 80, 80)
                theme.panel(screen, dr, radius=8, accent=red if dhov else None,
                            hovered=dhov, top=(58, 30, 34), bottom=(40, 22, 26),
                            shadow=False)
                theme.text_center(screen, self.font_info, "Löschen", dr.center,
                                  color=(235, 180, 180))

        theme.text_center(screen, self.font_sub, "Klicke einen Speicherstand, um zu starten.",
                          (cx, SCREEN_HEIGHT - 52), color=theme.TEXT_FAINT, shadow=False)


# ---------------------------------------------------------------------------
# Hauptmenü
# ---------------------------------------------------------------------------

_MENU_DEFS = [
    {"id": "start",        "label": "Lauf Starten",    "color": (60, 200, 100)},
    {"id": "improvements", "label": "Verbesserungen",  "color": (160, 80, 220)},
    {"id": "bestiary",     "label": "Lexikon",          "color": (210, 160, 50)},
    {"id": "options",      "label": "Optionen",         "color": (60, 160, 220)},
    {"id": "quit",         "label": "Spiel Schließen", "color": (200, 60, 60)},
]


_GEAR_SIZE = 48   # Zahnrad-Button oben links

# Optionales Leonardo-Logo (assets/custom/menu_logo.png). Fehlt es, greift der
# gezeichnete Gold-Titel als Fallback (Golden Rule 5: nie ohne Asset crashen).
_LOGO_PATH    = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "custom", "menu_logo.png")
_LOGO_MAX_W   = 420   # Logo-Wappen: proportional in diese Box (Breite × Höhe) skaliert
_LOGO_MAX_H   = 150
_LOGO_TOP     = 40    # y-Oberkante des Wappens


class MainMenu:
    def __init__(self):
        self._fonts_ready = False
        total_h = len(_MENU_DEFS) * BTN_H + (len(_MENU_DEFS) - 1) * BTN_GAP
        sx = SCREEN_WIDTH  // 2 - BTN_W // 2
        sy = SCREEN_HEIGHT // 2 - total_h // 2 + 104   # tiefer → Platz für Wappen + Schriftzug oben
        self.buttons    = [
            Button(pygame.Rect(sx, sy + i * (BTN_H + BTN_GAP), BTN_W, BTN_H),
                   d["label"], d["color"])
            for i, d in enumerate(_MENU_DEFS)
        ]
        self.button_ids  = [d["id"] for d in _MENU_DEFS]
        self._gear_rect  = pygame.Rect(SCREEN_WIDTH - _GEAR_SIZE - 12, 12,
                                       _GEAR_SIZE, _GEAR_SIZE)
        self._gear_surf  = None
        self._logo_surf  = None   # None bis Lade-Versuch; False = nicht vorhanden

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title = theme.font(56, bold=True, display=True)
            self.font_sub   = theme.font(16)
            self.font_btn   = theme.font(20, bold=True)
            raw = ui_loader._img("Icons/Icon_12.png")
            self._gear_surf = pygame.transform.smoothscale(raw, (_GEAR_SIZE, _GEAR_SIZE))
            self._load_logo()
            self._fonts_ready = True

    def _load_logo(self) -> None:
        """Logo-PNG lazy laden; proportional in die Box (_LOGO_MAX_W × _LOGO_MAX_H). False = fehlt."""
        try:
            raw = pygame.image.load(_LOGO_PATH).convert_alpha()
            w, h = raw.get_width(), raw.get_height()
            scale = min(_LOGO_MAX_W / w, _LOGO_MAX_H / h, 1.0)
            if scale < 1.0:
                raw = pygame.transform.smoothscale(raw, (int(w * scale), int(h * scale)))
            self._logo_surf = raw
        except Exception:
            self._logo_surf = False

    def handle_click(self, pos: tuple, run_active: bool = False) -> str | None:
        if self._gear_rect.collidepoint(pos):
            return "options"
        for btn, bid in zip(self.buttons, self.button_ids):
            if bid == "improvements" and run_active:
                continue
            if btn.is_hovered(pos):
                return bid
        return None

    def draw(self, screen: pygame.Surface, mouse_pos: tuple,
             save: dict, run_active: bool = False, best_wave: int = 0) -> None:
        self._load_fonts()
        theme.backdrop(screen)

        cx = SCREEN_WIDTH // 2
        # Wappen-PNG (falls vorhanden) oben, darunter der Gold-Schriftzug; ohne PNG nur Schriftzug.
        if self._logo_surf:
            lw, lh = self._logo_surf.get_size()
            screen.blit(self._logo_surf, (cx - lw // 2, _LOGO_TOP))
            ty = _LOGO_TOP + lh + 2
        else:
            ty = SCREEN_HEIGHT // 4 - 24
        glow = self.font_title.render("ROGUELITE CLICKER", True, theme.GOLD_DIM)
        screen.blit(glow, (cx - glow.get_width() // 2 + 2, ty + 2))
        theme.text_center(screen, self.font_title, "ROGUELITE CLICKER",
                          (cx, ty + glow.get_height() // 2), color=theme.GOLD)
        sub_y = ty + glow.get_height() + 6
        theme.text_center(screen, self.font_sub, "Tower Defense  ·  Wave Survival",
                          (cx, sub_y + 8), color=theme.TEXT_DIM, shadow=False)

        # Münzen-Pill oben links (Icon + Zahl)
        coin_txt = str(save['total_coins'])
        cw = self.font_sub.size(coin_txt)[0]
        pill_rect = pygame.Rect(12, 12, 34 + cw + 18, 34)
        theme.pill(screen, pill_rect, accent=balance.GROUP_COLORS[balance.GROUP_GOLD])
        ui_loader.draw_coin_icon(screen, pill_rect.x + 20, pill_rect.centery, 22)
        theme.text(screen, self.font_sub, coin_txt,
                   (pill_rect.x + 36, pill_rect.centery - self.font_sub.get_height() // 2),
                   color=theme.GOLD)

        # Rekord-Pill (obere Leiste, zentriert — kollidiert nie mit den Buttons)
        if best_wave > 0:
            rt = f"Rekord: Welle {best_wave}"
            rw = self.font_sub.size(rt)[0]
            rec_rect = pygame.Rect(cx - (rw + 32) // 2, 12, rw + 32, 34)
            theme.pill(screen, rec_rect)
            theme.text_center(screen, self.font_sub, rt, rec_rect.center, color=theme.GOLD)

        for btn, bid in zip(self.buttons, self.button_ids):
            disabled = (bid == "improvements" and run_active)
            btn.draw(screen, self.font_btn, mouse_pos, disabled=disabled)

        # Zahnrad-Button (Einstellungen)
        if self._gear_surf:
            hovered = self._gear_rect.collidepoint(mouse_pos)
            if hovered:
                theme.pill(screen, self._gear_rect.inflate(6, 6))
            screen.blit(self._gear_surf, self._gear_rect.topleft)


# ---------------------------------------------------------------------------
# Optionen-Menü
# ---------------------------------------------------------------------------

class OptionsMenu:
    # Wählbare Bildraten für den FPS-Regler (Schieberegler wie die Lautstärke-Balken).
    _FRAMERATE_VALUES = [30, 60, 75, 90, 120, 140, 165, 200, 240]
    # Regler-Zeilen (Drag-Balken statt < >-Pfeile): Lautstärke + Bildrate.
    _SLIDER_KEYS = ("sfx", "music", "framerate")

    _ROWS = [
        {"key": "difficulty", "label": "Schwierigkeitsgrad",
         "values": DIFFICULTIES},
        {"key": "sfx",        "label": "SFX-Lautstärke",
         "values": [f"{i*10}%" for i in range(11)]},
        {"key": "music",      "label": "Musik-Lautstärke",
         "values": [f"{i*10}%" for i in range(11)]},
        {"key": "framerate",  "label": "FPS (Bildrate)",
         "values": _FRAMERATE_VALUES},
        {"key": "fps",        "label": "FPS anzeigen",
         "values": ["Aus", "An"]},
    ]
    _ROW_START = -110   # cy-Offset für erste Zeile (eine Zeile mehr → etwas höher starten)
    _ROW_STEP  =  64

    def __init__(self):
        self._fonts_ready = False
        self._dragging    = None      # "sfx" | "music" | "framerate" | None
        # Defaults: Normal, SFX 70%, Musik 50%, 140 FPS (Index 5), FPS-Anzeige Aus
        self._idx = {"difficulty": 1, "sfx": 7, "music": 5,
                     "framerate": self._FRAMERATE_VALUES.index(140), "fps": 0}
        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        self.back_btn = Button(
            pygame.Rect(cx - BTN_W // 2,
                        cy + self._ROW_START + len(self._ROWS) * self._ROW_STEP + 20,
                        BTN_W, BTN_H),
            "Zurück", (60, 160, 220)
        )
        # < > Buttons NUR für Nicht-Regler-Zeilen (Slider haben Drag-Balken statt Pfeile)
        self._arrow_idxs = [i for i, r in enumerate(self._ROWS)
                            if r["key"] not in self._SLIDER_KEYS]
        self._left_btns  = [
            Button(pygame.Rect(cx - 140, cy + self._ROW_START + i * self._ROW_STEP - 20, 44, 44),
                   "<", (180, 180, 200))
            for i in self._arrow_idxs
        ]
        self._right_btns = [
            Button(pygame.Rect(cx + 96, cy + self._ROW_START + i * self._ROW_STEP - 20, 44, 44),
                   ">", (180, 180, 200))
            for i in self._arrow_idxs
        ]

    _VOL_ICON_SIZE = 26
    _BAR_W         = 150
    _BAR_H         = 18

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title  = theme.font(38, bold=True, display=True)
            self.font        = theme.font(20, bold=True)
            self.font_sm     = theme.font(14)
            raw = ui_loader._img("Icons/Icon_11.png")
            self._note_surf  = pygame.transform.smoothscale(
                raw, (self._VOL_ICON_SIZE, self._VOL_ICON_SIZE))
            self._fonts_ready = True

    @property
    def difficulty(self) -> str:
        return DIFFICULTIES[self._idx["difficulty"]]

    @property
    def sfx_volume(self) -> float:
        return self._idx["sfx"] / 10.0

    @property
    def music_volume(self) -> float:
        return self._idx["music"] / 10.0

    @property
    def show_fps(self) -> bool:
        return self._idx["fps"] == 1

    @property
    def fps_value(self) -> int:
        """Gewählte Bildrate (treibt clock.tick UND die Feuerrate in main.py)."""
        return self._FRAMERATE_VALUES[self._idx["framerate"]]

    def get_modifiers(self) -> dict:
        return DIFF_MODIFIERS[self.difficulty]

    def get_settings(self) -> dict:
        return dict(self._idx)

    def load_settings(self, s: dict) -> None:
        for key, row in zip(
            [r["key"] for r in self._ROWS],
            self._ROWS
        ):
            if key in s:
                self._idx[key] = max(0, min(len(row["values"]) - 1, s[key]))

    def _vol_bar_rect(self, row_idx: int) -> pygame.Rect:
        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        ry = cy + self._ROW_START + row_idx * self._ROW_STEP
        return pygame.Rect(cx - self._BAR_W // 2, ry + 4, self._BAR_W, self._BAR_H)

    def _apply_drag(self, pos: tuple) -> None:
        for i, row in enumerate(self._ROWS):
            if row["key"] == self._dragging:
                bar   = self._vol_bar_rect(i)
                ratio = (pos[0] - bar.x) / bar.width
                n     = len(row["values"]) - 1   # Slider-Schrittzahl (11 für Lautstärke, sonst variabel)
                self._idx[self._dragging] = max(0, min(n, round(ratio * n)))
                return

    def start_drag(self, pos: tuple) -> str | None:
        """Startet Drag wenn auf einen Regler-Balken (Lautstärke/Bildrate) geklickt wird."""
        for i, row in enumerate(self._ROWS):
            if row["key"] in self._SLIDER_KEYS:
                if self._vol_bar_rect(i).inflate(0, 14).collidepoint(pos):
                    self._dragging = row["key"]
                    self._apply_drag(pos)
                    return row["key"]
        return None

    def update_drag(self, pos: tuple) -> str | None:
        """Aktualisiert Wert während Drag. Gibt Key zurück wenn geändert, sonst None."""
        if not self._dragging:
            return None
        old = self._idx[self._dragging]
        self._apply_drag(pos)
        return self._dragging if self._idx[self._dragging] != old else None

    def stop_drag(self) -> str | None:
        key           = self._dragging
        self._dragging = None
        return key

    def handle_click(self, pos: tuple) -> str | None:
        """Gibt 'back', '<key>_changed' oder None zurück."""
        if self.back_btn.is_hovered(pos):
            return "back"
        for btn_i, row_i in enumerate(self._arrow_idxs):
            row = self._ROWS[row_i]
            k   = row["key"]
            n   = len(row["values"])
            if self._left_btns[btn_i].is_hovered(pos):
                self._idx[k] = (self._idx[k] - 1) % n
                return f"{k}_changed"
            if self._right_btns[btn_i].is_hovered(pos):
                self._idx[k] = (self._idx[k] + 1) % n
                return f"{k}_changed"
        return None

    def draw(self, screen: pygame.Surface, mouse_pos: tuple) -> None:
        self._load_fonts()
        theme.backdrop(screen)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        theme.text_center(screen, self.font_title, "Optionen",
                          (cx, SCREEN_HEIGHT // 4 + 18), color=theme.GOLD)

        for i, row in enumerate(self._ROWS):
            ry  = cy + self._ROW_START + i * self._ROW_STEP
            key = row["key"]
            idx = self._idx[key]

            label_surf = self.font_sm.render(row["label"], True, (160, 160, 185))
            screen.blit(label_surf, (cx - label_surf.get_width() // 2, ry - 20))

            if key in self._SLIDER_KEYS:
                n = len(row["values"]) - 1
                # Lautstärke-Zeilen tragen das Musiknoten-Icon; der FPS-Regler nicht.
                if key in ("sfx", "music"):
                    icon_x = cx - self._BAR_W // 2 - self._VOL_ICON_SIZE - 8
                    icon_y = ry + 4 + (self._BAR_H - self._VOL_ICON_SIZE) // 2
                    screen.blit(self._note_surf, (icon_x, icon_y))

                bx, by = cx - self._BAR_W // 2, ry + 4
                fill_w = int(self._BAR_W * idx / n) if n else 0
                pygame.draw.rect(screen, (20, 55, 20),
                                 (bx, by, self._BAR_W, self._BAR_H), border_radius=5)
                if fill_w > 0:
                    pygame.draw.rect(screen, (60, 210, 80),
                                     (bx, by, fill_w, self._BAR_H), border_radius=5)
                # Drag-Handle (weißer Kreis am Ende des Füllstands)
                hx = bx + fill_w
                hy = by + self._BAR_H // 2
                dragging = self._dragging == key
                pygame.draw.circle(screen, (255, 255, 255) if dragging else (200, 240, 200),
                                   (hx, hy), 8 if dragging else 6)
                # Rechts: Prozent (Lautstärke) bzw. FPS-Zahl (Bildrate)
                label = f"{idx*10}%" if key in ("sfx", "music") else f"{row['values'][idx]} FPS"
                rl = self.font_sm.render(label, True, (180, 230, 180))
                screen.blit(rl, (bx + self._BAR_W + 18, by + (self._BAR_H - rl.get_height()) // 2))
            else:
                val = row["values"][idx]
                value_surf = self.font.render(val, True, (255, 255, 255))
                screen.blit(value_surf, (cx - value_surf.get_width() // 2, ry + 4))

                if key == "difficulty":
                    mod = self.get_modifiers()
                    desc = (f"Gegner-HP ×{mod['hp_mult']:.1f}   |   "
                            f"Spawn {'+' if mod['spawn_bonus'] >= 0 else ''}"
                            f"{mod['spawn_bonus']} Frames")
                    ds = self.font_sm.render(desc, True, (100, 100, 125))
                    screen.blit(ds, (cx - ds.get_width() // 2, ry + 30))

        # < > Buttons nur für Nicht-Lautstärke-Zeilen
        for btn_i in range(len(self._arrow_idxs)):
            self._left_btns[btn_i].draw(screen,  self.font, mouse_pos)
            self._right_btns[btn_i].draw(screen, self.font, mouse_pos)

        self.back_btn.draw(screen, self.font, mouse_pos)


# ---------------------------------------------------------------------------
# Lexikon / Bestiarium — alle Gegner mit Stats (nur gesehene werden enthüllt)
# ---------------------------------------------------------------------------

class BestiaryMenu:
    # Katalog: key = Klassenname (für "gesehen"-Abgleich), + Anzeige-Infos/Stats.
    _CATALOG = [
        {"key": "Warrior",      "name": "Krieger",      "role": "Nahkämpfer",
         "stats": ["HP-Faktor ×1.0", "Tempo: normal", "Belohnung: 1"]},
        {"key": "Archer",       "name": "Bogenschütze", "role": "Fernkämpfer",
         "stats": ["HP-Faktor ×0.4", "Tempo: schnell", "schießt Pfeile", "Belohnung: 1"]},
        {"key": "Lancer",       "name": "Lanzenträger", "role": "Tank",
         "stats": ["HP-Faktor ×3.0", "Tempo: langsam", "Belohnung: 3"]},
        {"key": "Monk",         "name": "Mönch",        "role": "Heiler",
         "stats": ["HP-Faktor ×0.6", "heilt 5 Gegner (+15)", "Belohnung: 3"]},
        {"key": "Goblin",       "name": "Goblin",       "role": "Schwarm",
         "stats": ["HP-Faktor ×2.5", "Tempo: sehr schnell", "Belohnung: 1"]},
        {"key": "OrcBerserker", "name": "Ork-Berserker","role": "Brecher",
         "stats": ["HP-Faktor ×25", "doppelter Schaden", "Belohnung: 4"]},
        {"key": "Necromancer",  "name": "Nekromant",    "role": "Beschwörer",
         "stats": ["HP-Faktor ×6.0", "beschwört Goblins", "Belohnung: 4"]},
        # --- Tier 1 — Untote (Welle 1–50) ---
        {"key": "SkeletonWarrior", "name": "Skelett-Krieger", "role": "Nahkämpfer · W1–50",
         "stats": ["HP-Faktor ×1.0", "Tempo: normal", "Belohnung: 1"]},
        {"key": "BoneSwarmling", "name": "Knochen-Schwarm", "role": "Schwarm · W1–50",
         "stats": ["HP-Faktor ×2.5", "Tempo: sehr schnell", "Belohnung: 1"]},
        {"key": "SkeletonArcher", "name": "Skelett-Schütze", "role": "Fernkämpfer · W1–50",
         "stats": ["HP-Faktor ×0.4", "schießt", "Belohnung: 1"]},
        {"key": "BoneColossus", "name": "Knochen-Koloss", "role": "Brecher · W1–50",
         "stats": ["HP-Faktor ×25", "doppelter Schaden", "Belohnung: 4"]},
        {"key": "Lich", "name": "Lich", "role": "Beschwörer · W1–50",
         "stats": ["HP-Faktor ×6.0", "beschwört Knochen-Schwarm", "Belohnung: 4"]},
        # --- Tier 2 — Dämonen (Welle 51–100) ---
        {"key": "ImpWarrior", "name": "Imp-Krieger", "role": "Nahkämpfer · W51–100",
         "stats": ["HP-Faktor ×1.0", "Tempo: normal", "Belohnung: 1"]},
        {"key": "Hellhound", "name": "Höllenhund", "role": "Schwarm · W51–100",
         "stats": ["HP-Faktor ×2.5", "Tempo: sehr schnell", "Belohnung: 1"]},
        {"key": "DemonCaster", "name": "Dämon-Magier", "role": "Fernkämpfer · W51–100",
         "stats": ["HP-Faktor ×0.4", "schießt", "Belohnung: 1"]},
        {"key": "PitBrute", "name": "Höllen-Brecher", "role": "Brecher · W51–100",
         "stats": ["HP-Faktor ×25", "doppelter Schaden", "Belohnung: 4"]},
        {"key": "DemonSummoner", "name": "Dämonen-Beschwörer", "role": "Beschwörer · W51–100",
         "stats": ["HP-Faktor ×6.0", "beschwört Höllenhunde", "Belohnung: 4"]},
        # --- Tier 3 — Drachen-Brut (Welle 101–150) ---
        {"key": "DrakeWarrior", "name": "Drakonier-Krieger", "role": "Nahkämpfer · W101–150",
         "stats": ["HP-Faktor ×1.0", "Tempo: normal", "Belohnung: 1"]},
        {"key": "Wyrmling", "name": "Wyrmling", "role": "Schwarm · W101–150",
         "stats": ["HP-Faktor ×2.5", "Tempo: sehr schnell", "Belohnung: 1"]},
        {"key": "DrakeArcher", "name": "Drakonier-Schütze", "role": "Fernkämpfer · W101–150",
         "stats": ["HP-Faktor ×0.4", "schießt", "Belohnung: 1"]},
        {"key": "ScaleTitan", "name": "Schuppen-Titan", "role": "Brecher · W101–150",
         "stats": ["HP-Faktor ×25", "doppelter Schaden", "Belohnung: 4"]},
        {"key": "DragonPriest", "name": "Drachen-Priester", "role": "Beschwörer · W101–150",
         "stats": ["HP-Faktor ×6.0", "beschwört Wyrmlinge", "Belohnung: 4"]},
        {"key": "Boss",         "name": "Boss",         "role": "alle 10 Wellen",
         "stats": ["HP ×6 der Basis", "tötet mit 1 Treffer", "Belohnung: 10"]},
        {"key": "SuperBoss",    "name": "Drache",       "role": "Welle 50 & 100",
         "stats": ["HP ×10 der Basis", "tötet mit 1 Treffer", "Belohnung: 50"]},
    ]
    _COLS = 3
    _CARD_W, _CARD_H, _GAP = 384, 150, 16
    _THUMB = 84
    _TOP = 104              # y-Start der ersten Karten-Reihe
    _HEADER_H = 100         # Kopfband (Titel/Fortschritt) — maskiert hochgescrollte Karten
    _SCROLL_STEP = 60       # Pixel pro Mausrad-Raste

    def __init__(self):
        self._fonts_ready = False
        self._thumbs = {}   # key -> Surface | False (Cache, lazy geladen)
        self._scroll = 0        # vertikaler Scroll-Offset (24 Einträge passen nicht auf einen Schirm)
        self._max_scroll = 0    # in draw aus der Inhaltshöhe berechnet
        cx = SCREEN_WIDTH // 2
        self.back_btn = Button(
            pygame.Rect(cx - BTN_W // 2, SCREEN_HEIGHT - BTN_H - 24, BTN_W, BTN_H),
            "Zurück", (60, 160, 220))

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title = theme.font(38, bold=True, display=True)
            self.font_name  = theme.font(20, bold=True)
            self.font_sm    = theme.font(13)
            self._fonts_ready = True

    def _thumb_for(self, key: str):
        """Sprite-Thumbnail eines Gegners (lazy, gecacht). False, wenn nicht ladbar."""
        if key in self._thumbs:
            return self._thumbs[key]
        surf = False
        try:
            from . import enemy as _e
            cls = getattr(_e, key)
            cls._load_sprites()
            frames = cls._frames_r or cls._frames_l
            if frames:
                fr = frames[0]
                scale = self._THUMB / max(fr.get_width(), fr.get_height())
                surf = pygame.transform.smoothscale(
                    fr, (max(1, int(fr.get_width() * scale)),
                         max(1, int(fr.get_height() * scale))))
        except Exception as exc:
            print(f"[Bestiary] Thumb {key}: {exc}")
        self._thumbs[key] = surf
        return surf

    def handle_click(self, pos: tuple) -> str | None:
        return "back" if self.back_btn.is_hovered(pos) else None

    def scroll(self, notches: int) -> None:
        """Mausrad: notches>0 = nach oben blättern. Clamp gegen _max_scroll (in draw gesetzt)."""
        self._scroll = max(0, min(self._max_scroll, self._scroll - notches * self._SCROLL_STEP))

    def _card_rect(self, i: int) -> pygame.Rect:
        col, row = i % self._COLS, i // self._COLS
        grid_w = self._COLS * self._CARD_W + (self._COLS - 1) * self._GAP
        sx = SCREEN_WIDTH // 2 - grid_w // 2
        sy = self._TOP - self._scroll
        return pygame.Rect(sx + col * (self._CARD_W + self._GAP),
                           sy + row * (self._CARD_H + self._GAP),
                           self._CARD_W, self._CARD_H)

    def draw(self, screen: pygame.Surface, mouse_pos: tuple, seen: set) -> None:
        self._load_fonts()
        theme.backdrop(screen)
        cx = SCREEN_WIDTH // 2
        # Scroll-Grenzen aus der Inhaltshöhe (24 Einträge ⇒ 8 Reihen, passt nicht mehr).
        rows      = -(-len(self._CATALOG) // self._COLS)
        foot_y    = SCREEN_HEIGHT - BTN_H - 32
        content_h = self._TOP + (rows - 1) * (self._CARD_H + self._GAP) + self._CARD_H
        self._max_scroll = max(0, content_h - foot_y)
        self._scroll     = max(0, min(self._max_scroll, self._scroll))

        for i, entry in enumerate(self._CATALOG):
            r = self._card_rect(i)
            if r.bottom < self._HEADER_H or r.top > foot_y:
                continue   # außerhalb des Sichtfensters → überspringen
            is_seen = entry["key"] in seen
            theme.panel(screen, r, radius=10,
                        top=theme.PANEL_SOFT, bottom=theme.PANEL_SOFT_LO, shadow=False)
            # Thumbnail-/Silhouetten-Feld links
            tb = pygame.Rect(r.x + 10, r.y + 10, self._THUMB + 12, r.height - 20)
            pygame.draw.rect(screen, (16, 17, 26), tb, border_radius=8)
            if is_seen:
                thumb = self._thumb_for(entry["key"])
                if thumb:
                    screen.blit(thumb, (tb.centerx - thumb.get_width() // 2,
                                        tb.centery - thumb.get_height() // 2))
                # Name + Rolle + Stats rechts
                tx = tb.right + 14
                name = self.font_name.render(entry["name"], True, (255, 235, 150))
                screen.blit(name, (tx, r.y + 14))
                role = self.font_sm.render(entry["role"], True, (150, 200, 230))
                screen.blit(role, (tx, r.y + 42))
                for j, line in enumerate(entry["stats"]):
                    s = self.font_sm.render(line, True, (185, 185, 205))
                    screen.blit(s, (tx, r.y + 64 + j * 18))
            else:
                q = self.font_title.render("?", True, (90, 90, 110))
                screen.blit(q, (tb.centerx - q.get_width() // 2,
                                tb.centery - q.get_height() // 2))
                lock = self.font_name.render("???", True, (110, 110, 130))
                screen.blit(lock, (tb.right + 14, r.centery - lock.get_height() // 2))

        # Kopf- und Fußband maskieren Karten, die über/unter das Sichtfenster ragen
        # (Backdrop-Ausschnitt neu blitten → nahtlos zum Verlauf).
        theme.backdrop_region(screen, pygame.Rect(0, 0, SCREEN_WIDTH, self._HEADER_H))
        foot_y = SCREEN_HEIGHT - BTN_H - 32
        theme.backdrop_region(screen, pygame.Rect(0, foot_y, SCREEN_WIDTH,
                                                  SCREEN_HEIGHT - foot_y))

        theme.text_center(screen, self.font_title, "Lexikon", (cx, 56), color=theme.GOLD)
        n_seen = sum(1 for e in self._CATALOG if e["key"] in seen)
        theme.text_center(screen, self.font_sm, f"{n_seen} / {len(self._CATALOG)} entdeckt",
                          (cx, 90), color=theme.TEXT_DIM, shadow=False)
        if self._max_scroll > 0:
            theme.text_center(screen, self.font_sm, "Mausrad zum Blättern",
                              (cx, foot_y + 12), color=theme.TEXT_FAINT, shadow=False)

        self.back_btn.draw(screen, self.font_name, mouse_pos)


# ---------------------------------------------------------------------------
# Verbesserungen-Menü
# ---------------------------------------------------------------------------

# Shop-Layout: vier Spalten (eine je Farbgruppe), Käufe untereinander (ADR 026).
SHOP_COL_W   = 288
SHOP_COL_GAP = 18
SHOP_SLOT_H  = 88
SHOP_ROW_GAP = 10
SHOP_GRID_TOP = 150


class ImprovementsMenu:
    def __init__(self):
        self._fonts_ready = False
        cx = SCREEN_WIDTH // 2
        self._grid_x = cx - (4 * SHOP_COL_W + 3 * SHOP_COL_GAP) // 2
        self.back_btn = Button(
            pygame.Rect(cx - BTN_W // 2, SCREEN_HEIGHT - 82, BTN_W, BTN_H),
            "Zurück", (60, 160, 220)
        )

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title = theme.font(38, bold=True, display=True)
            self.font       = theme.font(17, bold=True)
            self.font_sm    = theme.font(13)
            self._fonts_ready = True

    def _iter_shop_slots(self):
        """Layout-Iterator: yield (rect, kind, entry) je Kauf, gruppiert in 4 Farb-Spalten.
        EINE Quelle für draw() UND handle_click() → kein Drift zwischen Klick und Zeichnung."""
        cols = {g: [] for g in _GROUP_ORDER}
        for kind, e in _shop_entries():
            cols[e["group"]].append((kind, e))
        for ci, g in enumerate(_GROUP_ORDER):
            x = self._grid_x + ci * (SHOP_COL_W + SHOP_COL_GAP)
            for ri, (kind, e) in enumerate(cols[g]):
                y = SHOP_GRID_TOP + ri * (SHOP_SLOT_H + SHOP_ROW_GAP)
                yield pygame.Rect(x, y, SHOP_COL_W, SHOP_SLOT_H), kind, e

    def _entry_state(self, kind: str, e: dict, save: dict):
        """Gibt (state, cost) zurück. state ∈ buyable|locked|bought|maxed; cost = nächster Preis oder None."""
        upgrades = save.get("upgrades", {})
        if kind == "infinite":
            cost = upgrade_cost(e["base_cost"], upgrades.get(e["id"], 0))
            return ("buyable" if save["total_coins"] >= cost else "locked"), cost
        if kind == "tiered":
            lvl = upgrades.get(e["id"], 0)
            if lvl >= len(e["costs"]):
                return "maxed", None
            cost = e["costs"][lvl]
            return ("buyable" if save["total_coins"] >= cost else "locked"), cost
        # one_time
        if e["id"] in save["bought"]:
            return "bought", None
        cost = e["cost"]
        return ("buyable" if save["total_coins"] >= cost else "locked"), cost

    # ------------------------------------------------------------------

    def handle_click(self, pos: tuple, save: dict) -> str | None:
        if self.back_btn.is_hovered(pos):
            return "back"
        save.setdefault("upgrades", {})
        for rect, kind, e in self._iter_shop_slots():
            if not rect.collidepoint(pos):
                continue
            state, cost = self._entry_state(kind, e, save)
            if cost is None or save["total_coins"] < cost:
                return None
            save["total_coins"] -= cost
            if kind == "one_time":
                save["bought"].append(e["id"])
            else:
                save["upgrades"][e["id"]] = save["upgrades"].get(e["id"], 0) + 1
            sd.save(save)
            return None
        return None

    # ------------------------------------------------------------------

    def _draw_slot(self, screen, mouse_pos, rect: pygame.Rect,
                   color, name_txt, desc_txt, cost_txt, state: str) -> None:
        bought_like = state in ("bought", "maxed")
        hovered = rect.collidepoint(mouse_pos) and not bought_like
        active  = bought_like or hovered

        if hovered:
            theme.accent_glow(screen, rect, color, radius=10, spread=12, alpha=85)
        theme.panel(screen, rect, radius=10, accent=color if active else None,
                    hovered=hovered, top=theme.PANEL_SOFT, bottom=theme.PANEL_SOFT_LO)
        # Kopfband in Gruppenfarbe (oben)
        pygame.draw.rect(screen, color, (rect.x, rect.y, rect.width, 6),
                         border_top_left_radius=10, border_top_right_radius=10)

        rx, ry = rect.x, rect.y
        name_c = color if bought_like else theme.TEXT
        theme.text(screen, self.font, name_txt, (rx + 14, ry + 14), color=name_c)
        theme.text(screen, self.font_sm, desc_txt, (rx + 14, ry + 40),
                   color=theme.TEXT_DIM, shadow=False)

        sy = ry + rect.height - 24
        if bought_like:
            theme.text(screen, self.font_sm,
                       "Gekauft" if state == "bought" else "Max ausgebaut",
                       (rx + 14, sy), color=color, shadow=False)
        elif state == "locked":
            theme.text(screen, self.font_sm, f"{cost_txt}  (zu teuer)",
                       (rx + 14, sy), color=(190, 96, 96), shadow=False)
        else:  # buyable
            txt = "→ Klicken zum Kaufen" if hovered else cost_txt
            theme.text(screen, self.font_sm, txt, (rx + 14, sy),
                       color=color if hovered else theme.GOLD_DIM, shadow=False)

    def draw(self, screen: pygame.Surface, mouse_pos: tuple, save: dict) -> None:
        self._load_fonts()
        theme.backdrop(screen)
        cx       = SCREEN_WIDTH // 2
        upgrades = save.get("upgrades", {})

        theme.text_center(screen, self.font_title, "Verbesserungen", (cx, 60),
                          color=theme.GOLD)
        # Münzen-Pill oben links (konsistent zum Hauptmenü)
        coin_txt = str(save['total_coins'])
        cw = self.font.size(coin_txt)[0]
        pr = pygame.Rect(14, 14, 34 + cw + 18, 34)
        theme.pill(screen, pr, accent=balance.GROUP_COLORS[balance.GROUP_GOLD])
        ui_loader.draw_coin_icon(screen, pr.x + 20, pr.centery, 22)
        theme.text(screen, self.font, coin_txt,
                   (pr.x + 36, pr.centery - self.font.get_height() // 2), color=theme.GOLD)

        # Spalten-Überschriften je Farbgruppe als Chip (Schaden/Verteidigung/Geld/XP)
        for ci, g in enumerate(_GROUP_ORDER):
            x     = self._grid_x + ci * (SHOP_COL_W + SHOP_COL_GAP)
            color = balance.GROUP_COLORS[g]
            chip  = pygame.Rect(x + 20, SHOP_GRID_TOP - 36, SHOP_COL_W - 40, 28)
            theme.pill(screen, chip, accent=color)
            theme.text_center(screen, self.font, balance.GROUP_TITLES[g],
                              chip.center, color=color)

        for rect, kind, e in self._iter_shop_slots():
            color       = balance.GROUP_COLORS[e["group"]]
            state, cost = self._entry_state(kind, e, save)
            lvl         = upgrades.get(e["id"], 0)
            if kind == "infinite":
                name_txt, desc_txt = f"{e['name']}  Lv.{lvl}", e["per_level"]
            elif kind == "tiered":
                name_txt = f"{e['name']}  Lv.{lvl}/{len(e['costs'])}"
                desc_txt = e["tiers"][min(lvl, len(e["tiers"]) - 1)]
            else:
                name_txt, desc_txt = e["name"], e["desc"]
            cost_txt = "" if cost is None else f"{cost} Münzen"
            self._draw_slot(screen, mouse_pos, rect, color, name_txt, desc_txt, cost_txt, state)

        self.back_btn.draw(screen, self.font, mouse_pos)

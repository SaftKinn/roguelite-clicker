import pygame
from . import save_data as sd
from . import ui_loader
from . import balance
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

# Gestufte Käufe (capped, eigene Kostenliste je Stufe) — Reihe 1, Spalte 0
_TIERED = [
    {"id": "doppelschuss", "name": "Doppelschuss",
     "tiers": ["+1 Schuss (2 gesamt)", "+2 Schuss (3 gesamt)"],
     "costs": [balance.COST_DOPPELSCHUSS, balance.COST_DREIFACHSCHUSS],
     "color": (220, 180, 40)},
]

# Einmalige Käufe (Preise/Effekte zentral in balance.py) — Reihe 1, restliche Spalten
_ONE_TIME = [
    {"id": "gold_boost",   "name": "Goldene Kugeln", "desc": f"+{int((balance.GOLD_BOOST_MULT - 1) * 100)}% Münzen aus Kills", "cost": balance.COST_GOLD_BOOST, "color": (255, 210,   0)},
]

# Unendlich steigerbare Upgrades (Preise/Effekte zentral in balance.py)
_INFINITE = [
    {"id": "start_damage", "name": "Startschaden", "per_level": f"+{balance.PERMANENT_DAMAGE_PER_LEVEL} Schaden", "base_cost": balance.COST_START_DAMAGE, "color": (200,  60,  60)},
    {"id": "start_hp",     "name": "Start-HP",     "per_level": f"+{balance.PERMANENT_HP_PER_LEVEL} HP",         "base_cost": balance.COST_START_HP,     "color": ( 60, 200, 100)},
]
_COST_MULT = balance.COST_MULT   # Preismultiplikator pro Stufe

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
        if disabled:
            pygame.draw.rect(screen, (25, 25, 35), self.rect, border_radius=8)
            pygame.draw.rect(screen, (45, 45, 55), self.rect, width=1, border_radius=8)
            surf = font.render(self.label, True, (70, 70, 80))
            screen.blit(surf, (self.rect.centerx - surf.get_width()  // 2,
                                self.rect.centery - surf.get_height() // 2))
            return

        hovered    = self.is_hovered(mouse_pos)
        bg         = COLOR_BTN_HOVER if hovered else COLOR_BTN_BG
        border     = self.accent     if hovered else COLOR_BTN_BORDER
        text_color = (255, 255, 255) if hovered else (180, 180, 200)

        pygame.draw.rect(screen, bg,     self.rect, border_radius=8)
        pygame.draw.rect(screen, border, self.rect, width=2 if hovered else 1, border_radius=8)
        surf = font.render(self.label, True, text_color)
        screen.blit(surf, (self.rect.centerx - surf.get_width()  // 2,
                            self.rect.centery - surf.get_height() // 2))


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
            self.font_title = pygame.font.SysFont("Arial", 44, bold=True)
            self.font_sub   = pygame.font.SysFont("Arial", 16)
            self.font_name  = pygame.font.SysFont("Arial", 24, bold=True)
            self.font_info  = pygame.font.SysFont("Arial", 16)
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
        screen.fill(BG_COLOR)
        cx = SCREEN_WIDTH // 2
        title = self.font_title.render("Speicherstand wählen", True, (255, 220, 60))
        screen.blit(title, (cx - title.get_width() // 2, SCREEN_HEIGHT // 5))

        for i, slot in enumerate(sd.SLOTS):
            card    = self._card_rect(i)
            summary = summaries[i]
            hovered = card.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (40, 40, 58) if hovered else (30, 30, 44),
                             card, border_radius=12)
            pygame.draw.rect(screen, (90, 130, 200) if hovered else (60, 60, 85),
                             card, width=2, border_radius=12)
            name = self.font_name.render(f"Speicherstand {slot}", True, (235, 235, 250))
            screen.blit(name, (card.x + 22, card.y + 16))
            if summary is None:
                info = self.font_info.render("Leer — neuer Lauf", True, (120, 160, 120))
                screen.blit(info, (card.x + 22, card.y + 52))
            else:
                info = self.font_info.render(
                    f"Rekord: Welle {summary['best_wave']}   ·   Münzen: {summary['total_coins']}",
                    True, (180, 180, 205))
                screen.blit(info, (card.x + 22, card.y + 52))
                # Löschen-Button
                dr = self._del_rect(card)
                dhov = dr.collidepoint(mouse_pos)
                pygame.draw.rect(screen, (90, 40, 40) if dhov else (60, 30, 30), dr, border_radius=8)
                pygame.draw.rect(screen, (200, 80, 80), dr, width=1, border_radius=8)
                dl = self.font_info.render("Löschen", True, (230, 170, 170))
                screen.blit(dl, (dr.centerx - dl.get_width() // 2,
                                 dr.centery - dl.get_height() // 2))

        hint = self.font_sub.render("Klicke einen Speicherstand, um zu starten.",
                                    True, (110, 110, 135))
        screen.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 60))


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


class MainMenu:
    def __init__(self):
        self._fonts_ready = False
        total_h = len(_MENU_DEFS) * BTN_H + (len(_MENU_DEFS) - 1) * BTN_GAP
        sx = SCREEN_WIDTH  // 2 - BTN_W // 2
        sy = SCREEN_HEIGHT // 2 - total_h // 2 + 30
        self.buttons    = [
            Button(pygame.Rect(sx, sy + i * (BTN_H + BTN_GAP), BTN_W, BTN_H),
                   d["label"], d["color"])
            for i, d in enumerate(_MENU_DEFS)
        ]
        self.button_ids  = [d["id"] for d in _MENU_DEFS]
        self._gear_rect  = pygame.Rect(SCREEN_WIDTH - _GEAR_SIZE - 12, 12,
                                       _GEAR_SIZE, _GEAR_SIZE)
        self._gear_surf  = None

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title = pygame.font.SysFont("Arial", 50, bold=True)
            self.font_sub   = pygame.font.SysFont("Arial", 16)
            self.font_btn   = pygame.font.SysFont("Arial", 20, bold=True)
            raw = ui_loader._img("Icons/Icon_12.png")
            self._gear_surf = pygame.transform.smoothscale(raw, (_GEAR_SIZE, _GEAR_SIZE))
            self._fonts_ready = True

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
        screen.fill(BG_COLOR)

        cx = SCREEN_WIDTH // 2
        title = self.font_title.render("ROGUELITE CLICKER", True, (255, 220, 60))
        sub   = self.font_sub.render("Tower Defense  ·  Wave Survival", True, (100, 100, 130))
        screen.blit(title, (cx - title.get_width() // 2, SCREEN_HEIGHT // 4 - 20))
        screen.blit(sub,   (cx - sub.get_width()   // 2, SCREEN_HEIGHT // 4 + 44))

        if best_wave > 0:
            rec = self.font_sub.render(f"★  Rekord: Welle {best_wave}", True, (180, 150, 40))
            screen.blit(rec, (cx - rec.get_width() // 2, SCREEN_HEIGHT // 4 + 66))

        # Münzen-Anzeige oben links
        coins_surf = self.font_sub.render(f"Münzen: {save['total_coins']}", True, (220, 180, 40))
        screen.blit(coins_surf, (14, 12 + (_GEAR_SIZE - coins_surf.get_height()) // 2))

        for btn, bid in zip(self.buttons, self.button_ids):
            disabled = (bid == "improvements" and run_active)
            btn.draw(screen, self.font_btn, mouse_pos, disabled=disabled)

        # Zahnrad-Button (Einstellungen)
        if self._gear_surf:
            hovered = self._gear_rect.collidepoint(mouse_pos)
            if hovered:
                pygame.draw.rect(screen, (60, 60, 80), self._gear_rect, border_radius=8)
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
            self.font_title  = pygame.font.SysFont("Arial", 36, bold=True)
            self.font        = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_sm     = pygame.font.SysFont("Arial", 14)
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
        screen.fill(BG_COLOR)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        title = self.font_title.render("Optionen", True, (255, 220, 60))
        screen.blit(title, (cx - title.get_width() // 2, SCREEN_HEIGHT // 4))

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
        {"key": "Boss",         "name": "Boss",         "role": "alle 10 Wellen",
         "stats": ["HP ×6 der Basis", "tötet mit 1 Treffer", "Belohnung: 10"]},
        {"key": "SuperBoss",    "name": "Drache",       "role": "Welle 50 & 100",
         "stats": ["HP ×10 der Basis", "tötet mit 1 Treffer", "Belohnung: 50"]},
    ]
    _COLS = 3
    _CARD_W, _CARD_H, _GAP = 384, 150, 16
    _THUMB = 84

    def __init__(self):
        self._fonts_ready = False
        self._thumbs = {}   # key -> Surface | False (Cache, lazy geladen)
        cx = SCREEN_WIDTH // 2
        self.back_btn = Button(
            pygame.Rect(cx - BTN_W // 2, SCREEN_HEIGHT - BTN_H - 24, BTN_W, BTN_H),
            "Zurück", (60, 160, 220))

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
            self.font_name  = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_sm    = pygame.font.SysFont("Arial", 13)
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

    def _card_rect(self, i: int) -> pygame.Rect:
        col, row = i % self._COLS, i // self._COLS
        grid_w = self._COLS * self._CARD_W + (self._COLS - 1) * self._GAP
        sx = SCREEN_WIDTH // 2 - grid_w // 2
        sy = 104
        return pygame.Rect(sx + col * (self._CARD_W + self._GAP),
                           sy + row * (self._CARD_H + self._GAP),
                           self._CARD_W, self._CARD_H)

    def draw(self, screen: pygame.Surface, mouse_pos: tuple, seen: set) -> None:
        self._load_fonts()
        screen.fill(BG_COLOR)
        cx = SCREEN_WIDTH // 2
        title = self.font_title.render("Lexikon", True, (255, 220, 60))
        screen.blit(title, (cx - title.get_width() // 2, 38))
        n_seen = sum(1 for e in self._CATALOG if e["key"] in seen)
        prog = self.font_sm.render(f"{n_seen} / {len(self._CATALOG)} entdeckt",
                                   True, (140, 140, 165))
        screen.blit(prog, (cx - prog.get_width() // 2, 84))

        for i, entry in enumerate(self._CATALOG):
            r = self._card_rect(i)
            is_seen = entry["key"] in seen
            pygame.draw.rect(screen, (30, 30, 44), r, border_radius=10)
            pygame.draw.rect(screen, (70, 70, 95) if is_seen else (45, 45, 60),
                             r, width=2, border_radius=10)
            # Thumbnail-/Silhouetten-Feld links
            tb = pygame.Rect(r.x + 10, r.y + 10, self._THUMB + 12, r.height - 20)
            pygame.draw.rect(screen, (18, 18, 28), tb, border_radius=8)
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

        self.back_btn.draw(screen, self.font_name, mouse_pos)


# ---------------------------------------------------------------------------
# Verbesserungen-Menü
# ---------------------------------------------------------------------------

SLOT_W, SLOT_H = 290, 140
SLOT_GAP       = 20


class ImprovementsMenu:
    def __init__(self):
        self._fonts_ready = False
        cx        = SCREEN_WIDTH // 2
        total_w   = 2 * SLOT_W + SLOT_GAP
        self._sx  = cx - total_w // 2
        self._sy  = 148
        self.back_btn = Button(
            pygame.Rect(cx - BTN_W // 2, SCREEN_HEIGHT - 82, BTN_W, BTN_H),
            "Zurück", (60, 160, 220)
        )

    def _slot_rect(self, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            self._sx + col * (SLOT_W + SLOT_GAP),
            self._sy + row * (SLOT_H + SLOT_GAP),
            SLOT_W, SLOT_H
        )

    def _load_fonts(self) -> None:
        if not self._fonts_ready:
            self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
            self.font       = pygame.font.SysFont("Arial", 17, bold=True)
            self.font_sm    = pygame.font.SysFont("Arial", 13)
            self._fonts_ready = True

    # ------------------------------------------------------------------

    def handle_click(self, pos: tuple, save: dict) -> str | None:
        if self.back_btn.is_hovered(pos):
            return "back"

        upgrades = save.setdefault("upgrades", {"start_damage": 0, "start_hp": 0})

        for i, inf in enumerate(_INFINITE):
            if not self._slot_rect(0, i).collidepoint(pos):
                continue
            lvl  = upgrades.get(inf["id"], 0)
            cost = upgrade_cost(inf["base_cost"], lvl)
            if save["total_coins"] >= cost:
                save["total_coins"]  -= cost
                upgrades[inf["id"]]   = lvl + 1
                sd.save(save)

        # Reihe 1: gestufte Käufe (links) + einmalige Käufe (rechts)
        for i, entry in enumerate(_TIERED + _ONE_TIME):
            if not self._slot_rect(1, i).collidepoint(pos):
                continue
            if "costs" in entry:                       # gestuft (capped)
                lvl = upgrades.get(entry["id"], 0)
                if lvl < len(entry["costs"]) and save["total_coins"] >= entry["costs"][lvl]:
                    save["total_coins"]   -= entry["costs"][lvl]
                    upgrades[entry["id"]]  = lvl + 1
                    sd.save(save)
            else:                                      # einmalig
                if entry["id"] not in save["bought"] and save["total_coins"] >= entry["cost"]:
                    save["total_coins"] -= entry["cost"]
                    save["bought"].append(entry["id"])
                    sd.save(save)

        return None

    # ------------------------------------------------------------------

    def _draw_slot(self, screen, mouse_pos, rect: pygame.Rect,
                   color, name_txt, desc_txt, cost_txt,
                   state: str, special: bool = False) -> None:
        # state: "buyable" | "bought" | "locked"
        hovered = rect.collidepoint(mouse_pos) and state != "bought"

        bg = (38, 38, 55) if hovered and state == "buyable" else (28, 28, 42)
        pygame.draw.rect(screen, bg, rect, border_radius=8)

        border_col = (color if state in ("bought", "buyable") and (state == "bought" or hovered)
                      else (55, 55, 75))
        border_w   = 2 if (state == "bought" or (hovered and state == "buyable")) else 1
        pygame.draw.rect(screen, border_col, rect, width=border_w, border_radius=8)

        # Accent stripe left
        pygame.draw.rect(screen, color,
                         pygame.Rect(rect.x, rect.y + 8, 4, rect.height - 16),
                         border_radius=2)

        rx, ry = rect.x, rect.y
        name_c = color if state == "bought" else (255, 255, 255)
        screen.blit(self.font.render(name_txt, True, name_c),              (rx + 14, ry + 12))
        screen.blit(self.font_sm.render(desc_txt, True, (140, 140, 160)),  (rx + 14, ry + 40))

        if state == "bought":
            ok = self.font.render("✓ Gekauft", True, color)
            screen.blit(ok, (rx + 14, ry + rect.height - ok.get_height() - 12))
        elif state == "locked":
            screen.blit(self.font_sm.render(cost_txt, True, (180, 150, 50)), (rx + 14, ry + 62))
            no = self.font_sm.render("Nicht genug Münzen", True, (180, 60, 60))
            screen.blit(no, (rx + 14, ry + rect.height - no.get_height() - 12))
        else:  # buyable
            screen.blit(self.font_sm.render(cost_txt, True, (180, 150, 50)), (rx + 14, ry + 62))
            if hovered:
                hint = self.font_sm.render("← Klicken zum Kaufen", True, color)
                screen.blit(hint, (rx + 14, ry + rect.height - hint.get_height() - 12))

    def draw(self, screen: pygame.Surface, mouse_pos: tuple, save: dict) -> None:
        self._load_fonts()
        screen.fill(BG_COLOR)
        cx       = SCREEN_WIDTH // 2
        upgrades = save.get("upgrades", {})

        title = self.font_title.render("Verbesserungen", True, (255, 220, 60))
        screen.blit(title, (cx - title.get_width() // 2, 50))

        coins_surf = self.font.render(f"Münzen:  {save['total_coins']}", True, (220, 180, 40))
        screen.blit(coins_surf, (cx - coins_surf.get_width() // 2, 98))

        # --- Unendliche Upgrades (oben) ---
        for i, inf in enumerate(_INFINITE):
            rect = self._slot_rect(0, i)
            lvl  = upgrades.get(inf["id"], 0)
            cost = upgrade_cost(inf["base_cost"], lvl)
            state = "buyable" if save["total_coins"] >= cost else "locked"
            self._draw_slot(screen, mouse_pos, rect,
                            color    = inf["color"],
                            name_txt = f"{inf['name']}   Lv.{lvl}",
                            desc_txt = inf["per_level"],
                            cost_txt = f"Kosten: {cost} Münzen",
                            state    = state)
            inf_lbl = self.font_sm.render("∞", True, inf["color"])
            screen.blit(inf_lbl, (rect.right - inf_lbl.get_width() - 10, rect.y + 10))

        # --- Reihe 1: gestufte (links) + einmalige Käufe (rechts) ---
        for i, entry in enumerate(_TIERED + _ONE_TIME):
            rect = self._slot_rect(1, i)
            if "costs" in entry:                       # gestuft
                lvl   = upgrades.get(entry["id"], 0)
                maxed = lvl >= len(entry["costs"])
                if maxed:
                    state, cost_txt = "bought", "Maximal ausgebaut"
                else:
                    cost  = entry["costs"][lvl]
                    state = "buyable" if save["total_coins"] >= cost else "locked"
                    cost_txt = f"Kosten: {cost} Münzen"
                self._draw_slot(screen, mouse_pos, rect,
                                color    = entry["color"],
                                name_txt = f"{entry['name']}  Lv.{lvl}/{len(entry['costs'])}",
                                desc_txt = entry["tiers"][min(lvl, len(entry["tiers"]) - 1)],
                                cost_txt = cost_txt,
                                state    = state,
                                special  = True)
            else:                                      # einmalig
                bought = entry["id"] in save["bought"]
                state  = ("bought"  if bought
                          else "buyable" if save["total_coins"] >= entry["cost"]
                          else "locked")
                self._draw_slot(screen, mouse_pos, rect,
                                color    = entry["color"],
                                name_txt = entry["name"],
                                desc_txt = entry["desc"],
                                cost_txt = f"Kosten: {entry['cost']} Münzen",
                                state    = state,
                                special  = True)

        self.back_btn.draw(screen, self.font, mouse_pos)

import os
import random
import pygame
from . import ui_loader
from . import balance
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT

COLOR_BODY  = ( 80, 160, 255)
COLOR_INNER = (200, 230, 255)

RADIUS   = 18
MAX_HP   = 120   # Basis-HP des Turms (knackiger/tödlicher, ADR 008; HP kommt nun v. a. über Level-up-Karten)

_TURM_PATH  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "custom", "player_tower.png")
_TOWER_SIZE = round(135 * balance.SPRITE_SCALE)   # Turm-Sprite global mitskaliert (SPRITE_SCALE)

_SENTINEL   = object()
_tower_surf = None
_bar_font   = None


def _get_tower() -> pygame.Surface | None:
    global _tower_surf
    if _tower_surf is None:
        try:
            raw         = pygame.image.load(_TURM_PATH).convert_alpha()
            _tower_surf = pygame.transform.smoothscale(raw, (_TOWER_SIZE, _TOWER_SIZE))
        except Exception as exc:
            print(f"[Player] Turm-Sprite: {exc}")
            _tower_surf = _SENTINEL
    return None if _tower_surf is _SENTINEL else _tower_surf


def _get_bar_font() -> pygame.font.Font:
    global _bar_font
    if _bar_font is None:
        _bar_font = pygame.font.SysFont("Arial", 12, bold=True)
    return _bar_font


class Player:
    def __init__(self):
        self.x      = SCREEN_WIDTH  // 2
        self.y      = SCREEN_HEIGHT // 2
        self.max_hp = MAX_HP
        self.hp     = MAX_HP
        # Verteidigungs-/Lifesteal-Werte aus den Karten (ADR 025); von `_sync_player_defense`
        # aus gs["stats"] gespiegelt, damit die Treffer-Funktionen sie ohne stats-Durchreichung kennen.
        self.armor          = 0.0   # Anteil Schadensreduktion (0..ARMOR_CAP)
        self.dodge          = 0.0   # Chance, einen Treffer komplett zu vermeiden (0..DODGE_CAP)
        self.thorns_pct     = 0.0   # Anteil reflektierten Nahkampf-Schadens
        self.hp_regen       = 0.0   # HP/Sekunde (Regeneration)
        self.lifesteal_flat = 0     # flache HP/Treffer zusätzlich zur Basis
        self.lifesteal_pct  = 0.0   # Anteil des Treffer-Schadens als HP

    def take_damage(self, amount: int) -> None:
        # Ausweichen: mit `dodge`-Chance kompletten Treffer vermeiden (greift NICHT gegen
        # den Boss-Oneshot, der in main.py player.hp direkt auf 0 setzt — ADR 025).
        if self.dodge and random.random() < self.dodge:
            return
        amount *= (1.0 - self.armor)   # Rüstung reduziert den eingehenden Schaden
        self.hp = max(0, self.hp - amount)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def update(self) -> None:
        pass

    def _draw_hp_bar(self, screen: pygame.Surface) -> None:
        bar_w = _TOWER_SIZE + 20
        bar_h = 22
        bar_x = int(self.x) - bar_w // 2
        bar_y = int(self.y) - _TOWER_SIZE // 2 - bar_h - 4
        ratio = max(0.0, self.hp / self.max_hp)

        ui_loader.draw_bar(screen, pygame.Rect(bar_x, bar_y, bar_w, bar_h),
                           ratio, big=True)
        label = _get_bar_font().render(str(self.hp), True, (255, 255, 255))
        screen.blit(label, (bar_x + bar_w // 2 - label.get_width()  // 2,
                             bar_y + bar_h // 2 - label.get_height() // 2))

    def draw(self, screen: pygame.Surface, mouse_pos: tuple = None) -> None:
        pos   = (int(self.x), int(self.y))
        tower = _get_tower()

        if tower:
            screen.blit(tower, (pos[0] - tower.get_width()  // 2,
                                pos[1] - tower.get_height() // 2))
        else:
            pygame.draw.circle(screen, COLOR_BODY,  pos, RADIUS)
            pygame.draw.circle(screen, COLOR_INNER, pos, RADIUS - 6)

        self._draw_hp_bar(screen)

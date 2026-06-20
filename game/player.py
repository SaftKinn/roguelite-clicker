import os
import pygame
from . import ui_loader
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT

COLOR_BODY  = ( 80, 160, 255)
COLOR_INNER = (200, 230, 255)

RADIUS   = 18
MAX_HP   = 100

_TURM_PATH  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "Tiny Swords (Free Pack)", "Turm.png")
_TOWER_SIZE = 110

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

    def take_damage(self, amount: int) -> None:
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

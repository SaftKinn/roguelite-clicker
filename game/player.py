import math
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

# Turm-Animation (Juice, ADR 035): rein über Transform/Tint des vorhandenen Sprites.
_IDLE_PULSE_PERIOD = 90       # Ticks für einen Atem-Zyklus
_IDLE_PULSE_SCALE  = 0.03     # ±3 % Scale-Wabern (Idle-„Atmen")
_RECOIL_TICKS      = 7        # Dauer des Rückstoß-Pops nach einem Schuss
_RECOIL_SCALE      = 0.10     # Scale-Dip beim Schuss (federt zurück)
_RECOIL_OFFSET_PX  = 6        # Versatz entgegen der Schussrichtung (in Sprite-Pixeln)
_OVERDRIVE_TINT    = (70, 45, 0)   # additiver Glüh-Ton während Overdrive (pulsierend)

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
        self.invuln         = False # Dev-Schalter (Taste U): nimmt keinen Schaden
        # Turm-Animation (Juice, ADR 035)
        self._anim_t        = 0                              # globaler Tick-Zähler (Idle-Puls)
        self._recoil        = 0                              # Rest-Ticks des Rückstoß-Pops
        self._recoil_dir    = pygame.math.Vector2(0, -1)     # Schussrichtung (für Versatz)
        self._overdrive_on  = False                          # von main je Frame gespiegelt

    def take_damage(self, amount: int) -> None:
        if self.invuln:            # Dev-Unverwundbarkeit (Taste U): kompletten Treffer ignorieren
            return
        # Ausweichen: mit `dodge`-Chance kompletten Treffer vermeiden (greift NICHT gegen
        # den Boss-Oneshot, der in main.py player.hp direkt auf 0 setzt — ADR 025).
        if self.dodge and random.random() < self.dodge:
            return
        amount *= (1.0 - self.armor)   # Rüstung reduziert den eingehenden Schaden
        self.hp = max(0, self.hp - amount)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def update(self, overdrive: bool = False) -> None:
        self._anim_t      += 1
        self._overdrive_on = overdrive
        if self._recoil > 0:
            self._recoil -= 1

    def trigger_recoil(self, direction: pygame.math.Vector2 | None = None) -> None:
        """Vom Game-Loop bei jedem Turm-Schuss gerufen: startet den Rückstoß-Pop
        und merkt sich die Schussrichtung für den Versatz."""
        self._recoil = _RECOIL_TICKS
        if direction is not None and direction.length() > 0:
            self._recoil_dir = direction.normalize()

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
            # Idle-Puls (sanftes Atmen) + Recoil-Dip als kombinierter Scale; der Recoil
            # versetzt das Sprite zusätzlich kurz entgegen der Schussrichtung.
            pulse = math.sin(self._anim_t * (2 * math.pi / _IDLE_PULSE_PERIOD)) * _IDLE_PULSE_SCALE
            rec   = self._recoil / _RECOIL_TICKS if self._recoil > 0 else 0.0
            scale = (1.0 + pulse) * (1.0 - _RECOIL_SCALE * rec)
            ox    = int(-self._recoil_dir.x * _RECOIL_OFFSET_PX * rec)
            oy    = int(-self._recoil_dir.y * _RECOIL_OFFSET_PX * rec)

            img = tower
            if abs(scale - 1.0) > 0.001:
                w = max(1, int(tower.get_width()  * scale))
                h = max(1, int(tower.get_height() * scale))
                img = pygame.transform.smoothscale(tower, (w, h))
            if self._overdrive_on:
                if img is tower:        # gecachte Surface nie in-place tönen → Kopie
                    img = img.copy()
                glow = 0.55 + 0.45 * abs(math.sin(self._anim_t * 0.15))   # pulsierend
                img.fill(tuple(int(c * glow) for c in _OVERDRIVE_TINT),
                         special_flags=pygame.BLEND_RGB_ADD)

            screen.blit(img, (pos[0] - img.get_width()  // 2 + ox,
                              pos[1] - img.get_height() // 2 + oy))
        else:
            pygame.draw.circle(screen, COLOR_BODY,  pos, RADIUS)
            pygame.draw.circle(screen, COLOR_INNER, pos, RADIUS - 6)

        self._draw_hp_bar(screen)

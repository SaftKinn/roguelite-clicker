import math
import random
import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT
from . import balance

# ---------------------------------------------------------------------------
# Feind-Projektil (Archer-Pfeil)
# ---------------------------------------------------------------------------

class EnemyProjectile:
    SPEED        = 3.5
    RADIUS       = 4
    DAMAGE       = 16   # Archer-Pfeilschaden (tödlicher, ADR 008)
    _COLOR_OUTER = (180, 130,  40)
    _COLOR_INNER = (255, 210, 100)
    _arrow_surf  = None

    @classmethod
    def _get_arrow(cls):
        if cls._arrow_surf is None:
            try:
                from . import sprite_loader
                cls._arrow_surf = sprite_loader.load_arrow(20)
            except Exception:
                cls._arrow_surf = False
        return cls._arrow_surf if cls._arrow_surf else None

    def __init__(self, pos: pygame.math.Vector2, target: pygame.math.Vector2):
        self.pos   = pygame.math.Vector2(pos)
        self.alive = True
        direction  = target - self.pos
        self.vel   = (direction.normalize() * self.SPEED
                      if direction.length() > 0 else pygame.math.Vector2(0, 0))

    def update(self) -> None:
        self.pos += self.vel
        if not (0 <= self.pos.x <= SCREEN_WIDTH and 0 <= self.pos.y <= SCREEN_HEIGHT):
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        arrow = self._get_arrow()
        p = (int(self.pos.x), int(self.pos.y))
        if arrow:
            angle = -math.degrees(math.atan2(self.vel.y, self.vel.x))
            rotated = pygame.transform.rotate(arrow, angle)
            screen.blit(rotated, (p[0] - rotated.get_width() // 2,
                                   p[1] - rotated.get_height() // 2))
        else:
            pygame.draw.circle(screen, self._COLOR_OUTER, p, self.RADIUS)
            pygame.draw.circle(screen, self._COLOR_INNER, p, self.RADIUS - 2)


# ---------------------------------------------------------------------------

RADIUS = 14   # Modul-Konstante für Rückwärtskompatibilität

_ANIM_PERIOD = 6   # Ticks zwischen Animations-Frames (~10 FPS bei 60 FPS)
_PLAYER_RADIUS = 18   # spiegelt player.RADIUS — Nahkämpfer stoppen davor statt hineinzulaufen


class Warrior:
    RADIUS        = 14
    COLOR_BODY    = (220,  50,  50)
    COLOR_OUTLINE = (140,  20,  20)
    COLOR_HP_BAR  = (255,  80,  80)

    elite = False   # Default; Elite-Instanzen setzen self.elite=True (10× HP, Ring-Markierung)

    _frames_r = None
    _frames_l = None
    _atk1_frames_r    = None
    _atk1_frames_l    = None
    _atk2_frames_r    = None
    _atk2_frames_l    = None
    ATTACK_ANIM_RANGE = 60
    ATTACK_DAMAGE     = balance.ATTACK_DAMAGE     # Nahkampf-Schaden pro Treffer (zentral in balance.py)
    ATTACK_COOLDOWN   = balance.ATTACK_COOLDOWN   # Ticks zwischen Treffern (~0.75 s)

    def __init__(self, speed: float = 1.8, max_hp: int = 30):
        self.pos         = pygame.math.Vector2(self._random_edge_pos())
        self.speed       = speed
        self.max_hp      = max_hp
        self.hp          = max_hp
        self.alive       = True
        self.radius      = self.__class__.RADIUS
        self.coin_value  = 1
        self.facing_left = False
        self._anim_tick  = 0
        self._anim_frame = 0
        self._is_attacking = False
        self._atk_fr       = 0
        self._atk_tk       = 0
        self._atk_alt      = False
        self._attack_cd    = 0   # Cooldown bis zum nächsten Nahkampf-Treffer

    @staticmethod
    def _random_edge_pos() -> tuple:
        side = random.choice(("top", "bottom", "left", "right"))
        if side == "top":    return random.randint(0, SCREEN_WIDTH), 0
        if side == "bottom": return random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT
        if side == "left":   return 0, random.randint(0, SCREEN_HEIGHT)
        return SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT)

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l         = sprite_loader.load_black_warrior_run(48)
            cls._atk1_frames_r, cls._atk1_frames_l = sprite_loader.load_black_warrior_attack(1, 48)
            cls._atk2_frames_r, cls._atk2_frames_l = sprite_loader.load_black_warrior_attack(2, 48)
        except Exception as exc:
            print(f"[{cls.__name__}] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
            cls._atk1_frames_r = cls._atk1_frames_l = []
            cls._atk2_frames_r = cls._atk2_frames_l = []

    def update(self, target: pygame.math.Vector2) -> None:
        if self._attack_cd > 0:
            self._attack_cd -= 1
        direction = target - self.pos
        dist      = direction.length()
        stop_dist = _PLAYER_RADIUS + self.radius   # genau vor dem Spieler anhalten
        if dist > stop_dist:
            step = min(self.speed, dist - stop_dist)   # nicht in den Spieler rutschen
            vel  = direction.normalize() * step
            if abs(vel.x) > 0.05:
                self.facing_left = vel.x < 0
            self.pos += vel
        elif dist > 0:
            self.facing_left = direction.x < 0   # in Reichweite: weiter zum Spieler ausrichten
        if dist > 0 and not self._is_attacking and self._atk1_frames_r:
            if dist < self.ATTACK_ANIM_RANGE:
                self._is_attacking = True
                self._atk_fr       = 0
                self._atk_tk       = 0
                self._atk_alt      = not self._atk_alt
        if self._is_attacking:
            self._atk_tk += 1
            if self._atk_tk >= _ANIM_PERIOD:
                self._atk_tk = 0
                self._atk_fr += 1
                atk_len = len(self._atk1_frames_r) if self._atk1_frames_r else 0
                if self._atk_fr >= atk_len:
                    self._is_attacking = False
        self._anim_tick += 1
        if self._anim_tick >= _ANIM_PERIOD:
            self._anim_tick = 0
            if self._frames_r:
                self._anim_frame = (self._anim_frame + 1) % len(self._frames_r)

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def melee_attack(self) -> int:
        """Schaden, wenn der Cooldown bereit ist, sonst 0.

        Der Gegner stirbt durch Kontakt NICHT — nur Projektile töten ihn.
        """
        if self._attack_cd <= 0:
            self._attack_cd = self.ATTACK_COOLDOWN
            return self.ATTACK_DAMAGE
        return 0

    def _draw_hp_bar(self, screen: pygame.Surface, pos: tuple) -> None:
        bar_w = max(28, self.radius * 2)
        bar_h = 3
        bar_x = pos[0] - bar_w // 2
        bar_y = pos[1] - self.radius - bar_h - 3
        ratio = max(0.0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (20, 20, 20), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(screen, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, self.COLOR_HP_BAR,
                         (bar_x, bar_y, int(bar_w * ratio), bar_h))

    def _blit_sprite(self, screen: pygame.Surface) -> bool:
        self._load_sprites()
        frames = self._frames_l if self.facing_left else self._frames_r
        if not frames:
            return False
        frame = frames[self._anim_frame % len(frames)]
        screen.blit(frame, (int(self.pos.x) - frame.get_width()  // 2,
                             int(self.pos.y) - frame.get_height() // 2))
        return True

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        pos = (int(self.pos.x), int(self.pos.y))
        if self._is_attacking and self._atk1_frames_r:
            frames_r = self._atk2_frames_r if self._atk_alt else self._atk1_frames_r
            frames_l = self._atk2_frames_l if self._atk_alt else self._atk1_frames_l
            frames   = frames_l if self.facing_left else frames_r
            fr       = min(self._atk_fr, len(frames) - 1)
            screen.blit(frames[fr], (pos[0] - frames[fr].get_width() // 2,
                                      pos[1] - frames[fr].get_height() // 2))
        elif not self._blit_sprite(screen):
            pygame.draw.circle(screen, self.COLOR_OUTLINE, pos, self.radius + 2)
            pygame.draw.circle(screen, self.COLOR_BODY,    pos, self.radius)
        self._draw_hp_bar(screen, pos)


# ---------------------------------------------------------------------------

class Archer(Warrior):
    """Archer-Fernkämpfer — bleibt auf Distanz, schießt Pfeile."""
    RADIUS        = 9
    ATTACK_RANGE  = 220
    SHOOT_EVERY   = 90
    # Frame in der 8-teiligen Shoot-Animation, bei dem der Bogen voll gespannt
    # ist (höchster Punkt) — erst dann verlässt der Pfeil den Bogen.
    SHOOT_RELEASE_FRAME = 5
    COLOR_BODY    = (255, 130,  30)
    COLOR_OUTLINE = (200,  70,   0)
    COLOR_HP_BAR  = (255, 200,  80)

    _frames_r       = None
    _frames_l       = None
    _shoot_frames_r = None
    _shoot_frames_l = None

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=base_speed * 1.3, max_hp=max(1, int(base_hp * 0.4)))
        self.coin_value       = 1
        self._shoot_timer     = random.randint(20, self.SHOOT_EVERY)
        self._shots: list[EnemyProjectile] = []
        self._is_shooting     = False
        self._shoot_anim_fr   = 0
        self._shoot_anim_tk   = 0
        self._pending_release = False   # Pfeil noch nicht abgeschossen (wartet auf Release-Frame)

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_black_archer_run(50)
            cls._shoot_frames_r, cls._shoot_frames_l = sprite_loader.load_black_archer_shoot(50)
        except Exception as exc:
            print(f"[Archer] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
            cls._shoot_frames_r = cls._shoot_frames_l = []

    def update(self, target: pygame.math.Vector2) -> None:
        direction = target - self.pos
        dist      = direction.length()
        if dist > self.ATTACK_RANGE:
            vel = direction.normalize() * self.speed
            if abs(vel.x) > 0.05:
                self.facing_left = vel.x < 0
            self.pos += vel
        else:
            self._shoot_timer -= 1
            if self._shoot_timer <= 0:
                self._shoot_timer = self.SHOOT_EVERY
                shoot_len = len(self._shoot_frames_r) if self._shoot_frames_r else 0
                if shoot_len > 0:
                    # Animation starten — Pfeil folgt erst am Release-Frame.
                    self._is_shooting     = True
                    self._pending_release = True
                    self._shoot_anim_fr   = 0
                    self._shoot_anim_tk   = 0
                else:
                    # Kein Sprite geladen → sofort feuern (Fallback).
                    self._shots.append(EnemyProjectile(self.pos, target))
        if self._is_shooting:
            self._shoot_anim_tk += 1
            if self._shoot_anim_tk >= _ANIM_PERIOD:
                self._shoot_anim_tk = 0
                self._shoot_anim_fr += 1
                # Beim Erreichen des Release-Frames (Bogen am höchsten Punkt)
                # den Pfeil auf die aktuelle Zielposition abschießen.
                if self._pending_release and self._shoot_anim_fr >= self.SHOOT_RELEASE_FRAME:
                    self._shots.append(EnemyProjectile(self.pos, target))
                    self._pending_release = False
                shoot_len = len(self._shoot_frames_r) if self._shoot_frames_r else 0
                if self._shoot_anim_fr >= shoot_len:
                    # Animation vorbei: Sicherung, falls Release-Frame > Länge.
                    if self._pending_release:
                        self._shots.append(EnemyProjectile(self.pos, target))
                        self._pending_release = False
                    self._is_shooting = False
        self._anim_tick += 1
        if self._anim_tick >= _ANIM_PERIOD:
            self._anim_tick = 0
            if self._frames_r:
                self._anim_frame = (self._anim_frame + 1) % len(self._frames_r)

    def pop_shots(self) -> list[EnemyProjectile]:
        shots = list(self._shots)
        self._shots.clear()
        return shots

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        pos = (int(self.pos.x), int(self.pos.y))
        if self._is_shooting and self._shoot_frames_r:
            frames = self._shoot_frames_l if self.facing_left else self._shoot_frames_r
            fr = min(self._shoot_anim_fr, len(frames) - 1)
            screen.blit(frames[fr], (pos[0] - frames[fr].get_width() // 2,
                                      pos[1] - frames[fr].get_height() // 2))
        elif not self._blit_sprite(screen):
            pygame.draw.circle(screen, self.COLOR_OUTLINE, pos, self.radius + 1)
            pygame.draw.circle(screen, self.COLOR_BODY,    pos, self.radius)
        self._draw_hp_bar(screen, pos)


# ---------------------------------------------------------------------------

class Lancer(Warrior):
    """Langsamer Nahkämpfer mit viel HP."""
    RADIUS        = 22
    COLOR_BODY    = ( 80,  40, 130)
    COLOR_OUTLINE = (140,  80, 200)
    COLOR_HP_BAR  = (160,  80, 220)

    _frames_r         = None
    _frames_l         = None
    _lancer_atk       = None
    _atk1_frames_r    = None
    _atk1_frames_l    = None
    _atk2_frames_r    = None
    _atk2_frames_l    = None
    ATTACK_ANIM_RANGE = 100

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=max(0.5, base_speed * 0.45), max_hp=int(base_hp * 3.0))
        self.coin_value = 3
        self._lancer_is_attacking = False
        self._lancer_atk_fr       = 0
        self._lancer_atk_tk       = 0
        self._lancer_atk_dir      = 0

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_black_lancer_run(90)
            cls._lancer_atk               = sprite_loader.load_black_lancer_attacks(90)
        except Exception as exc:
            print(f"[Lancer] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
            cls._lancer_atk = []

    def update(self, target: pygame.math.Vector2) -> None:
        super().update(target)
        if not self._lancer_atk:
            return
        direction = target - self.pos
        dist = direction.length()
        if not self._lancer_is_attacking and dist < self.ATTACK_ANIM_RANGE:
            self._lancer_is_attacking = True
            self._lancer_atk_fr       = 0
            self._lancer_atk_tk       = 0
            dx = direction.x if not self.facing_left else -direction.x
            dy = direction.y
            angle = math.degrees(math.atan2(dy, dx))
            if   -22.5 <= angle <= 22.5:    self._lancer_atk_dir = 0
            elif  22.5 <  angle <= 67.5:   self._lancer_atk_dir = 3
            elif  angle  > 67.5:           self._lancer_atk_dir = 4
            elif -67.5 <= angle < -22.5:   self._lancer_atk_dir = 1
            else:                           self._lancer_atk_dir = 2
        if self._lancer_is_attacking:
            self._lancer_atk_tk += 1
            if self._lancer_atk_tk >= _ANIM_PERIOD:
                self._lancer_atk_tk = 0
                self._lancer_atk_fr += 1
                atk_len = len(self._lancer_atk[0][0]) if self._lancer_atk else 0
                if self._lancer_atk_fr >= atk_len:
                    self._lancer_is_attacking = False

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        pos = (int(self.pos.x), int(self.pos.y))
        if self._lancer_is_attacking and self._lancer_atk:
            frames_r, frames_l = self._lancer_atk[self._lancer_atk_dir]
            frames = frames_l if self.facing_left else frames_r
            fr     = min(self._lancer_atk_fr, len(frames) - 1)
            screen.blit(frames[fr], (pos[0] - frames[fr].get_width() // 2,
                                      pos[1] - frames[fr].get_height() // 2))
        elif not self._blit_sprite(screen):
            pygame.draw.circle(screen, self.COLOR_OUTLINE, pos, self.radius + 5, width=4)
            pygame.draw.circle(screen, self.COLOR_BODY,    pos, self.radius)
        self._draw_hp_bar(screen, pos)


# ---------------------------------------------------------------------------

class Monk(Warrior):
    """Heiler — bleibt auf Distanz, heilt benachbarte Gegner."""
    RADIUS       = 10
    ATTACK_RANGE = 220
    HEAL_EVERY   = 150     # Ticks zwischen Heilungen (~2.5 s)
    HEAL_AMOUNT  = 15
    HEAL_COUNT   = 5      # heilt die N nächsten Gegner
    COLOR_BODY   = ( 80, 200, 120)
    COLOR_OUTLINE= ( 40, 130,  70)
    COLOR_HP_BAR = (100, 255, 140)

    _frames_r       = None
    _frames_l       = None
    _heal_frames_r  = None
    _heal_frames_l  = None
    _heal_fx_frames = None
    _aura_surf      = None   # gecachte Heilaura-Surface
    _HEAL_FX_SIZE   = 64
    _HEAL_FX_PERIOD = 4

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=base_speed * 0.9, max_hp=int(base_hp * 0.6))
        self.coin_value        = 3
        self._heal_timer       = random.randint(40, self.HEAL_EVERY)
        self._aura_timer       = 0
        self._heal_anim_active = False
        self._heal_anim_fr     = 0
        self._heal_anim_tk     = 0
        self._heal_effects     = []

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l          = sprite_loader.load_monk(44)
            cls._heal_frames_r, cls._heal_frames_l = sprite_loader.load_monk_heal(44)
            cls._heal_fx_frames                    = sprite_loader.load_heal_effect(cls._HEAL_FX_SIZE)
        except Exception as exc:
            print(f"[Monk] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
            cls._heal_frames_r = cls._heal_frames_l = []
            cls._heal_fx_frames = []

    _AURA_R = 60   # rein visuelle Aura-Größe

    @classmethod
    def _get_aura(cls) -> pygame.Surface:
        if cls._aura_surf is None:
            size = cls._AURA_R * 2
            cls._aura_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(cls._aura_surf, (80, 255, 120, 70),
                               (cls._AURA_R, cls._AURA_R), cls._AURA_R)
        return cls._aura_surf

    def update(self, target: pygame.math.Vector2) -> None:
        direction = target - self.pos
        dist      = direction.length()
        if dist > self.ATTACK_RANGE:
            vel = direction.normalize() * self.speed
            if abs(vel.x) > 0.05:
                self.facing_left = vel.x < 0
            self.pos += vel
        self._heal_timer -= 1
        if self._aura_timer > 0:
            self._aura_timer -= 1
        self._anim_tick += 1
        if self._anim_tick >= _ANIM_PERIOD:
            self._anim_tick = 0
            if self._frames_r:
                self._anim_frame = (self._anim_frame + 1) % len(self._frames_r)
        if self._heal_anim_active:
            self._heal_anim_tk += 1
            if self._heal_anim_tk >= _ANIM_PERIOD:
                self._heal_anim_tk = 0
                self._heal_anim_fr += 1
                heal_len = len(self._heal_frames_r) if self._heal_frames_r else 0
                if self._heal_anim_fr >= heal_len:
                    self._heal_anim_active = False
        new_fx = []
        for fx in self._heal_effects:
            fx[3] += 1
            if fx[3] >= self._HEAL_FX_PERIOD:
                fx[3] = 0
                fx[2] += 1
            fx_len = len(self._heal_fx_frames) if self._heal_fx_frames else 0
            if fx[2] < fx_len:
                new_fx.append(fx)
        self._heal_effects = new_fx

    def heal_nearby(self, enemies: list) -> None:
        if self._heal_timer > 0:
            return
        self._heal_timer       = self.HEAL_EVERY
        self._aura_timer       = 40
        self._heal_anim_active = True
        self._heal_anim_fr     = 0
        self._heal_anim_tk     = 0
        candidates = sorted(
            (e for e in enemies if e is not self and e.alive),
            key=lambda e: self.pos.distance_to(e.pos)
        )
        for e in candidates[:self.HEAL_COUNT]:
            e.hp = min(e.max_hp, e.hp + self.HEAL_AMOUNT)
            self._heal_effects.append([e.pos.x, e.pos.y, 0, 0])

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        pos = (int(self.pos.x), int(self.pos.y))
        if self._aura_timer > 0:
            aura  = self._get_aura()
            alpha = int(self._aura_timer / 40 * 255)
            aura.set_alpha(alpha)
            screen.blit(aura, (pos[0] - self._AURA_R, pos[1] - self._AURA_R))
        if self._heal_anim_active and self._heal_frames_r:
            frames = self._heal_frames_l if self.facing_left else self._heal_frames_r
            fr = min(self._heal_anim_fr, len(frames) - 1)
            screen.blit(frames[fr], (pos[0] - frames[fr].get_width() // 2,
                                      pos[1] - frames[fr].get_height() // 2))
        elif not self._blit_sprite(screen):
            pygame.draw.circle(screen, self.COLOR_OUTLINE, pos, self.radius + 2)
            pygame.draw.circle(screen, self.COLOR_BODY,    pos, self.radius)
        if self._heal_fx_frames:
            size = self._HEAL_FX_SIZE
            for fx in self._heal_effects:
                fr = fx[2]
                if 0 <= fr < len(self._heal_fx_frames):
                    surf = self._heal_fx_frames[fr]
                    screen.blit(surf, (int(fx[0]) - size // 2, int(fx[1]) - size // 2))
        self._draw_hp_bar(screen, pos)


# ---------------------------------------------------------------------------

class Boss(Warrior):
    """Boss — alle 10 Wellen. Tötet Spieler mit einem Treffer."""
    RADIUS        = 34
    COLOR_BODY    = (160,  65,  10)
    COLOR_OUTLINE = (255, 155,  25)
    COLOR_HP_BAR  = (255, 140,  20)

    _frames_r         = None
    _frames_l         = None
    _lancer_atk       = None
    _atk1_frames_r    = None
    _atk1_frames_l    = None
    _atk2_frames_r    = None
    _atk2_frames_l    = None
    ATTACK_ANIM_RANGE = 120

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=max(0.4, base_speed * 0.35), max_hp=int(base_hp * 8))
        self.coin_value = 10
        self._tick      = 0
        self._lancer_is_attacking = False
        self._lancer_atk_fr       = 0
        self._lancer_atk_tk       = 0
        self._lancer_atk_dir      = 0

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_black_lancer_run(96)
            cls._lancer_atk               = sprite_loader.load_black_lancer_attacks(96)
        except Exception as exc:
            print(f"[Boss] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
            cls._lancer_atk = []

    def _draw_hp_bar(self, screen, pos) -> None:
        pass

    def update(self, target: pygame.math.Vector2) -> None:
        self._tick += 1
        super().update(target)
        if not self._lancer_atk:
            return
        direction = target - self.pos
        dist = direction.length()
        if not self._lancer_is_attacking and dist < self.ATTACK_ANIM_RANGE:
            self._lancer_is_attacking = True
            self._lancer_atk_fr       = 0
            self._lancer_atk_tk       = 0
            dx = direction.x if not self.facing_left else -direction.x
            dy = direction.y
            angle = math.degrees(math.atan2(dy, dx))
            if   -22.5 <= angle <= 22.5:    self._lancer_atk_dir = 0
            elif  22.5 <  angle <= 67.5:   self._lancer_atk_dir = 3
            elif  angle  > 67.5:           self._lancer_atk_dir = 4
            elif -67.5 <= angle < -22.5:   self._lancer_atk_dir = 1
            else:                           self._lancer_atk_dir = 2
        if self._lancer_is_attacking:
            self._lancer_atk_tk += 1
            if self._lancer_atk_tk >= _ANIM_PERIOD:
                self._lancer_atk_tk = 0
                self._lancer_atk_fr += 1
                atk_len = len(self._lancer_atk[0][0]) if self._lancer_atk else 0
                if self._lancer_atk_fr >= atk_len:
                    self._lancer_is_attacking = False

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        pos   = (int(self.pos.x), int(self.pos.y))
        pulse = int(abs(math.sin(self._tick * 0.06)) * 7)
        pygame.draw.circle(screen, self.COLOR_OUTLINE, pos, self.radius + 5 + pulse, width=3)
        if self._lancer_is_attacking and self._lancer_atk:
            frames_r, frames_l = self._lancer_atk[self._lancer_atk_dir]
            frames = frames_l if self.facing_left else frames_r
            fr     = min(self._lancer_atk_fr, len(frames) - 1)
            screen.blit(frames[fr], (pos[0] - frames[fr].get_width() // 2,
                                      pos[1] - frames[fr].get_height() // 2))
        elif not self._blit_sprite(screen):
            pygame.draw.circle(screen, self.COLOR_BODY, pos, self.radius)


# ---------------------------------------------------------------------------

class SuperBoss(Warrior):
    """Super Boss — alle 50 Wellen. Tötet Spieler mit einem Treffer."""
    RADIUS        = 50
    COLOR_BODY    = ( 70,   0,  15)
    COLOR_OUTLINE = (220,  20,  40)
    COLOR_HP_BAR  = (255,  20,  60)

    _frames_r         = None
    _frames_l         = None
    _lancer_atk       = None
    _atk1_frames_r    = None
    _atk1_frames_l    = None
    _atk2_frames_r    = None
    _atk2_frames_l    = None
    ATTACK_ANIM_RANGE = 140

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=max(0.25, base_speed * 0.2), max_hp=int(base_hp * 25))
        self.coin_value = 50
        self._tick      = 0
        self._lancer_is_attacking = False
        self._lancer_atk_fr       = 0
        self._lancer_atk_tk       = 0
        self._lancer_atk_dir      = 0

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_black_lancer_run(144)
            cls._lancer_atk               = sprite_loader.load_black_lancer_attacks(144)
        except Exception as exc:
            print(f"[SuperBoss] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
            cls._lancer_atk = []

    def _draw_hp_bar(self, screen, pos) -> None:
        pass

    def update(self, target: pygame.math.Vector2) -> None:
        self._tick += 1
        super().update(target)
        if not self._lancer_atk:
            return
        direction = target - self.pos
        dist = direction.length()
        if not self._lancer_is_attacking and dist < self.ATTACK_ANIM_RANGE:
            self._lancer_is_attacking = True
            self._lancer_atk_fr       = 0
            self._lancer_atk_tk       = 0
            dx = direction.x if not self.facing_left else -direction.x
            dy = direction.y
            angle = math.degrees(math.atan2(dy, dx))
            if   -22.5 <= angle <= 22.5:    self._lancer_atk_dir = 0
            elif  22.5 <  angle <= 67.5:   self._lancer_atk_dir = 3
            elif  angle  > 67.5:           self._lancer_atk_dir = 4
            elif -67.5 <= angle < -22.5:   self._lancer_atk_dir = 1
            else:                           self._lancer_atk_dir = 2
        if self._lancer_is_attacking:
            self._lancer_atk_tk += 1
            if self._lancer_atk_tk >= _ANIM_PERIOD:
                self._lancer_atk_tk = 0
                self._lancer_atk_fr += 1
                atk_len = len(self._lancer_atk[0][0]) if self._lancer_atk else 0
                if self._lancer_atk_fr >= atk_len:
                    self._lancer_is_attacking = False

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        pos = (int(self.pos.x), int(self.pos.y))
        for i in range(3):
            pulse = int(abs(math.sin(self._tick * 0.05 + i * 1.1)) * 10)
            pygame.draw.circle(screen, self.COLOR_OUTLINE, pos, self.radius + 8 + i * 13 + pulse, width=2)
        if self._lancer_is_attacking and self._lancer_atk:
            frames_r, frames_l = self._lancer_atk[self._lancer_atk_dir]
            frames = frames_l if self.facing_left else frames_r
            fr     = min(self._lancer_atk_fr, len(frames) - 1)
            screen.blit(frames[fr], (pos[0] - frames[fr].get_width() // 2,
                                      pos[1] - frames[fr].get_height() // 2))
        elif not self._blit_sprite(screen):
            pygame.draw.circle(screen, self.COLOR_BODY, pos, self.radius)

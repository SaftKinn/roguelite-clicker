import math
import random
import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT
from . import balance

# ---------------------------------------------------------------------------
# Feind-Projektil (Archer-Pfeil)
# ---------------------------------------------------------------------------

MUZZLE_TICKS = 7   # Frames, die der Abschuss-/Cast-Flash am Schützen sichtbar ist


class EnemyProjectile:
    SPEED        = 3.5
    RADIUS       = 4
    DAMAGE       = 16   # Archer-Pfeilschaden (tödlicher, ADR 008)
    SHOT_PX      = 18   # Zielgröße eigenes Geschoss-Sprite
    MUZZLE_PX    = 40   # Zielgröße Cast-Flash
    _COLOR_OUTER = (180, 130,  40)
    _COLOR_INNER = (255, 210, 100)
    _arrow_surf  = None
    # Per-Name-Caches: jeder Fernkämpfer (SPRITE_NAME) bekommt sein eigenes Geschoss/
    # seinen eigenen Mündungs-Flash. Fehlt die PNG → Wert False → alter Pfeil-Fallback.
    _shot_cache   = {}
    _muzzle_cache = {}

    @classmethod
    def _get_arrow(cls):
        if cls._arrow_surf is None:
            try:
                from . import sprite_loader
                cls._arrow_surf = sprite_loader.load_arrow(20)
            except Exception:
                cls._arrow_surf = False
        return cls._arrow_surf if cls._arrow_surf else None

    @classmethod
    def _get_shot(cls, name: str):
        """Eigenes Geschoss-Sprite eines Schützen (gecacht je Name). None, wenn die
        PNG fehlt → Aufrufer fällt auf den Standard-Pfeil zurück (Golden Rule 5)."""
        if name not in cls._shot_cache:
            try:
                from . import sprite_loader
                cls._shot_cache[name] = sprite_loader.load_enemy_shot(name, cls.SHOT_PX)
            except Exception:
                cls._shot_cache[name] = False
        surf = cls._shot_cache[name]
        return surf if surf else None

    @classmethod
    def _get_muzzle(cls, name: str):
        """Cast-/Mündungs-Flash eines Schützen (gecacht je Name). None, wenn die PNG fehlt."""
        if name not in cls._muzzle_cache:
            try:
                from . import sprite_loader
                cls._muzzle_cache[name] = sprite_loader.load_enemy_muzzle(name, cls.MUZZLE_PX)
            except Exception:
                cls._muzzle_cache[name] = False
        surf = cls._muzzle_cache[name]
        return surf if surf else None

    def __init__(self, pos: pygame.math.Vector2, target: pygame.math.Vector2,
                 damage: int | None = None, sprite: str | None = None):
        self.pos     = pygame.math.Vector2(pos)
        self.alive   = True
        self.damage  = self.DAMAGE if damage is None else damage   # vom Schützen skaliert (Wellen-Härte)
        self._sprite = sprite                       # SPRITE_NAME des Schützen (oder None → Standard-Pfeil)
        self._spawn  = pygame.math.Vector2(pos)     # Abschussort für den Mündungs-Flash
        self._age    = 0
        direction    = target - self.pos
        self.vel     = (direction.normalize() * self.SPEED
                        if direction.length() > 0 else pygame.math.Vector2(0, 0))
        self._angle  = -math.degrees(math.atan2(self.vel.y, self.vel.x))

    def update(self) -> None:
        self.pos += self.vel
        self._age += 1
        if not (0 <= self.pos.x <= SCREEN_WIDTH and 0 <= self.pos.y <= SCREEN_HEIGHT):
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        p = (int(self.pos.x), int(self.pos.y))
        # (1) Abschuss-/Cast-Flash: kurz am Abschussort, fadet über MUZZLE_TICKS aus.
        if self._sprite and self._age < MUZZLE_TICKS:
            muzzle = self._get_muzzle(self._sprite)
            if muzzle:
                muzzle = muzzle.copy()
                muzzle.set_alpha(int(255 * (1 - self._age / MUZZLE_TICKS)))
                screen.blit(muzzle, (int(self._spawn.x) - muzzle.get_width() // 2,
                                     int(self._spawn.y) - muzzle.get_height() // 2))
        # (2) Geschoss: eigenes Sprite → Standard-Pfeil → gezeichnete Kreise.
        shot = self._get_shot(self._sprite) if self._sprite else None
        arrow = shot or self._get_arrow()
        if arrow:
            rotated = pygame.transform.rotate(arrow, self._angle)
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
        self.dmg_mult    = 1.0   # Wellen-Härte-Faktor auf Schaden (in spawn_enemy_for_wave gesetzt)
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
            return int(self.ATTACK_DAMAGE * self.dmg_mult)   # × Wellen-Härte (alle 10 Wellen +40 %)
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
                    self._shots.append(EnemyProjectile(self.pos, target, round(EnemyProjectile.DAMAGE * self.dmg_mult), sprite=getattr(self, "SPRITE_NAME", None)))
        if self._is_shooting:
            self._shoot_anim_tk += 1
            if self._shoot_anim_tk >= _ANIM_PERIOD:
                self._shoot_anim_tk = 0
                self._shoot_anim_fr += 1
                # Beim Erreichen des Release-Frames (Bogen am höchsten Punkt)
                # den Pfeil auf die aktuelle Zielposition abschießen.
                if self._pending_release and self._shoot_anim_fr >= self.SHOOT_RELEASE_FRAME:
                    self._shots.append(EnemyProjectile(self.pos, target, round(EnemyProjectile.DAMAGE * self.dmg_mult), sprite=getattr(self, "SPRITE_NAME", None)))
                    self._pending_release = False
                shoot_len = len(self._shoot_frames_r) if self._shoot_frames_r else 0
                if self._shoot_anim_fr >= shoot_len:
                    # Animation vorbei: Sicherung, falls Release-Frame > Länge.
                    if self._pending_release:
                        self._shots.append(EnemyProjectile(self.pos, target, round(EnemyProjectile.DAMAGE * self.dmg_mult), sprite=getattr(self, "SPRITE_NAME", None)))
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

class Goblin(Warrior):
    """Schwarm-Rusher — sehr schnell, sehr wenig HP, schwacher Nahkampf.
    Spawnt gehäuft (Massendruck statt Einzelgefahr). Nur eine Lauf-Animation
    (kein eigener Angriff); Fallback bei fehlendem Asset = kleiner grüner Kreis."""
    RADIUS            = 10
    COLOR_BODY        = ( 90, 175,  60)
    COLOR_OUTLINE     = ( 45, 110,  30)
    COLOR_HP_BAR      = (150, 225,  90)
    ATTACK_ANIM_RANGE = 40

    _frames_r      = None
    _frames_l      = None
    _atk1_frames_r = None
    _atk1_frames_l = None
    _atk2_frames_r = None
    _atk2_frames_l = None

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=base_speed * 1.6, max_hp=max(1, int(base_hp * 2.5)))   # 10× zäher (Nutzerwunsch)
        self.coin_value = 1

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_goblin_run(40)
        except Exception as exc:
            print(f"[Goblin] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
        # Goblin hat keine Angriffs-Animation → leere Listen, damit Warrior.update/draw
        # den Attack-Zweig überspringen (er feiert dennoch Nahkampf via melee_attack).
        cls._atk1_frames_r = cls._atk1_frames_l = []
        cls._atk2_frames_r = cls._atk2_frames_l = []


# ---------------------------------------------------------------------------

class OrcBerserker(Warrior):
    """Brecher — langsam, sehr viel HP, doppelter Nahkampfschaden.
    Nutzt die schon angelegten orc_warrior-Sheets (run + attack); Fallback = grüner Kreis."""
    RADIUS            = 20
    COLOR_BODY        = ( 85, 125,  70)
    COLOR_OUTLINE     = ( 40,  70,  40)
    COLOR_HP_BAR      = (130, 205, 105)
    ATTACK_ANIM_RANGE = 70
    DAMAGE_MULT       = 2     # doppelter Nahkampfschaden ggü. Basis-Warrior (benannte Konstante)

    _frames_r      = None
    _frames_l      = None
    _atk1_frames_r = None
    _atk1_frames_l = None
    _atk2_frames_r = None
    _atk2_frames_l = None

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=max(0.4, base_speed * 0.5), max_hp=int(base_hp * 25))   # 10× zäher (Nutzerwunsch; zäher als SuperBoss)
        self.coin_value   = 4
        self.ATTACK_DAMAGE = balance.ATTACK_DAMAGE * self.DAMAGE_MULT

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_orc_warrior_run(56)
        except Exception as exc:
            print(f"[OrcBerserker] Run-Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
        # Angriffs-Animation ist OPTIONAL (der statische Ork hat keine) — separat laden,
        # damit ein fehlendes Attack-Sheet die Lauf-Sprites nicht mit wegreißt. Ohne
        # Attack-Frames überspringt Warrior.draw den Angriffs-Zweig; Nahkampf läuft
        # weiter über melee_attack().
        try:
            from . import sprite_loader
            cls._atk1_frames_r, cls._atk1_frames_l = sprite_loader.load_orc_warrior_attack(56)
            # Nur eine Angriffs-Animation → für beide Alternierungs-Slots dieselbe nutzen.
            cls._atk2_frames_r, cls._atk2_frames_l = cls._atk1_frames_r, cls._atk1_frames_l
        except Exception:
            cls._atk1_frames_r = cls._atk1_frames_l = []
            cls._atk2_frames_r = cls._atk2_frames_l = []


# ---------------------------------------------------------------------------

class Necromancer(Warrior):
    """Beschwörer — bleibt auf Distanz und ruft periodisch Goblins (gedeckelt).
    Offensives Gegenstück zum Monk-Heiler. main.py holt frische Beschwörungen via
    pop_summons() (analog Archer.pop_shots). Fallback = lila Kreis + Beschwör-Aura."""
    RADIUS        = 11
    # ATTACK_RANGE muss < PLAYER_ATTACK_RANGE (~236 px) bleiben, sonst kitet der
    # Beschwörer JENSEITS der Turm-Reichweite und ist unerreichbar → Soft-Lock,
    # sobald er der letzte Gegner ist und SUMMON_MAX erreicht hat.
    ATTACK_RANGE  = 220
    SHOOT_EVERY   = 110     # Ticks zwischen Pfeilschüssen (Übergangs-Angriff)
    SUMMON_EVERY  = 240     # Ticks zwischen Beschwörungen (~4 s bei 60 FPS)
    SUMMON_COUNT  = 2       # Beschwörungen pro Welle
    SUMMON_MAX    = 6       # lebenslanges Limit pro Nekromant (gegen Runaway-Spawn)
    SUMMON_CLASS  = Goblin  # welcher Schwarm-Gegner beschworen wird (Tier-Reskins überschreiben)
    COLOR_BODY    = (120,  70, 165)
    COLOR_OUTLINE = ( 70,  40, 100)
    COLOR_HP_BAR  = (185, 110, 225)

    _frames_r  = None
    _frames_l  = None
    _aura_surf = None
    _AURA_R    = 55

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=base_speed * 0.9, max_hp=int(base_hp * 6.0))   # 10× zäher (Nutzerwunsch)
        self.coin_value    = 4
        self._summon_timer = random.randint(60, self.SUMMON_EVERY)
        self._summoned     = 0
        self._summons: list = []   # frisch beschworene Goblins; main.py leert die Liste
        self._shoot_timer  = random.randint(30, self.SHOOT_EVERY)
        self._shots: list[EnemyProjectile] = []   # Pfeile; main.py holt sie via pop_shots
        self._aura_timer   = 0
        # Roh-Wellenwerte merken, um beschworene Goblins passend zur Welle zu skalieren.
        self._base_speed   = base_speed
        self._base_hp      = base_hp

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_necromancer_run(46)
        except Exception as exc:
            print(f"[Necromancer] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []

    @classmethod
    def _get_aura(cls) -> pygame.Surface:
        if cls._aura_surf is None:
            size = cls._AURA_R * 2
            cls._aura_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(cls._aura_surf, (150, 60, 200, 70),
                               (cls._AURA_R, cls._AURA_R), cls._AURA_R)
        return cls._aura_surf

    def update(self, target: pygame.math.Vector2) -> None:
        direction = target - self.pos
        dist      = direction.length()
        in_range  = dist <= self.ATTACK_RANGE
        if not in_range:
            vel = direction.normalize() * self.speed
            if abs(vel.x) > 0.05:
                self.facing_left = vel.x < 0
            self.pos += vel
        elif dist > 0:
            self.facing_left = direction.x < 0
        # Übergangs-Angriff (Nutzerwunsch): in Reichweite feuert der Beschwörer
        # zusätzlich einen Pfeil wie der Archer. Hält ihn aktiv, auch nachdem
        # SUMMON_MAX erreicht ist — sonst stünde er nur noch untätig herum.
        if in_range:
            self._shoot_timer -= 1
            if self._shoot_timer <= 0:
                self._shoot_timer = self.SHOOT_EVERY
                self._shots.append(EnemyProjectile(
                    self.pos, target, round(EnemyProjectile.DAMAGE * self.dmg_mult),
                    sprite=getattr(self, "SPRITE_NAME", None)))
        self._summon_timer -= 1
        if self._summon_timer <= 0 and self._summoned < self.SUMMON_MAX:
            self._summon_timer = self.SUMMON_EVERY
            self._aura_timer   = 40
            for _ in range(self.SUMMON_COUNT):
                if self._summoned >= self.SUMMON_MAX:
                    break
                g = self.SUMMON_CLASS(self._base_speed, self._base_hp)
                # Direkt neben dem Nekromanten erscheinen (statt am Bildrand).
                g.pos = pygame.math.Vector2(self.pos.x + random.randint(-25, 25),
                                            self.pos.y + random.randint(-25, 25))
                self._summons.append(g)
                self._summoned += 1
        if self._aura_timer > 0:
            self._aura_timer -= 1
        self._anim_tick += 1
        if self._anim_tick >= _ANIM_PERIOD:
            self._anim_tick = 0
            if self._frames_r:
                self._anim_frame = (self._anim_frame + 1) % len(self._frames_r)

    def pop_summons(self) -> list:
        summons = list(self._summons)
        self._summons.clear()
        return summons

    def pop_shots(self) -> list[EnemyProjectile]:
        shots = list(self._shots)
        self._shots.clear()
        return shots

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        pos = (int(self.pos.x), int(self.pos.y))
        if self._aura_timer > 0:
            aura  = self._get_aura()
            aura.set_alpha(int(self._aura_timer / 40 * 255))
            screen.blit(aura, (pos[0] - self._AURA_R, pos[1] - self._AURA_R))
        if not self._blit_sprite(screen):
            pygame.draw.circle(screen, self.COLOR_OUTLINE, pos, self.radius + 2)
            pygame.draw.circle(screen, self.COLOR_BODY,    pos, self.radius)
        self._draw_hp_bar(screen, pos)


# ---------------------------------------------------------------------------
# Tier-Gegner (ADR 024): 3 Wellen-Abschnitte × 5 Archetypen = 15 reskinnte Gegner.
# Sie ERBEN die Mechanik der fünf Rollen-Klassen (Warrior/Goblin/Archer/OrcBerserker/
# Necromancer) und tauschen nur die Optik: Lauf-Sprite aus assets/custom/<name>_run.png
# (per tools/animate_walk.py aus EINEM Standbild gebaut). Fehlt das PNG, greift
# Golden Rule 5 → gezeichnetes Primitiv in der Tier-Farbe. Spawn-Auswahl: main.py.
# ---------------------------------------------------------------------------

class _CustomSpriteMixin:
    """Lädt die Lauf-Animation eines Reskins aus assets/custom/<SPRITE_NAME>_run.png.
    Keine eigene Angriffs-Animation (Attack-/Schuss-Frames bleiben leer → die geerbte
    Mechanik feuert weiter, nur ohne Spezial-Animation, exakt wie beim Goblin)."""
    SPRITE_NAME = ""        # von der konkreten Klasse gesetzt
    SPRITE_PX   = 48
    _frames_r = _frames_l = None
    _atk1_frames_r = _atk1_frames_l = None
    _atk2_frames_r = _atk2_frames_l = None

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            cls._frames_r, cls._frames_l = sprite_loader.load_custom_enemy(cls.SPRITE_NAME, cls.SPRITE_PX)
        except Exception as exc:
            print(f"[{cls.__name__}] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []
        cls._atk1_frames_r = cls._atk1_frames_l = []
        cls._atk2_frames_r = cls._atk2_frames_l = []


# Rollen-Basisklassen: Mixin (Sprites) + Mechanik-Klasse. target_px je Rolle.
class _CustomMelee(_CustomSpriteMixin, Warrior):      SPRITE_PX = 50   # Nahkampf
class _CustomSwarm(_CustomSpriteMixin, Goblin):       SPRITE_PX = 40   # Schwarm (schnell, wenig HP)
class _CustomRanged(_CustomSpriteMixin, Archer):      SPRITE_PX = 48   # Fernkampf (schießt)
class _CustomTank(_CustomSpriteMixin, OrcBerserker):  SPRITE_PX = 60   # Tank/Brecher (sehr zäh)
class _CustomSummoner(_CustomSpriteMixin, Necromancer): SPRITE_PX = 48 # Beschwörer


# --- Tier 1 — Untote / Knochen-Legion (Welle 1–50) ------------------------
class SkeletonWarrior(_CustomMelee):
    SPRITE_NAME = "skeleton_warrior"
    COLOR_BODY, COLOR_OUTLINE = (215, 215, 200), (120, 120, 105)

class BoneSwarmling(_CustomSwarm):
    SPRITE_NAME = "bone_swarmling"
    COLOR_BODY, COLOR_OUTLINE = (180, 200, 150), (95, 120, 80)

class SkeletonArcher(_CustomRanged):
    SPRITE_NAME = "skeleton_archer"
    COLOR_BODY, COLOR_OUTLINE = (200, 205, 185), (110, 115, 95)

class BoneColossus(_CustomTank):
    SPRITE_NAME = "bone_colossus"
    COLOR_BODY, COLOR_OUTLINE = (225, 220, 205), (140, 130, 110)

class Lich(_CustomSummoner):
    SPRITE_NAME  = "lich"
    SUMMON_CLASS = BoneSwarmling
    COLOR_BODY, COLOR_OUTLINE = (130, 190, 150), (60, 110, 80)


# --- Tier 2 — Dämonen / Höllenbrut (Welle 51–100) -------------------------
class ImpWarrior(_CustomMelee):
    SPRITE_NAME = "imp_warrior"
    COLOR_BODY, COLOR_OUTLINE = (210, 70, 50), (130, 30, 25)

class Hellhound(_CustomSwarm):
    SPRITE_NAME = "hellhound"
    COLOR_BODY, COLOR_OUTLINE = (235, 120, 40), (150, 60, 20)

class DemonCaster(_CustomRanged):
    SPRITE_NAME = "demon_caster"
    COLOR_BODY, COLOR_OUTLINE = (230, 95, 60), (140, 45, 30)

class PitBrute(_CustomTank):
    SPRITE_NAME = "pit_brute"
    COLOR_BODY, COLOR_OUTLINE = (170, 60, 55), (100, 30, 30)

class DemonSummoner(_CustomSummoner):
    SPRITE_NAME  = "demon_summoner"
    SUMMON_CLASS = Hellhound
    COLOR_BODY, COLOR_OUTLINE = (200, 60, 90), (120, 30, 55)


# --- Tier 3 — Drachen-Brut / Schuppen (Welle 101–150) ---------------------
class DrakeWarrior(_CustomMelee):
    SPRITE_NAME = "drake_warrior"
    COLOR_BODY, COLOR_OUTLINE = (70, 160, 110), (35, 95, 65)

class Wyrmling(_CustomSwarm):
    SPRITE_NAME = "wyrmling"
    COLOR_BODY, COLOR_OUTLINE = (110, 200, 140), (60, 120, 80)

class DrakeArcher(_CustomRanged):
    SPRITE_NAME = "drake_archer"
    COLOR_BODY, COLOR_OUTLINE = (90, 175, 150), (45, 105, 90)

class ScaleTitan(_CustomTank):
    SPRITE_NAME = "scale_titan"
    COLOR_BODY, COLOR_OUTLINE = (60, 130, 120), (30, 80, 70)

class DragonPriest(_CustomSummoner):
    SPRITE_NAME  = "dragon_priest"
    SUMMON_CLASS = Wyrmling
    COLOR_BODY, COLOR_OUTLINE = (190, 165, 70), (115, 95, 35)


# --- Tanker (Lancer) & Heiler (Monk) als Tier-Reskins ----------------------
# Anders als die 5 Rollen oben haben Lancer/Monk reiche Spezial-Animationen
# (Lancer: Richtungsangriffe, Monk: Heilung). Der Reskin tauscht NUR die Lauf-
# Frames gegen assets/custom/<SPRITE_NAME>_run.png; fehlt das PNG, bleibt das
# Tiny-Swords-Original (kein Primitiv-Kreis, also KEINE Regression). Spezial-
# Animationen bleiben immer das Original. Jede Leaf-Klasse deklariert ihre Sprite-
# Caches neu (= None), damit sich die Tier-Skins nicht teilen.
class _LancerReskin(Lancer):
    SPRITE_NAME = ""
    SPRITE_PX   = 90

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        super()._load_sprites()                       # Original-Walk + Lancer-Angriffe (Fallback)
        from . import sprite_loader
        try:
            fr, fl = sprite_loader.load_custom_enemy(cls.SPRITE_NAME, cls.SPRITE_PX)
            if fr:                                     # nur ersetzen, wenn das PNG wirklich da ist
                cls._frames_r, cls._frames_l = fr, fl
        except Exception:
            pass


class _MonkReskin(Monk):
    SPRITE_NAME = ""
    SPRITE_PX   = 44

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        super()._load_sprites()                       # Original-Walk + Heil-Animation (Fallback)
        from . import sprite_loader
        try:
            fr, fl = sprite_loader.load_custom_enemy(cls.SPRITE_NAME, cls.SPRITE_PX)
            if fr:
                cls._frames_r, cls._frames_l = fr, fl
        except Exception:
            pass


# Tier 1 — Untote
class SkeletonLancer(_LancerReskin):
    SPRITE_NAME = "skeleton_lancer"
    _frames_r = _frames_l = None
    _lancer_atk = None
    COLOR_BODY, COLOR_OUTLINE = (210, 210, 195), (120, 120, 105)

class SkeletonMonk(_MonkReskin):
    SPRITE_NAME = "skeleton_monk"
    _frames_r = _frames_l = None
    _heal_frames_r = _heal_frames_l = None
    _heal_fx_frames = None
    COLOR_BODY, COLOR_OUTLINE = (170, 200, 175), (90, 120, 95)

# Tier 2 — Dämonen
class DemonLancer(_LancerReskin):
    SPRITE_NAME = "demon_lancer"
    _frames_r = _frames_l = None
    _lancer_atk = None
    COLOR_BODY, COLOR_OUTLINE = (185, 60, 50), (110, 30, 25)

class DemonMonk(_MonkReskin):
    SPRITE_NAME = "demon_monk"
    _frames_r = _frames_l = None
    _heal_frames_r = _heal_frames_l = None
    _heal_fx_frames = None
    COLOR_BODY, COLOR_OUTLINE = (215, 110, 70), (135, 55, 35)

# Tier 3 — Drachen-Brut
class DrakeLancer(_LancerReskin):
    SPRITE_NAME = "drake_lancer"
    _frames_r = _frames_l = None
    _lancer_atk = None
    COLOR_BODY, COLOR_OUTLINE = (70, 150, 115), (35, 90, 70)

class DrakeMonk(_MonkReskin):
    SPRITE_NAME = "drake_monk"
    _frames_r = _frames_l = None
    _heal_frames_r = _heal_frames_l = None
    _heal_fx_frames = None
    COLOR_BODY, COLOR_OUTLINE = (90, 180, 150), (45, 110, 90)


# ---------------------------------------------------------------------------

class Boss(Warrior):
    """Boss — alle 10 Wellen. Tötet Spieler mit einem Treffer.

    Ohne SPRITE_NAME: Tiny-Swords Black-Lancer als Platzhalter (mit Stoß-Animation).
    Eine Tier-Subklasse setzt SPRITE_NAME → eigenes Boss-Sprite (frontale Pose) aus
    assets/custom/<name>_run.png; dann entfällt die Lancer-Stoß-Anim (Walk reicht)."""
    RADIUS        = 34
    COLOR_BODY    = (160,  65,  10)
    COLOR_OUTLINE = (255, 155,  25)
    COLOR_HP_BAR  = (255, 140,  20)

    SPRITE_NAME       = None    # None → Lancer-Platzhalter; gesetzt → Tier-Reskin
    SPRITE_PX         = 96      # Zielgröße (wie der bisherige Lancer-Boss)
    _frames_r         = None
    _frames_l         = None
    _lancer_atk       = None
    _atk1_frames_r    = None
    _atk1_frames_l    = None
    _atk2_frames_r    = None
    _atk2_frames_l    = None
    ATTACK_ANIM_RANGE = 120

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=max(0.4, base_speed * 0.35),
                         max_hp=int(base_hp * balance.BOSS_HP_MULT))
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
            if cls.SPRITE_NAME:   # Tier-Reskin: eigenes Boss-Sprite (frontale Pose)
                cls._frames_r, cls._frames_l = sprite_loader.load_custom_enemy(cls.SPRITE_NAME, cls.SPRITE_PX)
                cls._lancer_atk = []          # eigenes Sprite hat keine Lancer-Stoß-Anim → Walk-Frames reichen
            else:                 # Platzhalter: Tiny-Swords Black-Lancer (mit Stoß-Animation)
                cls._frames_r, cls._frames_l = sprite_loader.load_black_lancer_run(cls.SPRITE_PX)
                cls._lancer_atk               = sprite_loader.load_black_lancer_attacks(cls.SPRITE_PX)
        except Exception as exc:
            print(f"[{cls.__name__}] Sprites: {exc}")
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


# Tier-Bosse (alle 10 Wellen): je 50-Wellen-Abschnitt ein eigenes Boss-Sprite
# (frontale Pose, assets/custom/tier{1,2,3}_boss_run.png). Jede Subklasse braucht
# EIGENE _frames_r/_frames_l (sonst teilen sie sich den Klassen-Cache der Basis);
# nur Optik (SPRITE_NAME) und Fallback-Farben tauschen, Mechanik bleibt identisch.
class Tier1Boss(Boss):     # Welle 10/20/30/40 — Untoter Champion
    SPRITE_NAME   = "tier1_boss"
    _frames_r     = None
    _frames_l     = None
    _lancer_atk   = None
    COLOR_BODY    = (200, 205, 225)
    COLOR_OUTLINE = (150, 165, 205)
    COLOR_HP_BAR  = (170, 185, 225)

class Tier2Boss(Boss):     # Welle 60/70/80/90 — Dämonen Champion
    SPRITE_NAME   = "tier2_boss"
    _frames_r     = None
    _frames_l     = None
    _lancer_atk   = None
    COLOR_BODY    = ( 70,  10,  15)
    COLOR_OUTLINE = (235,  85,  35)
    COLOR_HP_BAR  = (255,  95,  40)

class Tier3Boss(Boss):     # Welle 110/120/130/140 — Drachen-Brut Champion
    SPRITE_NAME   = "tier3_boss"
    _frames_r     = None
    _frames_l     = None
    _lancer_atk   = None
    COLOR_BODY    = ( 90, 140, 200)
    COLOR_OUTLINE = (140, 200, 240)
    COLOR_HP_BAR  = (150, 205, 240)


# ---------------------------------------------------------------------------

class SuperBoss(Warrior):
    """Super Boss (Drache) — alle 50 Wellen. Tötet Spieler mit einem Treffer.
    Geerdeter Walk-Zyklus (Seitenansicht, Kopf links) — der Drache LÄUFT am Boden
    (Wippen ist im Sprite gebacken, kein Schweben). Betritt das Bild nur vom Ost- oder
    Westrand (horizontaler Anmarsch → Blickrichtung passt zur Bewegung)."""
    RADIUS        = 60     # an die große Drachen-Sprite angepasst (Stop-Distanz + Aura-Ringe)
    SPRITE_PX     = 240    # Zielbreite des Walk-Sprites (Höhe proportional, Seitenverhältnis bleibt)
    COLOR_BODY    = ( 70,   0,  15)
    COLOR_OUTLINE = (220,  20,  40)
    COLOR_HP_BAR  = (255,  20,  60)

    # Angriffs-Animation OHNE eigenes Sprite (Code-only): ein kurzer Vorwärts-Satz (Lunge)
    # auf den Turm + Skalier-/Aura-Blitz, ausgelöst nahe am Turm und dann auf Cooldown.
    # Alles rein visuell (`self.pos`/Schaden bleiben unberührt) — die sin(p·π)-Hüllkurve
    # schießt raus und kommt zurück (0 am Anfang/Ende, Maximum in der Mitte).
    ATTACK_RANGE_PX   = 130    # Distanz zum Turm, ab der ein Angriff startet
    ATTACK_DURATION   = 22     # Ticks, die ein Lunge dauert
    ATTACK_INTERVAL   = 80     # Ticks Cooldown zwischen zwei Angriffen
    ATTACK_LUNGE_PX   = 46     # Spitzen-Versatz des Lunge Richtung Turm (Pixel)
    ATTACK_SCALE      = 1.16   # Spitzen-Vergrößerung des Sprites im Angriffsmoment

    # None → bestehender Seitenansicht-Drache (load_drache_superboss). Eine Subklasse
    # setzt einen Namen → Reskin aus assets/custom/<SPRITE_NAME>_run.png (animate_walk).
    SPRITE_NAME       = None
    _frames_r         = None
    _frames_l         = None

    def __init__(self, base_speed: float, base_hp: int):
        super().__init__(speed=max(0.25, base_speed * 0.2),
                         max_hp=int(base_hp * balance.SUPERBOSS_HP_MULT))
        self.coin_value = 50
        self._tick      = 0
        self._atk_active = False
        self._atk_t      = 0      # Fortschritt im laufenden Lunge (0..ATTACK_DURATION)
        self._atk_cd     = self.ATTACK_INTERVAL   # erst nach kurzer Annäherung angreifen
        self._atk_dir    = pygame.math.Vector2(0, 0)   # Lunge-Richtung (zum Turm, bei Start fixiert)
        # Drache betritt das Bild nur horizontal (Ost/West) auf Turm-Höhe → die
        # Seitenansicht passt immer zur Laufrichtung (statt aller vier Ränder).
        side = random.choice(("left", "right"))
        self.pos = pygame.math.Vector2(0 if side == "left" else SCREEN_WIDTH,
                                       SCREEN_HEIGHT // 2)
        self.facing_left = (side == "right")

    @classmethod
    def _load_sprites(cls) -> None:
        if cls._frames_r is not None:
            return
        try:
            from . import sprite_loader
            if cls.SPRITE_NAME:   # Tier-Reskin (Untoter/Dämon) aus assets/custom/<name>_run.png
                cls._frames_r, cls._frames_l = sprite_loader.load_custom_enemy(cls.SPRITE_NAME, cls.SPRITE_PX)
            else:                 # Original-Drache (Seitenansicht-Walk)
                cls._frames_r, cls._frames_l = sprite_loader.load_drache_superboss(cls.SPRITE_PX)
        except Exception as exc:
            print(f"[{cls.__name__}] Sprites: {exc}")
            cls._frames_r = cls._frames_l = []

    def _draw_hp_bar(self, screen, pos) -> None:
        pass

    def update(self, target: pygame.math.Vector2) -> None:
        self._tick += 1
        super().update(target)   # Bewegung + Flügelschlag-Zyklus (cycelt _anim_frame)
        # Angriff auslösen, sobald der Drache am Turm ist und der Cooldown abgelaufen ist.
        if self._atk_cd > 0:
            self._atk_cd -= 1
        if self._atk_active:
            self._atk_t += 1
            if self._atk_t >= self.ATTACK_DURATION:   # Lunge fertig → zurück, Cooldown starten
                self._atk_active = False
                self._atk_cd     = self.ATTACK_INTERVAL
        else:
            direction = target - self.pos
            if self._atk_cd <= 0 and 0 < direction.length() < self.ATTACK_RANGE_PX:
                self._atk_active = True
                self._atk_t      = 0
                self._atk_dir    = direction.normalize()   # Richtung bei Start fixieren

    def _attack_envelope(self) -> float:
        """0→1→0-Hüllkurve des laufenden Lunge (Maximum in der Mitte); 0 wenn inaktiv."""
        if not self._atk_active:
            return 0.0
        return math.sin(self._atk_t / self.ATTACK_DURATION * math.pi)

    def draw(self, screen: pygame.Surface) -> None:
        self._load_sprites()
        env = self._attack_envelope()
        # Geerdet: kein Schwebe-Versatz (das Wippen steckt im Walk-Sprite). Nur der
        # Lunge Richtung Turm im Angriff verschiebt die Zeichen-Position (env·Richtung·Reichweite).
        cx = int(self.pos.x + self._atk_dir.x * env * self.ATTACK_LUNGE_PX)
        cy = int(self.pos.y + self._atk_dir.y * env * self.ATTACK_LUNGE_PX)
        # Aura-Ringe pulsieren immer; im Angriff zucken sie heller und enger zusammen.
        ring_w = 2 + int(env * 3)
        for i in range(3):
            pulse = int(abs(math.sin(self._tick * 0.05 + i * 1.1)) * 10)
            pygame.draw.circle(screen, self.COLOR_OUTLINE, (cx, cy),
                               self.radius + 8 + i * 13 + pulse - int(env * 14), width=ring_w)
        frames = self._frames_l if self.facing_left else self._frames_r
        if frames:
            frame = frames[self._anim_frame % len(frames)]
            if env > 0:   # im Angriff kurz vergrößern (Scale-Blitz)
                scale = 1 + env * (self.ATTACK_SCALE - 1)
                frame = pygame.transform.smoothscale(
                    frame, (int(frame.get_width() * scale), int(frame.get_height() * scale)))
            screen.blit(frame, (cx - frame.get_width() // 2, cy - frame.get_height() // 2))
        else:
            pygame.draw.circle(screen, self.COLOR_BODY, (cx, cy), self.radius)


# Tier-SuperBosse (ADR 024): je 50-Wellen-Abschnitt ein eigener Endgegner.
# Jede Subklasse braucht EIGENE _frames_r/_frames_l (sonst teilen sie sich den
# Klassen-Cache der Basis). Sprite-/Mechanik-Erbe von SuperBoss bleibt identisch;
# nur Optik (SPRITE_NAME → assets/custom/<name>_run.png) und Fallback-Farben tauschen.
class UndeadSuperBoss(SuperBoss):     # Welle 50 — Knochen-Lord
    SPRITE_NAME   = "undead_boss"
    _frames_r     = None
    _frames_l     = None
    COLOR_BODY    = (210, 210, 225)
    COLOR_OUTLINE = (150, 165, 205)
    COLOR_HP_BAR  = (170, 185, 225)

class DemonSuperBoss(SuperBoss):      # Welle 100 — Archdämon
    SPRITE_NAME   = "demon_boss"
    _frames_r     = None
    _frames_l     = None
    COLOR_BODY    = ( 70,  10,  15)
    COLOR_OUTLINE = (235,  85,  35)
    COLOR_HP_BAR  = (255,  95,  40)

class DragonSuperBoss(SuperBoss):     # Welle 150 — Drachen-Overlord (frontaler Eis-Drache)
    SPRITE_NAME   = "dragon_boss"     # → assets/custom/dragon_boss_run.png (SPRITE_NAME=None: alter Seitenansicht-Drache)
    _frames_r     = None
    _frames_l     = None
    COLOR_BODY    = ( 90, 140, 200)
    COLOR_OUTLINE = (140, 200, 240)
    COLOR_HP_BAR  = (150, 205, 240)

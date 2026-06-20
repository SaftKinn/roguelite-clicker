import math
import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT

COLOR        = (255, 220, 60)

_surf_cache: dict = {}
BASE_SPEED   = 10
BASE_DAMAGE  = 10
BASE_RADIUS  = 5


class Projectile:
    def __init__(self, origin, target=None, damage=BASE_DAMAGE,
                 speed=BASE_SPEED, radius=BASE_RADIUS, pierce=False, vel=None):
        self.pos    = pygame.math.Vector2(origin)
        self.alive  = True
        self.damage = damage
        self.radius = radius
        self.pierce = pierce

        if vel is not None:
            self.vel = vel
        elif target is not None:
            direction = pygame.math.Vector2(target) - self.pos
            self.vel  = direction.normalize() * speed if direction.length() > 0 else pygame.math.Vector2(0, -speed)
        else:
            self.vel = pygame.math.Vector2(0, -speed)

    def update(self) -> None:
        self.pos += self.vel
        if (self.pos.x < 0 or self.pos.x > SCREEN_WIDTH or
                self.pos.y < 0 or self.pos.y > SCREEN_HEIGHT):
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        size = max(8, self.radius * 2)
        key = ("ball", size)
        if key not in _surf_cache:
            try:
                import sprite_loader
                _surf_cache[key] = sprite_loader.load_cannonball(size)
            except Exception:
                _surf_cache[key] = None
        ball = _surf_cache[key]
        p = (int(self.pos.x), int(self.pos.y))
        if ball:
            screen.blit(ball, (p[0] - size // 2, p[1] - size // 2))
        else:
            pygame.draw.circle(screen, COLOR, p, self.radius)

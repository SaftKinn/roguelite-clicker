import random
import pygame

LIFETIME      = 48
RISE_SPEED    = 0.9
COLOR_DAMAGE  = (255, 230, 70)
COLOR_COIN    = (255, 210, 0)


class DamageNumber:
    def __init__(self, x: float, y: float, amount: int,
                 color: tuple = COLOR_DAMAGE, prefix: str = ""):
        self.x        = x + random.randint(-12, 12)
        self.y        = float(y)
        self.text     = f"{prefix}{amount}"
        self.color    = color
        self.lifetime = LIFETIME
        self.alive    = True

    def update(self) -> None:
        self.y        -= RISE_SPEED
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        alpha = int(255 * (self.lifetime / LIFETIME))
        surf  = font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        screen.blit(surf, (int(self.x) - surf.get_width() // 2, int(self.y)))

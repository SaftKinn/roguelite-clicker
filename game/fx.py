import math
import random
import pygame

LIFETIME      = 48
RISE_SPEED    = 0.9
COLOR_DAMAGE  = (255, 230, 70)
COLOR_COIN    = (255, 210, 0)

# --- Juice-/FX-Layer (ADR 035): rein visuell, keine Gameplay-Kopplung. Tuning hier ---
PARTICLE_GRAVITY = 0.12          # Schwerkraft je Tick (Poof/Staub fallen zurück)
POOF_COUNT       = 11            # Partikel pro Todes-Poof
POOF_LIFETIME    = 26            # Ticks bis ein Poof-Partikel verschwindet
POOF_SPEED       = (1.4, 3.6)    # min/max Anfangsgeschwindigkeit (radial)
POOF_COLOR       = (235, 235, 245)
POOF_RADIUS      = (2, 4)        # min/max Startradius eines Partikels

MUZZLE_LIFETIME  = 6             # Ticks, die ein Mündungsblitz lebt
MUZZLE_RADIUS    = 17            # Startradius des Blitzes
MUZZLE_COLOR     = (255, 225, 130)

TRAIL_LIFETIME   = 9             # Ticks, die ein Projektil-Schweifpunkt lebt
TRAIL_COLOR      = (255, 205, 90)
TRAIL_RADIUS     = 4
TRAIL_EVERY      = 1             # nur jeden N-ten Frame einen Schweifpunkt setzen

DUST_LIFETIME    = 16            # Ticks für ein Laufstaub-Partikel
DUST_COLOR       = (185, 165, 135)


class Particle:
    """Physik-getriebenes Partikel (Poof/Staub/Funke) — gleiches Protokoll wie DamageNumber."""

    def __init__(self, x: float, y: float, vx: float, vy: float, lifetime: int,
                 color: tuple, radius: float = 3.0,
                 gravity: float = PARTICLE_GRAVITY, shrink: bool = True):
        self.x        = float(x)
        self.y        = float(y)
        self.vx       = vx
        self.vy       = vy
        self.lifetime = lifetime
        self.max_life = max(1, lifetime)
        self.color    = color
        self.radius   = float(radius)
        self.gravity  = gravity
        self.shrink   = shrink
        self.alive    = True

    def update(self) -> None:
        self.x        += self.vx
        self.y        += self.vy
        self.vy       += self.gravity
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        t = self.lifetime / self.max_life            # 1 .. 0
        r = max(1, int(self.radius * t)) if self.shrink else max(1, int(self.radius))
        a = int(255 * t)
        # screen (world_surf) ist SRCALPHA → RGBA-Kreis blendet direkt, ohne Temp-Surface.
        pygame.draw.circle(screen, (*self.color, a), (int(self.x), int(self.y)), r)


class MuzzleFlash:
    """Kurzer additiver Lichtblitz am Abschussort (Turm/Fernkämpfer)."""

    def __init__(self, x: float, y: float, radius: int = MUZZLE_RADIUS,
                 color: tuple = MUZZLE_COLOR, lifetime: int = MUZZLE_LIFETIME):
        self.x        = float(x)
        self.y        = float(y)
        self.radius   = radius
        self.color    = color
        self.lifetime = lifetime
        self.max_life = max(1, lifetime)
        self.alive    = True

    def update(self) -> None:
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        t = self.lifetime / self.max_life            # 1 .. 0
        r = max(1, int(self.radius * (0.55 + 0.45 * t)))   # schrumpft leicht
        d = r * 2
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        # BLEND_RGB_ADD ignoriert den Quell-Alpha → RGB mit Restlebensdauer skalieren,
        # damit der Blitz tatsächlich ausfadet. Heller weißer Kern + farbiger Hof.
        col  = tuple(int(c * t) for c in self.color)
        pygame.draw.circle(surf, col, (r, r), r)
        pygame.draw.circle(surf, (int(255 * t),) * 3, (r, r), max(1, r // 2))
        screen.blit(surf, (int(self.x) - r, int(self.y) - r),
                    special_flags=pygame.BLEND_RGB_ADD)


class TrailDot:
    """Fadender Punkt entlang der Projektilbahn."""

    def __init__(self, x: float, y: float, color: tuple = TRAIL_COLOR,
                 radius: int = TRAIL_RADIUS, lifetime: int = TRAIL_LIFETIME):
        self.x        = float(x)
        self.y        = float(y)
        self.color    = color
        self.radius   = radius
        self.lifetime = lifetime
        self.max_life = max(1, lifetime)
        self.alive    = True

    def update(self) -> None:
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        t = self.lifetime / self.max_life
        r = max(1, int(self.radius * t))
        a = int(200 * t)
        pygame.draw.circle(screen, (*self.color, a), (int(self.x), int(self.y)), r)


# --- Spawner: geben Listen zurück, der Aufrufer hängt sie an seine fx-Liste an
#     (`fx += spawn_*()`), analog zu `gs["projectiles"] += spawn_projectiles(...)`. ---

def spawn_death_poof(x: float, y: float, color: tuple = POOF_COLOR,
                     count: int = POOF_COUNT) -> list:
    """Radialer Partikel-Burst beim Kill."""
    parts = []
    for i in range(count):
        ang = 2 * math.pi * i / count + random.uniform(-0.4, 0.4)
        spd = random.uniform(*POOF_SPEED)
        vx  = math.cos(ang) * spd
        vy  = math.sin(ang) * spd - 1.0          # leichter Aufwärts-Bias
        parts.append(Particle(x, y, vx, vy, POOF_LIFETIME, color,
                              radius=random.randint(*POOF_RADIUS)))
    return parts


def spawn_muzzle_flash(x: float, y: float, radius: int = MUZZLE_RADIUS,
                       color: tuple = MUZZLE_COLOR) -> list:
    return [MuzzleFlash(x, y, radius=radius, color=color)]


def spawn_trail(x: float, y: float, color: tuple = TRAIL_COLOR) -> list:
    return [TrailDot(x, y, color=color)]


def spawn_dust(x: float, y: float) -> list:
    """1–2 kleine, kurzlebige Bodenpartikel unter laufenden Gegnern."""
    parts = []
    for _ in range(random.randint(1, 2)):
        vx = random.uniform(-0.6, 0.6)
        parts.append(Particle(x + random.uniform(-4, 4), y, vx, -0.4,
                              DUST_LIFETIME, DUST_COLOR,
                              radius=random.randint(2, 3), gravity=0.05))
    return parts


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

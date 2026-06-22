import math
import array
import os
import pygame

SAMPLE_RATE = 22050
_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MUSIC_RUN  = os.path.join(_DIR, "assets", "audio", "Music", "Run music.ogg")
_MUSIC_BOSS = os.path.join(_DIR, "assets", "audio", "Music", "Epic boss Battle.ogg")
_MUSIC_MENU = os.path.join(_DIR, "assets", "audio", "Music", "Mainmenu Music.ogg")
_BOSS_VOL_MULT = 0.70   # Boss-Musik etwas leiser als Run-Musik


def init_mixer() -> None:
    """Vor pygame.init() aufrufen."""
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)


# ---------------------------------------------------------------------------
# Interne Buffer-Generatoren
# ---------------------------------------------------------------------------

def _sine(freq: float, duration: float, vol: float = 1.0) -> array.array:
    n   = int(SAMPLE_RATE * duration)
    buf = array.array('h')
    for i in range(n):
        t   = i / SAMPLE_RATE
        env = max(0.0, 1.0 - t / duration)
        buf.append(int(max(-32767, min(32767,
                    math.sin(2 * math.pi * freq * t) * env * vol * 32767))))
    return buf


def _sweep(f0: float, f1: float, duration: float, vol: float = 1.0) -> array.array:
    n     = int(SAMPLE_RATE * duration)
    buf   = array.array('h')
    phase = 0.0
    for i in range(n):
        t     = i / SAMPLE_RATE
        phase += 2 * math.pi * (f0 + (f1 - f0) * t / duration) / SAMPLE_RATE
        env   = max(0.0, 1.0 - t / duration)
        buf.append(int(max(-32767, min(32767,
                    math.sin(phase) * env * vol * 32767))))
    return buf


def _concat(*bufs: array.array) -> array.array:
    out = array.array('h')
    for b in bufs:
        out.extend(b)
    return out


def _make(buf: array.array) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(buffer=buf)



# ---------------------------------------------------------------------------
# SoundManager
# ---------------------------------------------------------------------------

class SoundManager:
    def __init__(self):
        self._sfx_vol   = 0.7
        self._music_vol = 0.5
        self._vol_mult  = 1.0   # per-Track-Faktor (Boss = 0.70)

        self.sounds: dict[str, pygame.mixer.Sound] = {
            "shoot":       _make(_sine(880,  0.07, 0.55)),
            "hit":         _make(_sine(660,  0.04, 0.35)),
            "kill":        _make(_sweep(440, 180,  0.18, 0.75)),
            "kill_tanker": _make(_sweep(220,  75,  0.32, 0.90)),
            "wave_clear":  _make(_concat(
                               _sine(523, 0.10, 0.65),   # C5
                               _sine(659, 0.10, 0.65),   # E5
                               _sine(784, 0.22, 0.65),   # G5
                           )),
            "game_over":   _make(_concat(
                               _sine(392, 0.20, 0.65),   # G4
                               _sine(330, 0.20, 0.65),   # E4
                               _sine(294, 0.20, 0.65),   # D4
                               _sine(262, 0.45, 0.65),   # C4
                           )),
            "ui_click":    _make(_sine(1200, 0.03, 0.30)),
            "boss_intro":  _make(_concat(
                               _sweep(150, 350, 0.18, 0.80),
                               _sweep(350, 130, 0.35, 0.95),
                           )),
            "kill_boss":   _make(_concat(
                               _sweep(280,  80, 0.28, 0.90),
                               _sine(  60, 0.20, 0.75),
                           )),
            "kill_superboss": _make(_concat(
                               _sine(523, 0.12, 0.80),
                               _sine(659, 0.12, 0.80),
                               _sine(784, 0.12, 0.80),
                               _sweep(350,  60, 0.50, 1.00),
                           )),
            # Overdrive-Aktivierung (Leertaste, ADR 034): aufsteigender Power-up-Sweep + heller Halteton
            "overdrive":   _make(_concat(
                               _sweep(220, 880, 0.22, 0.85),
                               _sine(880, 0.12, 0.70),
                           )),
        }

        self._apply_sfx()

    # --- Lautstärke ---

    @property
    def sfx_vol(self)   -> float: return self._sfx_vol
    @property
    def music_vol(self) -> float: return self._music_vol

    def set_sfx_vol(self, vol: float) -> None:
        self._sfx_vol = max(0.0, min(1.0, vol))
        self._apply_sfx()

    def set_music_vol(self, vol: float) -> None:
        self._music_vol = max(0.0, min(1.0, vol))
        pygame.mixer.music.set_volume(self._music_vol * self._vol_mult)

    def _apply_sfx(self) -> None:
        for s in self.sounds.values():
            s.set_volume(self._sfx_vol)

    # --- Wiedergabe ---

    def play(self, name: str) -> None:
        if name in self.sounds:
            self.sounds[name].play()

    def _play_music(self, path: str, vol_mult: float = 1.0) -> None:
        if os.path.exists(path):
            self._vol_mult = vol_mult
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_vol * vol_mult)
            pygame.mixer.music.play(-1)

    def start_menu_music(self) -> None:
        self._play_music(_MUSIC_MENU)

    def start_run_music(self) -> None:
        self._play_music(_MUSIC_RUN)

    def start_boss_music(self) -> None:
        self._play_music(_MUSIC_BOSS, _BOSS_VOL_MULT)

    def stop_music(self) -> None:
        pygame.mixer.music.stop()

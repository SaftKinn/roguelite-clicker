import json
import os

_SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "save.json")

_DEFAULT = {
    "total_coins":  0,
    "bought":       [],   # Einmalige Käufe: "doppelschuss", "gold_boost"
    "upgrades":     {"start_damage": 0, "start_hp": 0},  # Stufenzähler
    "best_wave":    0,
    "best_coins":   0,
    "settings":     {"difficulty": 1, "sfx": 7, "music": 5, "fps": 0},
}


def load() -> dict:
    if os.path.exists(_SAVE_PATH):
        try:
            with open(_SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in _DEFAULT.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return {k: (list(v) if isinstance(v, list) else v) for k, v in _DEFAULT.items()}


def save(data: dict) -> None:
    with open(_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

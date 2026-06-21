import json
import os
import copy

_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mehrere Speicherstände (Slots), die VOR dem Hauptmenü gewählt werden. Jeder Slot
# ist eine eigene JSON-Datei `save_slot<N>.json`. Der zuletzt geladene Slot ist der
# „aktive" — `save(data)` schreibt dorthin, damit die vielen bestehenden
# `sd.save(save)`-Aufrufe in main.py unverändert weiterfunktionieren.
SLOTS       = (1, 2, 3)
_LEGACY_PATH = os.path.join(_DIR, "save.json")   # Alt-Einzeldatei (für Migration in Slot 1)
_active_slot = 1

_DEFAULT = {
    "total_coins":  0,
    "bought":       [],   # Einmalige Käufe: "doppelschuss", "gold_boost"
    "upgrades":     {"start_damage": 0, "start_hp": 0},  # Stufenzähler
    "best_wave":    0,
    "best_coins":   0,
    "settings":     {"difficulty": 1, "sfx": 7, "music": 5, "fps": 0, "framerate": 5},
    "seen_enemies": [],   # Lexikon: bisher gesehene Gegner (Klassennamen)
}


def _slot_path(slot: int) -> str:
    return os.path.join(_DIR, f"save_slot{slot}.json")


def _fresh() -> dict:
    return copy.deepcopy(_DEFAULT)


def active_slot() -> int:
    return _active_slot


def set_slot(slot: int) -> None:
    global _active_slot
    _active_slot = slot


def _read(path: str) -> dict | None:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in _DEFAULT.items():
                data.setdefault(k, copy.deepcopy(v) if isinstance(v, (list, dict)) else v)
            return data
        except Exception:
            pass
    return None


def load(slot: int | None = None) -> dict:
    """Lädt einen Slot (setzt ihn aktiv). Migriert einmalig die Alt-`save.json` in Slot 1."""
    global _active_slot
    if slot is not None:
        _active_slot = slot
    path = _slot_path(_active_slot)
    data = _read(path)
    if data is None and _active_slot == 1:
        legacy = _read(_LEGACY_PATH)   # einmalige Migration der Alt-Einzeldatei
        if legacy is not None:
            data = legacy
            save(data, 1)
    return data if data is not None else _fresh()


def save(data: dict, slot: int | None = None) -> None:
    s = _active_slot if slot is None else slot
    with open(_slot_path(s), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete(slot: int) -> None:
    """Löscht einen Slot (Datei entfernen → wieder leer)."""
    path = _slot_path(slot)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def slot_summary(slot: int) -> dict | None:
    """Kurzinfo für die Slot-Auswahl: {best_wave, total_coins} oder None, wenn leer.

    Slot 1 zählt die noch nicht migrierte Alt-`save.json` als belegt mit."""
    data = _read(_slot_path(slot))
    if data is None and slot == 1:
        data = _read(_LEGACY_PATH)
    if data is None:
        return None
    return {"best_wave": data.get("best_wave", 0),
            "total_coins": data.get("total_coins", 0)}

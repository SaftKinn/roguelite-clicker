"""Zentrales Tuning-Datenmodul (ADR 002).

Alle Spielbalance-Werte und Wellen-Formeln leben hier, nicht verstreut im Code.
**Verhalten/Logik bleibt im jeweiligen Modul** — hier stehen nur Zahlen und die
reinen Skalierungsformeln. Wer einen Wert tunen will, ändert ihn an dieser einen
Stelle.

Die JSON-Auslagerung (Tuning aus Datei laden) ist laut ADR 002 für später
vorgesehen — vorerst sind es Python-Konstanten.
"""

# ---------------------------------------------------------------------------
# Spawn & Nahkampf
# ---------------------------------------------------------------------------

BASE_SPAWN_INTERVAL = 90    # Grund-Ticks zwischen zwei Spawns (Schwierigkeit moduliert)
MELEE_REACH         = 6     # kleiner Puffer, damit der anhaltende Gegner sicher in Reichweite ist

ATTACK_DAMAGE       = 10    # Nahkampf-Schaden pro Treffer (Belagerung, ADR 005)
ATTACK_COOLDOWN     = 45    # Ticks zwischen Nahkampf-Treffern (~0.75 s)


# ---------------------------------------------------------------------------
# Wellen-Skalierung
# ---------------------------------------------------------------------------

def enemies_for_wave(wave: int) -> int:
    if wave % 10 == 0:
        return 1
    return 5 + (wave - 1) * 3

def enemy_hp_for_wave(wave, hp_mult) -> int:  return int((30 + wave * 10) * hp_mult)
def enemy_speed_for_wave(wave: int) -> float: return min(1.8 + wave * 0.15, 4.0)
def coin_value_for_wave(wave: int) -> int:    return 1 + wave // 3


# ---------------------------------------------------------------------------
# In-Run-Upgrades (Auswahl nach jeder Welle)
# ---------------------------------------------------------------------------

UPGRADE_DAMAGE       = 10           # "Mehr Schaden": +Schaden pro Kugel
UPGRADE_BULLET_SPEED = 3            # "Schnelle Kugeln": +Kugelgeschwindigkeit
UPGRADE_BULLET_SIZE  = 4            # "Große Kugeln": +Kugelradius
UPGRADE_MAX_HP       = 25           # "Max HP": +Maximale HP (heilt zugleich um denselben Betrag)
MULTISHOT_ANGLES     = (-15, 0, 15) # "Dreifachschuss": Streuwinkel der Kugeln (Anzahl = len)


# ---------------------------------------------------------------------------
# Permanente Verbesserungen (Münz-Shop) — Effekte
# ---------------------------------------------------------------------------

PERMANENT_DAMAGE_PER_LEVEL = 10     # "Startschaden": +Schaden je Stufe
PERMANENT_HP_PER_LEVEL     = 30     # "Start-HP": +Max-HP je Stufe
GOLD_BOOST_MULT            = 1.5    # "Goldene Kugeln": Münz-Faktor aus Kills
DOPPELSCHUSS_DELAY         = 8      # "Doppelschuss": Frames Verzögerung bis zur zweiten Kugel


# ---------------------------------------------------------------------------
# Permanente Verbesserungen (Münz-Shop) — Preise
# ---------------------------------------------------------------------------

COST_MULT          = 1.65   # Preismultiplikator je Stufe (unendlich steigerbare Upgrades)
COST_START_DAMAGE  = 50     # Basispreis "Startschaden"
COST_START_HP      = 75     # Basispreis "Start-HP"
COST_DOPPELSCHUSS  = 120    # Einmalkauf "Doppelschuss"
COST_GOLD_BOOST    = 80     # Einmalkauf "Goldene Kugeln"

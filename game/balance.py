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

# Hinweis: Seit dem ~2h-Rebalance (ADR 007) ist der Spawn-Floor (Gesamt-Gegner ×
# Spawn-Interval) das Rückgrat der Spielzeit. Welle 100 ≈ 2 Stunden bei 1.25x
# Spielgeschwindigkeit (FPS 75, siehe constants.py). Alle Werte hier sind die
# Stellschrauben für das Feintuning nach dem Playtest.

BASE_SPAWN_INTERVAL = 58    # Grund-Ticks zwischen zwei Spawns (knackiger/dichter, ADR 008)
MELEE_REACH         = 6     # kleiner Puffer, damit der anhaltende Gegner sicher in Reichweite ist

ATTACK_DAMAGE       = 22    # Nahkampf-Schaden pro Treffer (deutlich tödlicher, ADR 008)
ATTACK_COOLDOWN     = 45    # Ticks zwischen Nahkampf-Treffern

# Spieler-Feuer: Halten der linken Maustaste feuert automatisch im Angriffstempo (ADR 009).
BASE_ATTACK_SPEED   = 0.60  # Schüsse pro Sekunde (Basis); Feuer-Intervall = FPS / attack_speed
LIFESTEAL_PER_HIT   = 1     # HP, die der Spieler je Treffer an einem Gegner heilt (ADR 009)

# ---------------------------------------------------------------------------
# Render-Feel (ADR 007): Kamera-Zoom + globale Sprite-Größe
# ---------------------------------------------------------------------------

CAMERA_ZOOM  = 1.2    # Welt wird post-render um diesen Faktor zentriert herangezoomt
SPRITE_SCALE = 1.1    # zusätzliche Vergrößerung aller Einheiten-/Geschoss-Sprites beim Laden


# ---------------------------------------------------------------------------
# Sieg & Wellen-Caps (Phase 2, ADR 004/006; Mengen ADR 007)
# ---------------------------------------------------------------------------

WIN_WAVE               = 100   # Lauf endet als Sieg beim Räumen dieser Welle (SuperBoss)
MAX_ENEMIES_PER_WAVE   = 45    # Obergrenze Gesamt-Gegner je Normalwelle (kürzere Wellen, ADR 008)
MAX_CONCURRENT_ENEMIES = 30    # max. gleichzeitig lebende Gegner — deckelt Perf + Belagerungs-DPS


# ---------------------------------------------------------------------------
# Wellen-Skalierung
# ---------------------------------------------------------------------------

def enemies_for_wave(wave: int) -> int:
    if wave % 10 == 0:
        return 1
    # Hybrid: Gesamtzahl steigt linear, plateaut beim Cap (Concurrent-Cap bremst zusätzlich)
    return min(5 + (wave - 1) * 3, MAX_ENEMIES_PER_WAVE)

def enemy_hp_for_wave(wave, hp_mult) -> int:  return int((30 + wave * 14) * hp_mult)  # steileres Scaling (ADR 009)
def enemy_speed_for_wave(wave: int) -> float: return min(2.2 + wave * 0.18, 4.6)  # schneller dran (ADR 008)
def coin_value_for_wave(wave: int) -> int:    return 1 + wave // 3


# ---------------------------------------------------------------------------
# XP & Level-System (ADR 008)
# ---------------------------------------------------------------------------
# Gegner droppen beim Tod XP (= ihr Münzwert `coin_value`). Sobald die Schwelle
# erreicht ist, steigt der Spieler eine Stufe auf und wählt 1 von 3 Karten
# (ersetzt das frühere Karten-Picken pro Welle). Die nötige XP wächst mit Stufe
# UND Welle — späte Wellen verlangen mehr XP pro Levelup.

XP_BASE      = 5    # Grund-XP für den ersten Levelup
XP_PER_LEVEL = 3    # zusätzliche XP je bereits erreichter Stufe
XP_PER_WAVE  = 2    # zusätzliche XP je Welle (macht spätere Levelups teurer)

def xp_to_next(level: int, wave: int) -> int:
    """Nötige XP für den nächsten Levelup, abhängig von Stufe und Welle."""
    return round(XP_BASE + (level - 1) * XP_PER_LEVEL + wave * XP_PER_WAVE)


# ---------------------------------------------------------------------------
# In-Run-Upgrades (Auswahl nach jeder Welle)
# ---------------------------------------------------------------------------

UPGRADE_DAMAGE       = 15           # "Mehr Schaden": +Schaden pro Kugel
UPGRADE_BULLET_SPEED = 4            # "Schnelle Kugeln": +Kugelgeschwindigkeit
UPGRADE_BULLET_SIZE  = 6            # "Große Kugeln": +Kugelradius
UPGRADE_MAX_HP       = 40           # "Max HP": +Maximale HP (heilt zugleich um denselben Betrag)
UPGRADE_ATTACK_SPEED = 0.10         # "Angriffstempo": +10% Feuerrate je Karte (multiplikativ, ADR 009)
MULTISHOT_ANGLES     = (-15, 0, 15) # "Dreifachschuss": Streuwinkel der Kugeln (Anzahl = len)


# ---------------------------------------------------------------------------
# Permanente Verbesserungen (Münz-Shop) — Effekte
# ---------------------------------------------------------------------------

PERMANENT_DAMAGE_PER_LEVEL = 15     # "Startschaden": +Schaden je Stufe
PERMANENT_HP_PER_LEVEL     = 40     # "Start-HP": +Max-HP je Stufe
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

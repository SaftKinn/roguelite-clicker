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

BASE_SPAWN_INTERVAL = 60    # Grund-Ticks zwischen zwei Spawns (länger gestreckt; bei FPS 75 = 0.8 s)
MELEE_REACH         = 6     # kleiner Puffer, damit der anhaltende Gegner sicher in Reichweite ist

ATTACK_DAMAGE       = 22    # Nahkampf-Schaden pro Treffer (deutlich tödlicher, ADR 008)
ATTACK_COOLDOWN     = 45    # Ticks zwischen Nahkampf-Treffern

# Spieler-Feuer: Halten der linken Maustaste feuert automatisch im Angriffstempo (ADR 009).
BASE_ATTACK_SPEED   = 1.5   # Schüsse pro Sekunde (Basis); Feuer-Intervall = FPS / attack_speed
LIFESTEAL_PER_HIT   = 1     # HP, die der Spieler je Treffer an einem Gegner heilt (ADR 009)

# ---------------------------------------------------------------------------
# Render-Feel (ADR 007): Kamera-Zoom + globale Sprite-Größe
# ---------------------------------------------------------------------------

CAMERA_ZOOM  = 1.2    # Welt wird post-render um diesen Faktor zentriert herangezoomt
SPRITE_SCALE = 1.1    # zusätzliche Vergrößerung aller Einheiten-/Geschoss-Sprites beim Laden
ENEMY_SPRITE_SCALE = 1.25  # Gegner-Körper zusätzlich vergrößert (etwas größer als der Turm); Turm bleibt _TOWER_SIZE


# ---------------------------------------------------------------------------
# Sieg & Wellen-Caps (Phase 2, ADR 004/006; Mengen ADR 007)
# ---------------------------------------------------------------------------

WIN_WAVE               = 100   # Lauf endet als Sieg beim Räumen dieser Welle (SuperBoss)
MAX_ENEMIES_PER_WAVE   = 30    # Obergrenze Gesamt-Gegner je Normalwelle (weniger Gegner, Playtest)
MAX_CONCURRENT_ENEMIES = 30    # max. gleichzeitig lebende Gegner — deckelt Perf + Belagerungs-DPS

# Elite-Gegner: jeder Nicht-Boss-Typ kann als Elite spawnen (zäher Brocken, egal welcher Typ).
ELITE_SPAWN_CHANCE = 0.10          # Wahrscheinlichkeit je Nicht-Boss-Spawn, ein Elite zu sein
ELITE_HP_MULT      = 10            # Elite-HP = normale Gegner-HP × diesem Faktor
ELITE_REWARD_MULT  = 5             # Elite gibt Münzen UND XP × diesem Faktor (lohnendes Ziel)
ELITE_COLOR        = (255, 60, 60) # Ring-Markierung um Elites (damit sie erkennbar sind)

# Boss-HP-Multiplikatoren auf die (super-lineare) Wellen-Basis-HP. Bewusst niedrig:
# Bosse one-shotten bei Kontakt und der Turm ist stationär → der Kampf ist ein reines
# DPS-Rennen gegen die Anlauf-Zeit des Bosses (~5 s Boss / ~8 s SuperBoss bei FPS 75).
# Seit dem quadratischen HP-Term (ADR 012) liefert die Basis-HP schon den Großteil der
# Endgame-Wand; hohe Multiplikatoren oben drauf machten Bosse ab ~W40 unfair (ADR 013,
# Modell: tools/balance_model.py).
BOSS_HP_MULT      = 2   # normaler Boss (alle 10 Wellen)
SUPERBOSS_HP_MULT = 3   # SuperBoss (Welle 50 & 100)


# ---------------------------------------------------------------------------
# Wellen-Skalierung
# ---------------------------------------------------------------------------

def enemies_for_wave(wave: int) -> int:
    if wave % 10 == 0:
        return 1
    # Hybrid: Gesamtzahl steigt linear, plateaut beim Cap (Concurrent-Cap bremst zusätzlich)
    return min(5 + (wave - 1) * 3, MAX_ENEMIES_PER_WAVE)

# Gegner-HP wächst SUPER-LINEAR (linear + quadratisch), damit es mit der multiplikativen
# Spielerkraft (Schaden × Angriffstempo × Multishot × Durchschlag) mithalten kann — eine
# rein lineare Kurve lässt der Spieler über lange Läufe zwangsläufig hinter sich.
ENEMY_HP_BASE        = 30    # Grund-HP (Welle 0)
ENEMY_HP_PER_WAVE    = 12    # linearer HP-Zuwachs je Welle
ENEMY_HP_PER_WAVE_SQ = 0.9   # quadratischer HP-Zuwachs (greift v.a. spät → echte Endgame-Wand)

def enemy_hp_for_wave(wave, hp_mult) -> int:
    return int((ENEMY_HP_BASE + wave * ENEMY_HP_PER_WAVE
                + wave * wave * ENEMY_HP_PER_WAVE_SQ) * hp_mult)
def enemy_speed_for_wave(wave: int) -> float: return min(2.2 + wave * 0.18, 4.6)  # schneller dran (ADR 008)
def coin_value_for_wave(wave: int) -> int:    return 1 + wave // 3


# ---------------------------------------------------------------------------
# XP & Level-System (ADR 008)
# ---------------------------------------------------------------------------
# Gegner droppen beim Tod XP (= ihr Münzwert `coin_value`). Sobald die Schwelle
# erreicht ist, steigt der Spieler eine Stufe auf und wählt 1 von 3 Karten
# (ersetzt das frühere Karten-Picken pro Welle). Die nötige XP wächst mit Stufe
# UND Welle — späte Wellen verlangen mehr XP pro Levelup.

XP_BASE      = 8    # Grund-XP für den ersten Levelup
XP_PER_LEVEL = 7    # zusätzliche XP je bereits erreichter Stufe (steiler: bremst schnelles Hochleveln)
XP_PER_WAVE  = 2    # zusätzliche XP je Welle (macht spätere Levelups teurer)

def xp_to_next(level: int, wave: int) -> int:
    """Nötige XP für den nächsten Levelup, abhängig von Stufe und Welle."""
    return round(XP_BASE + (level - 1) * XP_PER_LEVEL + wave * XP_PER_WAVE)

# XP pro Kill skaliert mit der Welle (ADR 014, Wurzel-Fix gegen die Endgame-Wand):
# Vorher gab ein Kill nur die flache Klassen-Basis `enemy.coin_value` (1/3, ×5 Elite) —
# unabhängig von der Welle, während die Gegner-HP super-linear wächst. Folge: Der Spieler
# blieb auf Welle 100 bei ~Level 33 und hatte zu wenig DPS für die späten Bosse. Mit diesem
# Multiplikator (gedämpft ggü. dem ×-Münzfaktor `coin_value_for_wave` = wave//3) levelt der
# Spieler spät weiter (Modell: ~Level 98 auf W100, alle Bosse im Walk-Budget).
XP_WAVE_DIV = 8     # XP-Wellenfaktor = 1 + wave // XP_WAVE_DIV (kleiner = stärker)

def xp_wave_mult(wave: int) -> int:
    """Wellenabhängiger Multiplikator auf den XP-Drop je Kill."""
    return 1 + wave // XP_WAVE_DIV

# Beim Levelup ist die Karten-Auswahl kurz klick-gesperrt, damit ein gehaltener/
# schneller Klick nicht versehentlich sofort eine Karte wählt (ADR 009).
LEVELUP_INPUT_LOCK_S = 0.75   # Sekunden Klick-Sperre nach Erscheinen des Karten-Screens


# ---------------------------------------------------------------------------
# In-Run-Upgrades (Auswahl nach jeder Welle)
# ---------------------------------------------------------------------------

UPGRADE_DAMAGE       = 15           # "Mehr Schaden": +Schaden pro Kugel
UPGRADE_BULLET_SPEED = 4            # "Schnelle Kugeln": +Kugelgeschwindigkeit
UPGRADE_BULLET_SIZE  = 6            # "Große Kugeln": +Kugelradius
UPGRADE_MAX_HP       = 40           # "Max HP": +Maximale HP (heilt zugleich um denselben Betrag)
UPGRADE_ATTACK_SPEED = 0.2          # "Angriffstempo": +0.2 Schüsse/Sek. je Karte (additiv, ADR 009)
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

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

# Hinweis: Das Spawn-Tempo ist seit ADR 023 NICHT mehr das Rückgrat der Spielzeit —
# eine Welle spawnt ihre Gegner immer über ein festes Wandzeit-Fenster (WAVE_SPAWN_SECONDS,
# FPS-unabhängig, siehe spawn_interval_ticks). Die Lauflänge ergibt sich jetzt aus
# Gegner-HP-Kurve × Spielerkraft (wie schnell geräumt wird), nicht aus gestreckten Spawns.
# Alle Werte hier sind die Stellschrauben für das Feintuning nach dem Playtest.

BASE_SPAWN_INTERVAL = 60    # (Alt) feste Ticks zwischen Spawns — ersetzt durch das 10-s-Spawnfenster unten
WAVE_SPAWN_SECONDS  = 10.0  # nach so vielen Sekunden ist die KOMPLETTE Welle gespawnt (Nutzerwunsch)
MELEE_REACH         = 6     # kleiner Puffer, damit der anhaltende Gegner sicher in Reichweite ist

ATTACK_DAMAGE       = 22    # Nahkampf-Schaden pro Treffer (deutlich tödlicher, ADR 008)
ATTACK_COOLDOWN     = 45    # Ticks zwischen Nahkampf-Treffern

# Spieler-Feuer: Halten der linken Maustaste feuert automatisch im Angriffstempo (ADR 009).
BASE_DAMAGE         = 15    # Schaden je Kugel zu Lauf-Beginn (+50% ggü. alt 10, Nutzerwunsch)
BASE_ATTACK_SPEED   = 1.5   # Schüsse pro Sekunde (Basis); Feuer-Intervall = FPS / attack_speed
LIFESTEAL_PER_HIT   = 1     # HP, die der Spieler je Treffer an einem Gegner heilt (ADR 009)

# ---------------------------------------------------------------------------
# Render-Feel (ADR 007): Kamera-Zoom + globale Sprite-Größe
# ---------------------------------------------------------------------------

CAMERA_ZOOM  = 1.4    # Welt wird post-render um diesen Faktor zentriert herangezoomt (größer = alles näher/größer)
# Spieler-Angriffsreichweite als Anteil der sichtbaren Halb-Höhe (= kleinster sichtbarer Radius
# bei CAMERA_ZOOM). Der Turm feuert nur auf Gegner innerhalb dieser Reichweite, damit Kills
# IMMER im sichtbaren Bild passieren (der Zoom schneidet den Rand ab). <1 = etwas Sicherheitsrand.
ATTACK_RANGE_FRAC = 0.92
SPRITE_SCALE = 1.1    # zusätzliche Vergrößerung aller Einheiten-/Geschoss-Sprites beim Laden
ENEMY_SPRITE_SCALE = 1.25  # Gegner-Körper zusätzlich vergrößert (etwas größer als der Turm); Turm bleibt _TOWER_SIZE


# ---------------------------------------------------------------------------
# Sieg & Wellen-Caps (Phase 2, ADR 004/006; Mengen ADR 007)
# ---------------------------------------------------------------------------

WIN_WAVE               = 150   # Lauf endet als Sieg beim Räumen dieser Welle (SuperBoss; 3 Tiers à 50)
MAX_ENEMIES_PER_WAVE   = 30    # Obergrenze Gesamt-Gegner je Normalwelle (weniger Gegner, Playtest)
MAX_CONCURRENT_ENEMIES = 30    # max. gleichzeitig lebende Gegner — deckelt Perf + Belagerungs-DPS

# Elite-Gegner: jeder Nicht-Boss-Typ kann als Elite spawnen (zäher Brocken, egal welcher Typ).
ELITE_SPAWN_CHANCE = 0.10          # Wahrscheinlichkeit je Nicht-Boss-Spawn, ein Elite zu sein
ELITE_HP_MULT      = 3             # Elite-HP = normale Gegner-HP × diesem Faktor (Basis)
ELITE_REWARD_MULT  = 5             # Elite gibt Münzen UND XP × diesem Faktor (lohnendes Ziel)
ELITE_COLOR        = (255, 60, 60) # Ring-Markierung um Elites (damit sie erkennbar sind)

# Elite-HP steigt zusätzlich gestuft: alle ELITE_HP_TIER_STEP Wellen +ELITE_HP_TIER_PCT
# (ADDITIV auf die Basis ×ELITE_HP_MULT, Nutzerwunsch). Bewusst additiv statt kompoundierend
# — +100% kompoundierend wäre auf der wave_tier-Basis unspielbar. W10 ×6, W50 ×18, W100 ×33.
ELITE_HP_TIER_STEP = 10            # alle so vielen Wellen ein Elite-HP-Schritt
ELITE_HP_TIER_PCT  = 1.0           # +100% (der Basis) je Schritt

def elite_hp_mult(wave: int) -> float:
    """Effektiver Elite-HP-Faktor inkl. Wellen-Stufen (additiv auf ELITE_HP_MULT)."""
    return ELITE_HP_MULT * (1 + ELITE_HP_TIER_PCT * (wave // ELITE_HP_TIER_STEP))

# Boss-HP-Multiplikatoren auf die (super-lineare) Wellen-Basis-HP. Bewusst niedrig:
# Bosse one-shotten bei Kontakt und der Turm ist stationär → der Kampf ist ein reines
# DPS-Rennen gegen die Anlauf-Zeit des Bosses (~5 s Boss / ~8 s SuperBoss bei FPS 75).
# Seit dem quadratischen HP-Term (ADR 012) liefert die Basis-HP schon den Großteil der
# Endgame-Wand; hohe Multiplikatoren oben drauf machten Bosse ab ~W40 unfair (ADR 013,
# Modell: tools/balance_model.py).
BOSS_HP_MULT      = 60  # normaler Boss (alle 10 Wellen) — ×5 (Nutzerwunsch; war 12)
SUPERBOSS_HP_MULT = 100  # SuperBoss (Welle 50/100/150) — ×5 (Nutzerwunsch; war 20)


# ---------------------------------------------------------------------------
# Wellen-Skalierung
# ---------------------------------------------------------------------------

def enemies_for_wave(wave: int) -> int:
    if wave % 10 == 0:
        return 1
    # Hybrid: Gesamtzahl steigt linear, plateaut beim Cap (Concurrent-Cap bremst zusätzlich)
    return min(5 + (wave - 1) * 3, MAX_ENEMIES_PER_WAVE)

def spawn_interval_ticks(wave: int, fps: int) -> int:
    """Ticks zwischen zwei Spawns, so dass ALLE Gegner der Welle in WAVE_SPAWN_SECONDS
    gespawnt sind. Da der spawn_timer bei 0 startet, erscheint der letzte der N Gegner bei
    N×Intervall → Intervall = WAVE_SPAWN_SECONDS×fps / N legt ihn genau auf das Fenster-Ende.
    An die Live-FPS gekoppelt (FPS-Regler), damit es echte Sekunden bleiben.
    Bosswelle (N=1): sofort spawnen statt 10 s leeres Feld. Hinweis: der Concurrent-Cap
    (MAX_CONCURRENT_ENEMIES) kann das Fenster dehnen, wenn der Spieler nicht schnell genug räumt."""
    n = enemies_for_wave(wave)
    if n <= 1:
        return 1
    return max(1, round(WAVE_SPAWN_SECONDS * fps / n))

# Gegner-HP wächst SUPER-LINEAR (linear + quadratisch), damit es mit der multiplikativen
# Spielerkraft (Schaden × Angriffstempo × Multishot × Durchschlag) mithalten kann — eine
# rein lineare Kurve lässt der Spieler über lange Läufe zwangsläufig hinter sich.
ENEMY_HP_BASE        = 30    # Grund-HP (Welle 0)
ENEMY_HP_PER_WAVE    = 12    # linearer HP-Zuwachs je Welle
ENEMY_HP_PER_WAVE_SQ = 0.9   # quadratischer HP-Zuwachs (greift v.a. spät → echte Endgame-Wand)
ENEMY_HP_GLOBAL_MULT = 0.25  # globaler HP-Faktor ALLER Gegner (stark gesenkt, Gegner waren viel zu stark — Nutzerwunsch)

# Meilenstein-Härtung (Nutzerwunsch): zusätzlich zur wellenweisen Skalierung werden
# Gegner alle WAVE_TIER_STEP Wellen um WAVE_TIER_MULT−1 stärker — und zwar KOMPOUNDIEREND
# (Welle 10 ×1.4, Welle 20 ×1.96, … Welle 100 ×1.4^10 ≈ ×28.9). Gilt für HP UND Schaden.
# Tuning: kleiner = sanfter. Für additiv statt kompoundierend: `1 + (WAVE_TIER_MULT-1)*(wave//WAVE_TIER_STEP)`.
WAVE_TIER_STEP = 10    # alle so vielen Wellen kommt ein Härte-Schritt dazu
WAVE_TIER_MULT = 1.0   # Faktor je Schritt — 1.0 = AUS (harte Wellen-Härte zurückgesetzt, Nutzerwunsch)

def wave_tier_mult(wave: int) -> float:
    """Kompoundierender Härte-Faktor auf HP und Schaden, je WAVE_TIER_STEP Wellen ×WAVE_TIER_MULT."""
    return WAVE_TIER_MULT ** (wave // WAVE_TIER_STEP)

def enemy_hp_for_wave(wave, hp_mult) -> int:
    return int((ENEMY_HP_BASE + wave * ENEMY_HP_PER_WAVE
                + wave * wave * ENEMY_HP_PER_WAVE_SQ)
               * hp_mult * ENEMY_HP_GLOBAL_MULT * wave_tier_mult(wave))
def enemy_speed_for_wave(wave: int) -> float: return min(1.1 + wave * 0.10, 2.4)  # noch langsamer (Nutzerwunsch, 2. Runde)
def coin_value_for_wave(wave: int) -> int:    return 1 + wave // 3
COIN_GAIN_MULT = 1.5   # globaler Münz-Faktor je Kill (+50%, Nutzerwunsch)


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
XP_GAIN_MULT = 1.7  # globaler XP-Faktor je Kill (+70%, Nutzerwunsch: Spieler levelt zu langsam)

def xp_wave_mult(wave: int) -> int:
    """Wellenabhängiger Multiplikator auf den XP-Drop je Kill."""
    return 1 + wave // XP_WAVE_DIV

# "Jede Runde 10% mehr XP" (Nutzerwunsch): zusätzlicher, linear je Welle wachsender
# XP-Faktor (+10% der Basis pro Welle → Welle 100 = ×11). Bewusst linear, nicht
# kompoundierend (1.1^Welle würde explodieren). Kleiner = sanfter.
XP_ROUND_PCT = 0.10

def xp_round_mult(wave: int) -> float:
    """+XP_ROUND_PCT je Welle (linear) auf den XP-Drop — 'jede Runde mehr XP'."""
    return 1 + XP_ROUND_PCT * wave

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

# --- ROT (Schaden): Lifesteal-Karten (stapelbar, gedeckelt auf max_hp, ADR 025) ---
UPGRADE_LIFESTEAL_PCT  = 0.05   # "Lebensraub": +5% des ausgeteilten Schadens als HP/Treffer je Stufe
UPGRADE_LIFESTEAL_FLAT = 2      # "Vampirschlag": +2 HP/Treffer je Stufe (flach)

# --- BLAU (Verteidigung, ADR 025) ---
UPGRADE_ARMOR_PCT = 0.06   # "Rüstung": eingehender Schaden -6% je Stufe (additiv)
ARMOR_CAP         = 0.75   # max. 75% Schadensreduktion (Deckel, sonst Unsterblichkeit)
UPGRADE_HP_REGEN  = 2.0    # "Regeneration": +2 HP/Sekunde je Stufe
UPGRADE_THORNS_PCT = 0.20  # "Dornen": Nahkämpfer nehmen 20% des erlittenen (Vor-Armor-)Schadens je Stufe
THORNS_CAP        = 1.0    # max. 100% Reflect
UPGRADE_DODGE_PCT = 0.05   # "Ausweichen": +5% Chance, einen Treffer komplett zu vermeiden je Stufe
DODGE_CAP         = 0.50   # max. 50% Ausweichchance

# --- GOLD (Geld, gilt für diesen Lauf, stapelbar, ADR 025) ---
UPGRADE_COIN_PCT = 0.15    # "Goldgier"/"Schatzfund": +15% Münzen aus Kills je Stufe

# --- WEISS (XP, gilt für diesen Lauf, stapelbar, ADR 025) ---
UPGRADE_XP_PCT         = 0.15  # "Gelehrsamkeit": +15% XP-Gewinn je Stufe
UPGRADE_REROLL_CHARGES = 1     # "Neuwurf": +1 Reroll-Charge im Levelup-Screen je Karte

# --- Farbgruppen der Karten/Shop-Käufe (ADR 025) — eine Quelle für Karten + Shop ---
GROUP_RED, GROUP_BLUE, GROUP_GOLD, GROUP_WHITE = "red", "blue", "gold", "white"
GROUP_COLORS = {GROUP_RED:   (200,  60,  60),   # Schaden
                GROUP_BLUE:  ( 60, 140, 220),   # Verteidigung
                GROUP_GOLD:  (240, 190,  40),   # Geld
                GROUP_WHITE: (225, 225, 235)}   # XP
GROUP_TITLES = {GROUP_RED: "Schaden", GROUP_BLUE: "Verteidigung",
                GROUP_GOLD: "Geld",   GROUP_WHITE: "XP"}


# ---------------------------------------------------------------------------
# Permanente Verbesserungen (Münz-Shop) — Effekte
# ---------------------------------------------------------------------------

PERMANENT_DAMAGE_PER_LEVEL = 25     # "Startschaden": +Schaden je Stufe (stärker, treibt den 5-Läufe-Aufstieg, ADR 018)
PERMANENT_HP_PER_LEVEL     = 40     # "Start-HP": +Max-HP je Stufe
GOLD_BOOST_MULT            = 1.5    # "Goldene Kugeln": Münz-Faktor aus Kills
DOPPELSCHUSS_DELAY         = 8      # "Doppelschuss": Frames Verzögerung bis zur zweiten Kugel

# Shop-Ausbau (ADR 026) — weitere Dauer-Stats + globale Meta-Multiplikatoren
PERMANENT_ATTACK_SPEED_PER_LEVEL = 0.08  # "Start-Angriffstempo": +0.08 Schuss/s je Stufe
PERMANENT_BULLET_SIZE_PER_LEVEL  = 3     # "Start-Kugelgröße": +3 Kugelradius je Stufe
PERMANENT_LIFESTEAL_PER_LEVEL    = 1     # "Start-Lebensraub": +1 flach HP/Treffer je Stufe
PERMANENT_COIN_MULT_PER_LEVEL    = 0.05  # "Münz-Meister": +5% Münzen ÜBER ALLE Läufe je Stufe
PERMANENT_XP_MULT_PER_LEVEL      = 0.05  # "Weisheit": +5% XP ÜBER ALLE Läufe je Stufe
PERMANENT_FREE_REROLLS_PER_LEVEL = 1     # "Glückshand": +1 Gratis-Reroll pro Lauf je Stufe
DEFAULT_CARD_COUNT = 3   # Karten pro Levelup (Standard)
EXTRA_CARD_COUNT   = 4   # Karten pro Levelup, wenn "extra_card" gekauft


# ---------------------------------------------------------------------------
# Permanente Verbesserungen (Münz-Shop) — Preise
# ---------------------------------------------------------------------------

COST_MULT          = 1.4    # Preismultiplikator je Stufe (flacher, damit Startschaden über ~5 Läufe stackbar bleibt, ADR 018)
COST_START_DAMAGE  = 50     # Basispreis "Startschaden"
COST_START_HP      = 75     # Basispreis "Start-HP"
COST_DOPPELSCHUSS  = 5000   # Stufe 1 "Doppelschuss" (+1 Schuss)
COST_DREIFACHSCHUSS = 20000 # Stufe 2 "Dreifachschuss" (+2 Schuss) — Ausbau des Doppelschuss
COST_GOLD_BOOST    = 80     # Einmalkauf "Goldene Kugeln"

# Shop-Ausbau (ADR 026) — Basispreise der neuen Käufe (∞ skalieren mit COST_MULT)
COST_START_ATTACK_SPEED = 120    # Basispreis "Start-Angriffstempo" (∞)
COST_START_BULLET_SIZE  = 90     # Basispreis "Start-Kugelgröße" (∞)
COST_START_LIFESTEAL    = 150    # Basispreis "Start-Lebensraub" (∞)
COST_COIN_MULT          = 200    # Basispreis "Münz-Meister" (∞, global über alle Läufe)
COST_XP_MULT            = 200    # Basispreis "Weisheit" (∞, global über alle Läufe)
COST_FREE_REROLLS       = 300    # Basispreis "Glückshand" (∞)
COST_EXTRA_CARD         = 1200   # Einmalkauf "Vierte Karte"

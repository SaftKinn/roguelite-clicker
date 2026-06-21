"""Read-only Balance-Modell (Analyse-Tool, KEIN Laufzeit-Modul, KEIN Spiel-Code).

Beantwortet die offene Playtest-Frage aus progress.md mit Zahlen statt Bauchgefühl:
Hält die Spieler-DPS über einen 1->100-Lauf mit der super-linearen Gegner-HP mit
(ADR 012), und ist der SuperBoss (W100) in fairer Zeit zu legen?

Modelliert wird die *Run-interne* Progression exakt nach Code:
  - XP pro Kill  = enemy.coin_value (Klassen-Basis 1/3/10/50, x5 als Elite) — NICHT
    wellenabhaengig (main.py:644). coin_value_for_wave fuettert nur Muenzen.
  - Levelup-Kosten = balance.xp_to_next(level, wave) (steigt mit Stufe UND Welle).
  - Karten: pro Levelup 3 zufaellige aus 7; greedy gepickt nach Spieler-Policy.
  - Einzelziel-DPS (Boss) = damage_pro_Kugel * attack_speed. Multishot (3 Kugeln
    +-15 Grad) und Durchschlag treffen ein Einzelziel NICHT zusaetzlich -> gegen
    den SuperBoss zaehlen nur die Karten `damage` und `attackspeed`.

Aufruf:  python tools/balance_model.py
Annahmen stehen oben im Output; Regler unten in SCENARIOS.
"""

import os
import sys
import math
import random

# game/balance.py importierbar machen, egal von wo aufgerufen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import balance as B

# Bildschirm/Turm (constants.py) — fuer das Boss-Walk-Budget
_SW, _SH, _FPS = 1280, 720, 75
_CX, _CY = _SW / 2, _SH / 2


def _avg_edge_distance() -> float:
    """Erwartete Lauf-Distanz vom zufaelligen Bildschirmrand zur Mitte (Turm)."""
    total, n = 0.0, 0
    for x in range(0, _SW + 1, 8):            # top + bottom
        total += math.hypot(x - _CX, 0 - _CY); n += 1
        total += math.hypot(x - _CX, _SH - _CY); n += 1
    for y in range(0, _SH + 1, 8):            # left + right
        total += math.hypot(0 - _CX, y - _CY); n += 1
        total += math.hypot(_SW - _CX, y - _CY); n += 1
    return total / n


_AVG_DIST = _avg_edge_distance()


def _boss_walk_budget_s(wave: int) -> float:
    """Sekunden, bis ein Boss dieser Welle die Mitte erreicht (= One-Shot-Kontakt)."""
    base_speed = B.enemy_speed_for_wave(wave)
    mult = 0.2 if wave % 50 == 0 else 0.35    # SuperBoss vs Boss (enemy.py)
    px_per_frame = max(0.25 if wave % 50 == 0 else 0.4, base_speed * mult)
    return _AVG_DIST / (px_per_frame * _FPS)


# --- Gegner-Zusammensetzung je Welle (gespiegelt aus main.spawn_enemy_for_wave) ---
# Nur fuer den XP-Ertrag relevant ist coin_value (Klassen-Basis): basic/rusher=1,
# tanker(Lancer)/monk=3. Gewichte nach Wellen-Bracket.
def _avg_xp_per_nonboss_kill(wave: int) -> float:
    if wave < 3:
        kinds = {1: 1.0}                                  # nur basic
    elif wave < 5:
        kinds = {1: 0.70 + 0.30}                          # basic+rusher, beide cv=1
    elif wave < 7:
        kinds = {1: 0.80, 3: 0.20}                        # +tanker(cv3)
    else:
        kinds = {1: 0.68, 3: 0.32}                        # +monk(cv3): tanker20+monk12
    base = sum(cv * w for cv, w in kinds.items())
    # Elite: ELITE_SPAWN_CHANCE -> coin_value x ELITE_REWARD_MULT
    elite_factor = (1 - B.ELITE_SPAWN_CHANCE) + B.ELITE_SPAWN_CHANCE * B.ELITE_REWARD_MULT
    return base * elite_factor


def _xp_income_for_wave(wave: int, xp_wave_scale: bool = False,
                        xp_wave_div: int = 3) -> float:
    # Lever B: XP skaliert mit der Welle (gedaempft), statt nur die flache Klassen-
    # Basis zu geben -> Spieler levelt spaet weiter. div=3 entspricht coin_value_for_wave
    # (zu stark); groessere div = sanfter.
    wmult = (1 + wave // xp_wave_div) if xp_wave_scale else 1.0
    gain = getattr(B, "XP_GAIN_MULT", 1.0)   # globaler XP-Faktor (+70%, falls gesetzt)
    if wave % 50 == 0:
        return 50.0 * wmult * gain    # SuperBoss coin_value
    if wave % 10 == 0:
        return 10.0 * wmult * gain    # Boss coin_value
    n = B.enemies_for_wave(wave)
    return n * _avg_xp_per_nonboss_kill(wave) * wmult * gain


def _hp_for_wave(wave: int, sq: float) -> int:
    # wie B.enemy_hp_for_wave, aber mit override-barem quadratischem Term (Lever A)
    g = getattr(B, "ENEMY_HP_GLOBAL_MULT", 1.0)   # globaler HP-Faktor (−20%, falls gesetzt)
    return int((B.ENEMY_HP_BASE + wave * B.ENEMY_HP_PER_WAVE + wave * wave * sq) * g)


# --- Karten-Policy: was ein realistischer Spieler aus 3 Angeboten waehlt ---
# Prioritaet: einmalig Multishot+Durchschlag (Clear-Power), danach DPS (damage >
# attackspeed). size/speed/max_hp sind Fueller.
_PRIORITY = ["multishot", "pierce", "damage", "attackspeed", "size", "speed", "max_hp"]
_ALL_CARDS = ["damage", "attackspeed", "speed", "size", "multishot", "pierce", "max_hp"]


def _pick(offered, owned):
    pool = [c for c in offered if not (c in ("multishot", "pierce") and c in owned)]
    if not pool:
        pool = offered
    for c in _PRIORITY:
        if c in pool:
            return c
    return pool[0]


def simulate(start_damage_levels=0, seed=42, bullets_on_boss=1.0,
             boss_mult=None, super_mult=None, xp_wave_scale=True, sq=None,
             xp_wave_div=None):
    if boss_mult is None:
        boss_mult = B.BOSS_HP_MULT
    if super_mult is None:
        super_mult = B.SUPERBOSS_HP_MULT
    if sq is None:
        sq = B.ENEMY_HP_PER_WAVE_SQ
    if xp_wave_div is None:
        xp_wave_div = B.XP_WAVE_DIV       # Default = Live-Stand aus balance.py
    """Ein 1->100-Lauf. Gibt pro Boss-Welle eine Zeile + Endbild zurueck."""
    rng = random.Random(seed)
    # Run-Start-Stats (fresh_game_state) + permanente Shop-Boni (apply_permanent_bonuses)
    damage = B.BASE_DAMAGE + start_damage_levels * B.PERMANENT_DAMAGE_PER_LEVEL
    attack_speed = B.BASE_ATTACK_SPEED
    multishot = pierce = False
    owned = set()

    level = 1
    xp = 0.0
    xp_to_next = B.xp_to_next(level, 1)
    levelups = 0

    rows = []
    for wave in range(1, B.WIN_WAVE + 1):
        xp += _xp_income_for_wave(wave, xp_wave_scale, xp_wave_div)
        while xp >= xp_to_next:
            xp -= xp_to_next
            level += 1
            levelups += 1
            offered = rng.sample(_ALL_CARDS, 3)
            choice = _pick(offered, owned)
            owned.add(choice)
            if choice == "damage":        damage += B.UPGRADE_DAMAGE
            elif choice == "attackspeed": attack_speed += B.UPGRADE_ATTACK_SPEED
            elif choice == "multishot":   multishot = True
            elif choice == "pierce":      pierce = True
            xp_to_next = B.xp_to_next(level, wave)

        # Einzelziel-DPS gegen Boss (Multishot/Durchschlag helfen hier nicht)
        boss_dps = damage * attack_speed * bullets_on_boss

        if wave % 10 == 0:                      # Boss- oder SuperBoss-Welle
            base_hp = _hp_for_wave(wave, sq)
            mult = super_mult if wave % 50 == 0 else boss_mult
            boss_hp = int(base_hp * mult)
            ttk = boss_hp / boss_dps if boss_dps else float("inf")
            budget = _boss_walk_budget_s(wave)
            # Multiplikator, der TTK == Budget ergibt (boss_hp = base_hp*mult, TTK=hp/dps):
            fair_mult = boss_dps * budget / base_hp if base_hp else 0
            rows.append((wave, round(boss_dps), boss_hp, ttk, budget,
                         fair_mult, "SUPER" if wave % 50 == 0 else "Boss"))
    return rows, levelups, level


def _print_scenario(name, **kw):
    rows, levelups, final_level = simulate(**kw)
    print(f"\n=== {name} ===")
    print(f"  Gesamt-Levelups ueber den Lauf: {levelups}  ->  Endstufe ~Level {final_level}")
    print(f"  Lauf-Distanz Rand->Mitte ~{_AVG_DIST:.0f}px")
    print(f"  {'Welle':>5} {'DPS':>6} {'BossHP':>9} {'TTK(s)':>8} {'Budget':>7} "
          f"{'fairMult':>9}  Typ")
    for wave, dps, hp, ttk, budget, fair_mult, typ in rows:
        flag = "  <-- WAND" if ttk > budget else ""
        print(f"  {wave:>5} {dps:>6} {hp:>9} {ttk:>8.1f} {budget:>6.1f}s "
              f"{fair_mult:>9.1f}  {typ}{flag}")
    print("  (fairMult = Boss-HP-Multiplikator, bei dem TTK == Walk-Budget; aktuell"
          " Boss x8 / SuperBoss x25)")


if __name__ == "__main__":
    print("BALANCE-MODELL (read-only) — Spieler-DPS vs Gegner-HP ueber einen 1->100-Lauf")
    print("Annahmen: Einzelziel-DPS = damage * attack_speed (Multishot/Durchschlag zaehlen")
    print("nicht gegen Einzel-Boss). XP/Kill = Klassen-Basis (1/3, x5 Elite) x Wellenfaktor")
    print(f"(1+wave//{B.XP_WAVE_DIV}, ADR 014). 'WAND' = Boss-TTK ueber dem Walk-Budget.")
    print(f"  ENEMY_HP_PER_WAVE_SQ={B.ENEMY_HP_PER_WAVE_SQ}  ELITE_REWARD_MULT={B.ELITE_REWARD_MULT}"
          f"  XP_WAVE_DIV={B.XP_WAVE_DIV}  XP_BASE={B.XP_BASE}/PER_LEVEL={B.XP_PER_LEVEL}/PER_WAVE={B.XP_PER_WAVE}")

    print(f"\n##### IST-ZUSTAND (live aus balance.py: Boss x{B.BOSS_HP_MULT}"
          f" / SuperBoss x{B.SUPERBOSS_HP_MULT}, XP-Fix div={B.XP_WAVE_DIV}) #####")
    _print_scenario("Frischer Lauf (keine permanenten Shop-Boni)", start_damage_levels=0)
    _print_scenario("Gut ausgeruestet (Startschaden Stufe 5 = +75 Dmg)", start_damage_levels=5)

    print(f"\n\n##### ZWEITER HEBEL (ADR 014): XP skaliert mit der Welle"
          f" (1+wave//{B.XP_WAVE_DIV}) #####")

    def summary(name, **kw):
        rows, lvl_ups, lvl = simulate(start_damage_levels=0, **kw)
        over = sum(1 for w, dps, hp, ttk, bud, fm, t in rows if ttk > bud)
        w90 = next(r for r in rows if r[0] == 90)
        w100 = next(r for r in rows if r[0] == 100)
        print(f"  {name:<40} Endlevel~{lvl:>3} | Bosse ueber Budget: {over:>2}/10 "
              f"| W90 TTK {w90[3]:>5.1f}s/Bud {w90[4]:.1f}s "
              f"| W100 TTK {w100[3]:>5.1f}s/Bud {w100[4]:.1f}s")

    summary(f"LIVE (ADR 014: div={B.XP_WAVE_DIV}, SQ={B.ENEMY_HP_PER_WAVE_SQ})")
    print("  --- zum Vergleich: ohne den XP-Fix (alter Stand, nur ADR 013) ---")
    summary("ohne XP-Fix (flache Kill-XP)", xp_wave_scale=False)

    print("\n\n##### VERGLEICH: ganz alter Stand vor ADR 013 (Boss x8 / SuperBoss x25,"
          " ohne XP-Fix) #####")
    _print_scenario("Frischer Lauf — alt", start_damage_levels=0,
                    boss_mult=8, super_mult=25, xp_wave_scale=False)

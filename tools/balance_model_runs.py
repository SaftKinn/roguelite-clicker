"""Read-only Mehr-Lauf-Modell: WIE VIELE Läufe braucht man bis Welle 100?

Baut auf `tools/balance_model.py` (gleiche Annahmen) auf und beantwortet die
Design-Frage „man soll ~5 Läufe brauchen": Ein Lauf **stirbt** an der ersten
Boss-Welle, deren TTK über dem Walk-Budget liegt (Boss erreicht die Mitte →
One-Shot). Münzen bis dahin kaufen permanenten **Startschaden** (×Stufe, Kosten
×COST_MULT/Stufe), was die Boss-Wand Lauf für Lauf nach hinten schiebt. Gezählt
wird, bis ein Lauf Welle 100 räumt.

Vereinfachungen (bewusst, wie das Basismodell): die bindende Wand ist das
Boss-DPS-Rennen (HP-Tod durch normale Gegner NICHT modelliert); Kaufpolitik =
nur Startschaden (für die Wand optimal); Karten-RNG fix (seed). „5" ist ein
Richtwert — echte Läufe streuen über Skill/RNG.

Aufruf:  python tools/balance_model_runs.py
"""
import os
import sys

try:                                    # Windows-Konsole (cp1252) sonst Crash auf →/×
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import balance as B
import tools.balance_model as bm


def _coin_income_for_wave(wave: int, gold_mult: float) -> float:
    cvw = B.coin_value_for_wave(wave)              # 1 + wave//3
    if wave % 50 == 0:
        base = 50.0                                # SuperBoss coin_value
    elif wave % 10 == 0:
        base = 10.0                                # Boss coin_value
    else:
        base = B.enemies_for_wave(wave) * bm._avg_xp_per_nonboss_kill(wave)
    coin_gain = getattr(B, "COIN_GAIN_MULT", 1.0)   # globaler Münz-Faktor (+50%, falls gesetzt)
    return base * cvw * gold_mult * coin_gain


def death_wave(sdl: int, boss_mult: float, super_mult: float, sq: float) -> int:
    """Erste Boss-Welle mit TTK > Budget = Todeswelle; sonst 100 (Lauf gewonnen)."""
    rows, _, _ = bm.simulate(start_damage_levels=sdl, boss_mult=boss_mult,
                             super_mult=super_mult, sq=sq)
    for wave, dps, hp, ttk, budget, fair_mult, typ in rows:
        if ttk > budget:
            return wave
    return 100


def runs_to_win(perm_dmg: int, cost_base: int, cost_mult: float, gold_mult: float,
                boss_mult: float, super_mult: float, sq: float,
                max_runs: int = 80, verbose: bool = False):
    B.PERMANENT_DAMAGE_PER_LEVEL = perm_dmg        # Sweep-Override (Analyse-Tool)
    sdl, bank = 0, 0.0
    for run in range(1, max_runs + 1):
        dw = death_wave(sdl, boss_mult, super_mult, sq)
        if verbose:
            print(f"    Lauf {run:>2}: Startschaden-Stufe {sdl:>2} "
                  f"(+{sdl*perm_dmg} Dmg) → Todeswelle {dw}")
        if dw >= 100:
            return run, sdl
        bank += sum(_coin_income_for_wave(w, gold_mult) for w in range(1, dw + 1))
        bought = 0
        while bank >= cost_base * (cost_mult ** sdl):
            bank -= cost_base * (cost_mult ** sdl)
            sdl += 1
            bought += 1
        if verbose:
            print(f"             Münzen → {bought} Stufe(n) gekauft, Rest {bank:.0f}")
    return max_runs + 1, sdl


if __name__ == "__main__":
    print("MEHR-LAUF-MODELL — Läufe bis Welle 100 (read-only)\n")
    print(f"Live-Stand: Boss ×{B.BOSS_HP_MULT} / SuperBoss ×{B.SUPERBOSS_HP_MULT}, "
          f"PermDmg/Stufe {B.PERMANENT_DAMAGE_PER_LEVEL}, CostStartDmg {B.COST_START_DAMAGE}, "
          f"CostMult {B.COST_MULT}, SQ {B.ENEMY_HP_PER_WAVE_SQ}")
    live = runs_to_win(B.PERMANENT_DAMAGE_PER_LEVEL, B.COST_START_DAMAGE, B.COST_MULT,
                       1.0, B.BOSS_HP_MULT, B.SUPERBOSS_HP_MULT, B.ENEMY_HP_PER_WAVE_SQ)
    print(f"  → LIVE braucht {live[0]} Lauf/Läufe bis Welle 100\n")

    # Diagnose: wie verschiebt sich die Todeswelle mit dem permanenten Startschaden?
    print("Todeswelle je Startschaden-Stufe (perm_dmg=20) bei Boss×6/Super×10:")
    B.PERMANENT_DAMAGE_PER_LEVEL = 20
    line = "  "
    for sdl in range(0, 33, 3):
        line += f"St{sdl}:W{death_wave(sdl, 6, 10, B.ENEMY_HP_PER_WAVE_SQ)}  "
    print(line)

    print("\nÖkonomie-Sweep (Ziel ≈ 5 Läufe): perm_dmg / cost_mult / gold / Boss×/Super×")
    print(f"  {'pDmg':>4} {'cMult':>5} {'gold':>4} {'Boss×':>5} {'Sup×':>4}  -> Läufe (Endstufe)")
    best = []
    for perm_dmg in (20, 25, 30):
        for cost_mult in (1.30, 1.40, 1.50):
            for gold in (1.0, 1.5):
                for bossm, superm in [(5, 8), (6, 10), (7, 12)]:
                    r, sdl = runs_to_win(perm_dmg, 50, cost_mult, gold, bossm, superm,
                                         B.ENEMY_HP_PER_WAVE_SQ)
                    if 4 <= r <= 6:
                        best.append((abs(r - 5), r, perm_dmg, cost_mult, gold, bossm, superm, sdl))
    for _, r, pd, cm, gd, bm_, sm_, sdl in sorted(best)[:12]:
        print(f"  {pd:>4} {cm:>5} {gd:>4} {bm_:>5} {sm_:>4}  -> {r} Läufe (Endstufe {sdl})")
    if not best:
        print("  (keine Kombi traf 4–6 — Bereich erweitern)")

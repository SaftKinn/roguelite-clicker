# ADR 018 — Boss-Wand als Meta-Gate: ~5 Läufe bis Welle 100
- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** architecture.md §6/§11; progress.md D33; revidiert ADR 013/014; Modell `tools/balance_model_runs.py`

## Context
Bisher (ADR 013 ×2/×3 + ADR 014 XP-Wellenskalierung) war das Ziel ein **fairer
1→100-Lauf** — das Modell fand „0/10 Bosse über Budget", d. h. ein **frischer Lauf
konnte Welle 100 im ersten Versuch räumen**. Der Nutzer will stattdessen einen echten
**Roguelite-Meta-Loop**: man soll **~5 Läufe** brauchen, bis man Welle 100 schafft —
der Fortschritt kommt über die **permanenten Münz-Upgrades** zwischen den Läufen.

## Decision
Die **Boss-Wand wird bewusst wieder eingeführt** und über permanenten Startschaden
über ~5 Läufe überwunden. Vier Hebel, modellgetrieben kalibriert (`balance.py`):

| Konstante | alt | neu | Wirkung |
|---|---|---|---|
| `BOSS_HP_MULT` | 2 | **6** | Boss-Wand alle 10 Wellen |
| `SUPERBOSS_HP_MULT` | 3 | **10** | W50/100 = harte Tore |
| `PERMANENT_DAMAGE_PER_LEVEL` | 15 | **25** | treibt den Aufstieg |
| `COST_MULT` | 1.65 | **1.4** | Startschaden über ~5 Läufe stackbar |

**Modell (`tools/balance_model_runs.py`, neu):** simuliert aufeinanderfolgende Läufe —
ein Lauf stirbt an der ersten Boss-Welle mit TTK > Walk-Budget; Münzen bis dahin kaufen
permanenten Startschaden (greedy), was die Wand Lauf für Lauf nach hinten schiebt. Mit
den neuen Werten: **Todeswelle 10 → 50 → 80 → 90 → 100** = **5 Läufe** (4 mit „Goldene
Kugeln" ×1.5). Die Todeswelle-je-Stufe-Kurve steigt glatt (St6→W40, St12→W60, St24→W90,
St27→W100), d. h. kein brüchiger Sprung.

## Alternatives
- **Nur Boss-Multiplikator hochdrehen (perm-Dmg/Kosten unverändert):** Modell zeigte eine
  **brüchige Klippe** — Boss×4/Super×6 → 2 Läufe, ×5/×8 → 65 Läufe, ×6+ → *nie* gewinnbar
  (Startschaden plateaut bei ×1.65-Kosten + niedrigem Münz-Einkommen). Darum **gleichzeitig**
  perm-Dmg stärker (25) **und** Kosten flacher (1.4) → glatter, kalibrierbarer Aufstieg.
- **Spieler-Basiskraft senken** statt Boss-HP heben: trifft auch den Frühgame-Flow hart;
  der Boss-Mult ist der gezielte Endgame-/Meta-Hebel.
- **Run-1-Tod später als Welle 10:** ließe sich über einen niedrigeren ersten Boss-Mult
  staffeln; bewusst simpel gehalten (ein Mult für alle Bosse).

## Consequences
- **Positiv:** echter Meta-Loop — frühe Läufe sterben an der Boss-Wand, permanente Upgrades
  fühlen sich notwendig + lohnend an; vier benannte Regler, alle modell-vorrechenbar.
- **Negativ / Bindung:**
  - **Revidiert ADR 013/014:** deren „kein-Wall / fairer-Einzellauf"-Ziel ist bewusst
    aufgegeben. Run 1 stirbt schon am **ersten Boss (Welle 10)** — gewollt, kann aber hart
    wirken.
  - **`COST_MULT 1.65→1.4` gilt für ALLE unendlichen Upgrades** (auch Start-HP) → alles
    etwas billiger stackbar (akzeptiert).
  - **GROSSER VORBEHALT — Modell-Lücke:** Das Modell misst nur die **Boss-DPS-Wand**, nicht
    den **HP-Tod durch reguläre Gegner**. Mit den parallel auf **×10 gesetzten neuen
    Gegnern** (D32; Ork ×25 = bei W50 ~72k HP, **4× der Boss**) könnten zähe Normalgegner
    die *eigentliche* Wand sein (Turm überrannt) → real evtl. **mehr** als 5 Läufe. Das
    Modell kennt diesen Pfad nicht. **Echter Playtest nötig**; Gegenhebel = neue-Gegner-HP
    senken oder das Modell um Überlebens-/Clear-Rate erweitern.
  - **Modell-Annahmen:** Kaufpolitik nur Startschaden, Karten-RNG fix (seed), gold=1.0 →
    „5" ist ein Punktschätzer, streut real über Skill/RNG/Shop-Wahl.
- **Verifikation:** Modell LIVE = 5 Läufe; `py_compile` OK; voller Treiber-Flow
  (Menü→Lauf→Levelup→W99→W100→Sieg) crashfrei mit allen Änderungen (Zoom 1.4, langsamere
  Gegner, ×10-HP-Gegner, Boss×6/×10).

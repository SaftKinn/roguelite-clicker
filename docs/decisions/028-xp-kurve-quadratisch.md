# ADR 028 — XP-Kurve quadratisch: Level 100 kostet ~10000 XP

- **Status:** Accepted
- **Date:** 2026-06-22
- **Refs:** `game/balance.py` (`xp_to_next`), `tools/balance_model.py`; revidiert die lineare Kurve aus ADR 008, ergänzt die Einnahme-Hebel ADR 014 / `xp_round_mult`

## Context
Im Playtest fiel auf: der Spieler levelt **viel zu schnell**. Das Balance-Modell bestätigte
es drastisch — **194 Levelups über einen 1→150-Lauf** (Endstufe ~Level 195). Ursache ist die
**Schere zwischen XP-Einnahme und Levelup-Kosten**:

- **Einnahme/Kill** skaliert stark mit der Welle: `xp_wave_mult` (`1 + wave//8`, ADR 014) ×
  `xp_round_mult` (`1 + 0.1·wave` → Welle 100 = ×11) × `XP_GAIN_MULT` 1.7. Ein Normal-Kill auf
  Welle 100 gibt ~240 XP.
- **Kosten** (`xp_to_next`) skalierte fast gar nicht: linear `XP_BASE + (level-1)·7 + wave·2`.
  Auf Level 100 / Welle 100 = nur ~850 XP → ~4 Kills pro Level.

Die Einnahme rennt der Kostenkurve davon. Nutzerwunsch: **Level 100 soll ~10000 XP kosten** und
die Kosten sollen **stärker mit der Welle skalieren**.

## Decision
**`xp_to_next` von linear auf quadratisch im Level umstellen** (`game/balance.py`):

```python
XP_PER_LEVEL_SQ = 1.0   # XP je (Stufe-1)²  — ersetzt den linearen XP_PER_LEVEL
XP_PER_WAVE     = 10    # je Welle (von 2 erhöht: stärkere Wellen-Skalierung)
xp_to_next(level, wave) = round(XP_BASE + XP_PER_LEVEL_SQ*(level-1)**2 + XP_PER_WAVE*wave)
```

`1.0·(100-1)² ≈ 9801` → der Level-100-Schritt landet bei ~10000–11000 XP (Anker getroffen).

**Bewusst gewählter Tradeoff (Option A, vom Nutzer entschieden):** Das gesamte XP-Einnahme-
Budget über 150 Wellen ist ~161.800 XP. „Level 100 = 10000" und „bis Level 100 kommen"
**schließen sich beim aktuellen Einkommen aus** — die kumulierten Kosten der Stufen 1–99 bei
10000-pro-100-Schritt übersteigen das Budget. Der Nutzer wählte den wörtlichen 10000-Anker;
**Folge: man erreicht pro Lauf nur noch ~Level 72** (Modell), Level 100 wird ein Fernziel
(nur mit Shop-Boni / starkem Build / langem Überleben).

## Alternatives
- **Steilere LINEARE Kurve** (`k≈101/Stufe` für 10000@100): erdrückt den Start (erster Levelup
  ~109 statt 18 XP) und bremst früh wie spät gleich — verworfen. Quadratisch bleibt früh günstig
  (Lv 1 = 18, Lv 25 = 884) und bremst gezielt die *späte* Eskalation.
- **Option B (bis ~Level 100 kommen):** sanftere Kurve (`a≈0.45`), Endlevel ~87, aber
  Level-100-Schritt nur ~6200 statt 10000 — weicht vom Anker ab. Vom Nutzer verworfen.
- **Option C (10000 UND Level 100 erreichbar):** zusätzlich XP-Einkommen ~verdoppeln
  (`XP_GAIN_MULT` ~3.4). Größerer Eingriff ins Balancing, mehr Stellschrauben — verworfen.

## Consequences
- **Positiv:** Leveln deutlich verlangsamt (194 → ~71 Levelups/Lauf); Level-Entscheidungen
  wiegen mehr; die Kosten skalieren jetzt mit Stufe (quadratisch) UND Welle (×5 stärker).
- **Negativ / offen:** Endlevel/Lauf sinkt von ~195 auf ~72 → die meisten Karten werden seltener
  gestapelt; **noch nicht im echten Lauf playtestet** — fühlt sich ~Level 72 als End-Build gut an
  oder zu mager? Hebel gegen zu hart: `XP_PER_LEVEL_SQ` senken (z. B. 0.7 → ~Lv 77) oder Einkommen
  anheben (Richtung Option C). Wechselwirkung mit der DPS-Wand (ADR 013/014) im Auge behalten:
  weniger Level = weniger Schaden-Karten = höhere Boss-TTK.
- **Verifikation:** `xp_to_next(100, 100) = 10809` (Levelterm allein 9801); Balance-Modell
  Endstufe ~Level 72 / 71 Levelups (war ~195 / 194); voller Treiber-Flow (Menü → Levelup → Welle
  100 → Sieg) crashfrei.

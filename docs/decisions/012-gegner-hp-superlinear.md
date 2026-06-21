# ADR 012 — Gegner-HP super-linear skalieren (gegen multiplikative Spielerkraft)
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** architecture.md §6, §11; progress.md D24; baut auf ADR 006 (Wellen-Cap) auf

## Context
Gegner-HP wuchs **linear** (`enemy_hp_for_wave = 30 + Welle·10`) — von Welle 17 zu 100
nur ~5×. Die Spielerkraft wächst dagegen **multiplikativ**: effektive DPS = Schaden ×
Angriffstempo × Multishot × Durchschlag, und seit ADR 010 trifft Autoaim jeden Schuss.
Eine lineare Kurve kann eine multiplikative über lange Läufe mathematisch nie einholen —
der Spieler enteilt zwangsläufig. Symptom (per F4-Debug-Sprung sichtbar): ein Level-17-
Build legte den SuperBoss auf Welle 100 mühelos; Welle 100 war keine Wand.

## Decision
- `enemy_hp_for_wave` von linear auf **super-linear** (linear + quadratisch):
  `(ENEMY_HP_BASE + Welle·ENEMY_HP_PER_WAVE + Welle²·ENEMY_HP_PER_WAVE_SQ) · hp_mult`
  mit `30 / 12 / 0.9`. Benannte Konstanten in `balance.py` (keine Magic Numbers).
- Der quadratische Term (`ENEMY_HP_PER_WAVE_SQ`) greift v.a. spät → echte Endgame-Wand,
  während das frühe Spiel kaum härter wird (Welle 1: 42 statt 40 HP).
- Boss-/SuperBoss-Multiplikatoren (×8 / ×25 in `enemy.py`) bleiben unverändert und
  erben die steilere Basis automatisch.
  > **Revidiert durch ADR 013:** Diese Multiplikatoren wurden später auf ×2/×3 gesenkt —
  > ein Balance-Modell zeigte, dass ×8/×25 auf der quadratischen Basis unfaire Boss-Wände
  > erzeugten (und die hier angenommene „Level ~60+"-Spielerstärke real eher ~Level 33 ist).

## Alternatives
- **Linear steiler (z. B. `Welle·25`):** macht das frühe Spiel zu hart und holt die
  multiplikative Kurve trotzdem nicht ein. Verworfen — Wachstums-*art* war das Problem.
- **Voll exponentiell (`Basis·(1+r)^Welle`):** matcht die Spielerkurve am besten, ist
  aber schwer zu kalibrieren und kippt schnell ins Unschaffbare. Quadratisch ist ein
  beherrschbarer Mittelweg mit einem klaren Regler.
- **Spielerkraft kappen statt Gegner anheben:** würde Build-Vielfalt (der eigentliche
  Spielspaß, architecture.md §1) beschneiden. Lieber Gegner mitziehen.

## Consequences
- **Positiv:** Welle 100 ist wieder eine Wand (SuperBoss 25,7k → 255k HP; Faktor W17→100
  jetzt ~20×). Ein unter-gelevelter Build kann das Endgame nicht mehr wegballern — passt
  zur Erwartung „Level 17 schlägt nicht Welle 100".
- **Negativ / Bindung:** `0.9` ist ein **erster Wurf** — bei 255k SuperBoss-HP besteht
  das Risiko, dass selbst ein echter Welle-100-Spieler (Level ~60+) zu lange braucht oder
  scheitert. `ENEMY_HP_PER_WAVE_SQ` ist der Haupt-Playtest-Regler. **F4 taugt NICHT zum
  Endgame-Balance-Test** (friert Level/Stats ein) — nur ein echter 1→100-Lauf zeigt, ob
  die Kurve gegen reale Spieler-DPS stimmt.
- **Verifikation:** Werte headless geprüft (W17 494 / W50 2880 / W100 10230; SuperBoss
  255.750); Treiber läuft fehlerfrei bis Welle 100. Balance per Playtest offen.

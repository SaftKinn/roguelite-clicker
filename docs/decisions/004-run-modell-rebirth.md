# ADR 004 — Run-Modell: Sieg bei Welle 100, Rebirth als Part 2
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** Decision-Log in progress.md; architecture.md §8; roadmap.md Phase 2 & Part 2

## Context
Das Spiel war bisher endlos (Bosse alle 10 Wellen, SuperBoss alle 50, Tod = Game
Over, „wie weit komme ich"). Für ein rundes, verkaufbares Erlebnis braucht es ein
Erfolgsgefühl und einen klaren Abschluss. Gleichzeitig soll dauerhafte
Meta-Progression der Hauptreiz sein. Constraint: Anfänger, MVP soll schnell
spielbar/verkaufbar sein, Scope eng halten.

## Decision
Ein Run **endet als Sieg beim Besiegen des SuperBosses in Welle 100**. Das
**Rebirth-System** (komplettes Reset → Karte mit 3 Waffen → 1 dauerhaft behalten +
im Verbesserungsmenü upgradebar) ist die Meta-Progression, gehört aber **erst in
Part 2**, nicht in den MVP.

## Alternatives
- **Endlos + Highscore beibehalten:** einfachster MVP, aber kein Abschluss/Sieg-Gefühl
  und keine prägende Meta-Mechanik — schwächere Identität.
- **Beides sofort (Sieg-Kampagne + Endlos-Modus + Rebirth) im MVP:** zu großer Scope
  für einen Anfänger-Solo-MVP, hohes Risiko, nie „fertig" zu werden.

## Consequences
- **Positiv:** Klares MVP-Ziel (Welle 100 + Sieg-Screen) — gut abgrenzbar und
  testbar (roadmap.md Phase 2). Rebirth bleibt als starker Backlog-Hook erhalten,
  ohne den ersten Release zu blockieren.
- **Negativ / Bindung:** Die jetzige Wellen-Skalierung (`5 + (Welle-1)·3`) macht
  Welle 100 unspielbar (≈300 Gegner nahe Welle 99) — Phase 2 muss die Skalierung
  überarbeiten. Das Save-Format muss in Part 2 um Waffen/Rebirth erweitert werden.
- **Offen (siehe progress.md):** Waffe = anderes Schussverhalten ist nur
  Arbeitsannahme; die Waffen-Upgrade-Mechanik im Verbesserungsmenü ist noch nicht
  festgelegt. Beim Umsetzen von Part 2 ggf. ein Folge-ADR.

# ADR 034 — Overdrive: aktivierbare Spieler-Fähigkeit (Leertaste)

- **Status:** Accepted
- **Date:** 2026-06-22
- **Refs:** Decision-Log D43 in progress.md, Open question „Genre-Identität"

## Context

Seit dem Wechsel zum Voll-Auto-Feuer + Autoaim (ADR 010) trifft der Spieler im
laufenden Gefecht **keine Echtzeit-Entscheidung** mehr: Der `fire_timer` taktet, und
`nearest_enemy_pos` zielt selbst. Damit ist der ursprüngliche „Clicker"-Anteil weg —
`progress.md` führt das seit Längerem als offene **Genre-Identitäts-Frage** („woher
kommt die aktive Spannung?"). Build-Tiefe (Karten/Shop) und Gegnerdruck tragen das
Gefecht, aber es fehlt ein Moment, in dem der Spieler aktiv eingreift.

Constraints: Das Feature soll sich sauber in die bestehende Architektur fügen — `gs`-
Dict als State, Auslöser im KEYDOWN-Block, Effekt im PLAYING-Update, Anzeige im HUD —
und **Balance-neutral gegenüber dem Zeitraffer** bleiben (der Update-Loop läuft im
Sub-Tick `for _ in range(time_scale)`, ADR 020).

## Decision

Eine aktivierbare Fähigkeit **„Overdrive"** auf der **Leertaste**: zündet einen
zeitlich begrenzten offensiven Burst (`OVERDRIVE_DURATION_S = 5 s`) mit **×2
Angriffstempo** und **×1.5 Schaden**, danach **Cooldown** (`OVERDRIVE_COOLDOWN_S =
18 s` ab Aktivierung → 13 s echte Abklingzeit). Status als Balken oben mittig
(orange/leerend = aktiv, grau/füllend = lädt, grün/voll = bereit).

Umsetzung:
- Zwei Timer in `gs` (`overdrive_active`, `overdrive_cd`) in **Ticks**, berechnet aus
  Sekunden × Live-FPS und **pro Sub-Tick** dekrementiert → FPS-stabil **und**
  Zeitraffer-fest (verläuft in Spielzeit identisch, nur in Echtzeit schneller), exakt
  wie `fire_timer`/HP-Regen.
- Effekt als reiner Multiplikator an genau zwei Stellen: `attack_speed × od_atk` beim
  Setzen des `fire_timer` und `spawn_projectiles(..., damage_mult=od_dmg)` (neuer
  Default-Parameter `1.0`). Außerhalb des Bursts sind beide Faktoren `1.0` → **keine
  persistente Mutation** von `gs["stats"]`.
- Eigener prozeduraler Sound `"overdrive"` (aufsteigender Sweep) in `game/sounds.py`.

## Alternatives

- **Klick-Einschlag (Meteor) / Schockwelle (Panik-Knopf):** ebenfalls erwogen (mit dem
  Nutzer durchgesprochen). Meteor holt den Clicker am direktesten zurück, Schockwelle
  ist rein defensiv. **Overdrive gewählt** (Nutzerwunsch) — offensiver Power-Spike, der
  mit dem Build synergiert (skaliert über `attack_speed`/`damage` mit allen Karten/
  Shop-Boni) und am einfachsten balancierbar ist (zwei Multiplikatoren + zwei Timer,
  kein neues Ziel-/Geschoss-/AoE-System).
- **Effekt durch Mutation von `gs["stats"]`** (Werte hoch-/runtersetzen): verworfen —
  fragil (Burst-Ende muss exakt zurücksetzen; Interaktion mit Karten-Upgrades während
  des Bursts). Der Multiplikator-an-der-Quelle-Ansatz kann nicht „hängen" bleiben.
- **Cooldown ab Burst-Ende statt ab Aktivierung:** verworfen zugunsten eines einzigen
  Lockout-Timers ab Aktivierung — ein Wert, eine Anzeige, keine Zustands-Verschachtelung.

## Consequences

- Der Spieler hat wieder eine **aktive Echtzeit-Entscheidung** (wann zünde ich den
  Burst — gegen eine dichte Welle, einen Elite, einen Boss-Anlauf?). Erster Schritt zur
  Auflösung der Genre-Frage; weitere aktive Fähigkeiten könnten folgen.
- Tuning-Hebel zentral in `balance.py` (`OVERDRIVE_*`). Offene Balance-Frage: Sind 5 s/
  18 s/×2/×1.5 der richtige Punkt, v. a. gegen die **Boss-DPS-Wand** (ein gut getimter
  Overdrive verkürzt die Boss-TTK spürbar — das Boss-Balance-Modell kennt ihn noch
  **nicht**). Bei Bedarf nachziehen oder ins `tools/balance_model.py` aufnehmen.
- HUD bekommt ein Dauer-Element oben mittig (kollidiert nicht mit Welle/Gegner links,
  Münzen/Speed rechts, XP-Bar unten).
- Verifiziert: voller Treiber-Flow crashfrei (Slot→Menü→PLAYING→Leertaste→Overdrive
  aktiv→F7-Karte→F6/F8→Sieg); Balken-Zustandswechsel grün→orange im Screenshot bestätigt.

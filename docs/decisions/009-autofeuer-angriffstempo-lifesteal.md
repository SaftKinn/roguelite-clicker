# ADR 009 — Auto-Feuer (Halten) + Angriffstempo-Karte + Lifesteal + steileres Gegner-Scaling
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** architecture.md §1, §5; ADR 008 (XP/Level); progress.md D14, D15

> **Nachjustiert (Playtest, gleiche Session, D15):** Die unten genannten
> Start-Kalibrierungen wurden direkt korrigiert — **`BASE_ATTACK_SPEED 0.60 → 1.0`**
> (das „bewusst langsam" weiter unten gilt nicht mehr) und **Gegner-HP-Scaling
> `·14 → ·10`** (zurück zum ADR-008-Stand; „steileres Scaling" zurückgenommen). Mechanik
> (Auto-Feuer, Karte, Lifesteal) unverändert. Aktuelle Werte: `game/balance.py`.

## Context
Der Clicker-Kern (jeder Schuss = ein Mausklick) ermüdet bei längeren Läufen und macht
die Spieler-DPS unkalkulierbar (klick-geschwindigkeitsabhängig). Gewünscht: **Halten
der linken Maustaste feuert automatisch** mit einem **Angriffstempo** (Schüsse/Sek.),
das per Karte steigerbar ist; zusätzlich **Lifesteal** (Treffer heilen) und ein
**steileres Gegner-Scaling**.

## Decision
- **Auto-Feuer:** `mouse_held` (LMB) statt Einzelklick. Im `PLAYING`-Update wird bei
  gehaltener Taste und abgelaufenem `fire_timer` Richtung Maus gefeuert; danach
  `fire_timer = FPS / attack_speed`. Erster Schuss sofort beim Drücken (`fire_timer=0`).
- **Angriffstempo-Stat:** `stats["attack_speed"]` in **Schüssen/Sekunde**, Basis
  `BASE_ATTACK_SPEED = 0.60`. Feuer-Intervall in Frames = `FPS / attack_speed`
  (bei FPS 75: 125 Frames ≈ 1.67 s/Schuss zu Beginn).
- **Neue Karte „Angriffstempo"** (rot, repeatable): `attack_speed *= 1 +
  UPGRADE_ATTACK_SPEED` (`+10%` je Karte, multiplikativ).
- **Lifesteal:** je Treffer an einem Gegner heilt der Spieler `LIFESTEAL_PER_HIT = 1`
  HP (bis `max_hp`) — in `check_projectile_hits()` (bekommt dafür `player`). Pierce/
  Multishot zählen pro getroffenem Gegner.
- **Steileres Gegner-Scaling:** `enemy_hp_for_wave = (30 + wave·14)·hp_mult` (vorher ·10).
- **Levelup-Klick-Sperre:** Der Karten-Screen ignoriert Klicks `LEVELUP_INPUT_LOCK_S = 0.75` s
  lang (sonst wählt das gehaltene Auto-Feuer sofort eine Karte fehl). Umsetzung in
  `UpgradeMenu` (`_input_lock`, in `roll()` gesetzt, in `tick()` gezählt); Hover-Hint
  erscheint erst nach Ablauf.

## Alternatives
- **Klick beibehalten / Auto-Feuer optional:** mehr Code, und der Wunsch war explizit
  Halten-statt-Klicken. Verworfen.
- **Lifesteal = voller Schaden ("1 HP pro Schadenspunkt"):** nahe Unsterblichkeit.
  Stattdessen **1 HP pro Treffer** (skaliert mit Trefferzahl, nicht mit Schaden).
- **Angriffstempo additiv (+0.06/s):** weniger Build-Dynamik als multiplikatives +10%.

## Consequences
- **Positiv:** Kein Klick-Spam; Spieler-DPS ist deterministisch und über Karten
  (Angriffstempo × Schaden × Multishot/Pierce) steuerbar. Lifesteal belohnt aggressives
  Treffen und gibt der Feuerrate doppelten Wert (mehr Schüsse = mehr Heilung). Alle
  Werte zentral in `balance.py`.
- **Negativ / Bindung:** **Basis 0.60/s ist bewusst langsam** — zusammen mit tödlicheren
  Gegnern (ADR 008) und steilerem HP-Scaling kann das **frühe Spiel hart** sein, bis
  Angriffstempo-/Schaden-Karten greifen. Das ist der zentrale Playtest-Regler
  (`BASE_ATTACK_SPEED`, `UPGRADE_ATTACK_SPEED`, `LIFESTEAL_PER_HIT`, `enemy_hp_for_wave`,
  XP-Kurve). Der Treiber feuert nicht (nutzt F-Tasten) — Auto-Feuer/Lifesteal sind per
  **menschlichem Playtest** zu prüfen.
- **Verifikation:** Spiel startet fehlerfrei (Treiber); Feuer-Intervall- und HP-Mathe
  headless geprüft; neue Karte „Angriffstempo" ist im Pool. Spielgefühl per Playtest.

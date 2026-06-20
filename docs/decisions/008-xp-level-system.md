# ADR 008 — XP/Level-System ersetzt Karten-pro-Welle + knackiger/tödlicher Rebalance
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** architecture.md §3.1, §5; ADR 007 (vorheriger ~2h-Rebalance, hier teils revidiert); progress.md D13

## Context
Der ~2h-Rebalance (ADR 007) machte Läufe **zu lang und zu wenig tödlich** — man
überlebte zu lange, ohne dass echter Druck entstand. Gewünscht: **knackigere,
tödlichere** Läufe und ein **XP/Level-System** als Fortschritts-Rückgrat: Gegner
droppen XP, der Spieler steigt Stufen auf, und **jeder Levelup** lässt ihn **1 von 3
Karten** wählen. Die nötige XP soll **mit der Welle wachsen**.

Bisher kam genau eine Karte **pro Welle** (Flow `WAVE_CLEAR → UPGRADE → nächste
Welle`). Das XP-System macht die Karten-Quelle XP-getrieben statt wellengetrieben.

## Decision
**Karten kommen jetzt aus Level-ups, nicht mehr pro Welle** (Vampire-Survivors-artig:
Kill → XP → Levelup → Pause → Karte → weiter).

- **XP-Drop:** Beim Kill `gs["xp"] += enemy.coin_value` (Münzwert = XP-Gewicht; Bosse
  geben mehr). Eine große XP-Charge kann **mehrere** Levelups auf einmal auslösen.
- **XP-Schwelle (wellenabhängig):** `xp_to_next(level, wave) = XP_BASE +
  (level-1)·XP_PER_LEVEL + wave·XP_PER_WAVE` (`balance.py`). Spätere Wellen verlangen
  mehr XP pro Levelup.
- **Level-up → Karte:** je Levelup ein `pending_levelups`; im `PLAYING`-Übergang wird
  bei `pending_levelups > 0` der `UPGRADE`-State (vorhandene `UpgradeMenu`, Titel jetzt
  „Level Up! Wähle eine Karte") betreten. Nach der Wahl `pending_levelups -= 1`; sind
  weitere offen, wird sofort neu gewürfelt, sonst zurück zu `PLAYING`. **Keine
  Wellen-Erhöhung** mehr beim Karten-Pick.
- **`WAVE_CLEAR` rückt jetzt direkt zur nächsten Welle** vor (Banner/Boss-Musik dorthin
  verschoben); kein erzwungenes Karten-Picken zwischen Wellen mehr.
- **HUD:** Level + XP-Fortschrittsbalken unten zentriert.
- **Knackiger/tödlicher (revidiert ggü. ADR 007):** `MAX_ENEMIES_PER_WAVE 80→45`,
  `BASE_SPAWN_INTERVAL 72→58`, `MAX_CONCURRENT_ENEMIES 40→30`, `WAVE_CLEAR_DELAY 120→70`;
  Gegner schneller (`enemy_speed_for_wave` Basis 1.8→2.2, Cap 4.0→4.6) und tödlicher
  (`ATTACK_DAMAGE 14→22`, Archer `DAMAGE 11→16`); Spieler weniger tanky (`MAX_HP 150→120`,
  HP kommt nun v. a. über Level-up-Karten).
- **Dev:** Taste **F5** erzwingt einen Levelup (Karten-Test).

## Alternatives
- **Karten zusätzlich pro Welle UND pro Levelup:** doppelte Quelle, XP würde sich
  belanglos anfühlen. Verworfen — Levelup ersetzt das Wellen-Picken.
- **XP separat vom Münzwert modellieren (eigenes `xp_value` je Gegnerklasse):** mehr
  Stellschrauben, aktuell unnötig — `coin_value` ist eine brauchbare XP-Gewichtung.
  Kann später entkoppelt werden, ohne diese Entscheidung zu kippen.

## Consequences
- **Positiv:** Klassischer, befriedigender Roguelite-Loop; Fortschritt hängt am
  aktiven Spielen (Kills), nicht am bloßen Wellen-Überstehen. Kürzere, gefährlichere
  Läufe. Alle Werte zentral in `balance.py`.
- **Negativ / Bindung:**
  - **Balance ist ein erster Wurf.** XP-Kurve (`XP_BASE/PER_LEVEL/PER_WAVE`) vs.
    Karten-Stärke vs. Gegner-Letalität müssen per Playtest eingestellt werden — zu viele
    Levelups = Schneeball/zu zäh, zu wenige = belanglos. Spannung: mehr Karten machen den
    Spieler stärker (länger), was dem „tödlich/kurz"-Ziel entgegenläuft; daher skaliert
    die Gegner-Letalität bewusst hart.
  - Bosse (1 Gegner) geben wenig XP — Levelup-Tempo hängt an den Normalwellen.
- **Verifikation:** Treiber (`/run-roguelite-clicker`, jetzt mit F5-Levelup-Flow):
  startet fehlerfrei, Screenshots zeigen XP-Bar, „Level Up!"-Karten und intakten
  Sieg-Pfad. XP-Mathematik headless geprüft. **Spielgefühl/Balance braucht menschlichen
  Playtest.**

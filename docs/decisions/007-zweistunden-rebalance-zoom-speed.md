# ADR 007 — ~2h-Rebalance + 1.25x Speed + Kamera-Zoom + größere Sprites
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** architecture.md §3.1, §5, §6, §8; ADR 005 (Belagerung), ADR 006 (Wellen-Cap); progress.md D12

## Context
Welle 100 war strukturell in ~90 Min (Spawn-Floor) erreichbar und das Late-Game
schnell. Gewünscht: **Welle 100 ≈ 2 Stunden Spielzeit**, dichtere Action (höhere
Spawnrate), gefährlichere Gegner bei zugleich zäherem Spieler, **1.25x
Spielgeschwindigkeit**, sowie eine **um 1.2x herangezoomte Kamera** und **um 1.1x
größere Sprites**.

Wichtige Einsicht: Eine Welle endet erst, wenn alle Gegner **gespawnt UND getötet**
sind. Damit ist `Gesamt-Gegner × Spawn-Interval` ein **deterministischer Spielzeit-
Floor**, unabhängig vom Spieler-Skill — das ideale Rückgrat für ein Zeitziel. „Spawnrate
erhöhen" (= Interval senken) verkürzt diesen Floor; die Länge muss daher über **mehr
Gegner pro Welle** kommen, nicht über langsamere Spawns.

## Decision
Tuning zentral in `game/balance.py` (+ `constants.py` FPS, `player.py` Basis-HP,
`enemy.py` Archer-Schaden). Ein Read-only-Spielzeitmodell kalibriert die Zahlen auf
~108 Min Spawn-Floor (+ Kill-Tail/Menüs ≈ 2 h) bei FPS 75:

- **1.25x Speed:** `FPS 60 → 75` (`constants.py`). Alles frame-basierte läuft 1.25x.
- **Spawn-Floor-Rückgrat:** `BASE_SPAWN_INTERVAL 90 → 72` (dichter), aber
  `MAX_ENEMIES_PER_WAVE 40 → 80` und `MAX_CONCURRENT_ENEMIES 25 → 40` (mehr & dichter).
  Cap greift ab Welle 26.
- **Gefährlicher + zäher:** Gegner-Nahkampf `ATTACK_DAMAGE 10 → 14`, Archer-Pfeil
  `EnemyProjectile.DAMAGE 8 → 11`; Spieler `MAX_HP 100 → 150`.
- **Stärkere Karten (damit Spieler-DPS mit ~2x HP-Pool mithält):** `UPGRADE_DAMAGE
  10→15`, `UPGRADE_BULLET_SIZE 4→6`, `UPGRADE_BULLET_SPEED 3→4`, `UPGRADE_MAX_HP 25→40`;
  permanent `PERMANENT_DAMAGE_PER_LEVEL 10→15`, `PERMANENT_HP_PER_LEVEL 30→40`.
- **Kamera-Zoom 1.2x:** Post-Render (`blit_world_zoomed` in `main.py`). Die Welt wird
  in ein `world_surf` gezeichnet; der zentrale 1/1.2-Ausschnitt wird formatfüllend auf
  den Screen skaliert. HUD/Menüs/Cursor danach **unskaliert** obendrauf. Zielen bleibt
  korrekt, da um die Bildmitte (= Turm) skaliert wird (Winkel erhalten).
- **Sprites 1.1x:** `SPRITE_SCALE = 1.1`, in `sprite_loader._px()` auf alle Einheiten-/
  Geschoss-Ladegrößen + Turm angewandt. Hitboxen (`RADIUS`) bleiben (Balance).

## Alternatives
- **Spielzeit über Spawn-Interval strecken statt Gegnerzahl:** widerspricht „Spawnrate
  erhöhen". Verworfen.
- **Welt-Maßstab-Zoom (alle Distanzen 1.2x) statt Post-Render:** ändert Laufwege/Balance
  und ist invasiver. Post-Render gewählt — entkoppelt Optik von Spiellogik.
- **Sprite-Skalierung an jeder Aufrufstelle:** verstreut; stattdessen ein `_px()`-Knoten
  im Loader.

## Consequences
- **Positiv:** Welle 100 zielt auf ~2 h; dichtere, gefährlichere Wellen; ein zäherer,
  aber stärker skalierender Spieler; herangezoomte, größere Optik. Alle Stellschrauben
  zentral in `balance.py` → Feintuning ohne Code-Suche.
- **Negativ / Bindung:**
  - **Exaktes 2-h-Ziel ist skill-abhängig** (Klickrate, Zielgenauigkeit, Karten-Picks).
    Die Zahlen sind ein **kalibrierter Startpunkt**; nach einem echten 1→100-Playtest
    sind v. a. `enemy_hp_for_wave` vs. Spieler-DPS und `MAX_ENEMIES_PER_WAVE`/Interval
    nachzuziehen.
  - **Kamera-Zoom schneidet die Ränder ab:** Gegner spawnen am Welt-Rand und „poppen"
    am gezoomten Bildrand herein. Tradeoff des Post-Render-Zooms.
  - **Performance:** 40 gleichzeitige (1.32x große) Sprites + Geschosse + eine
    `smoothscale` pro Frame bei 75 FPS. `MAX_CONCURRENT_ENEMIES` ist der Perf-Regler;
    bei Rucklern ggf. `smoothscale`→`scale` im Zoom-Blit.
- **Verifikation:** Treiber (`/run-roguelite-clicker`) startet fehlerfrei, Werte live
  (FPS 75, Zoom 1.2, Sprite 1.1, HP 150, cap 80); Screenshots zeigen Zoom + größere
  Sprites. Spielzeit selbst braucht einen menschlichen Playtest.

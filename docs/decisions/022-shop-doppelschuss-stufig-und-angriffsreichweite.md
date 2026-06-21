# ADR 022 — Gestufter Doppelschuss-Shop + begrenzte Angriffsreichweite + Aufgeben behält Gold
- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** architecture.md §4/§7; progress.md; `game/main_menu.py`, `game/balance.py`, `main.py`

## Context
Drei Nutzerwünsche in derselben Tuning-Session, alle rund um Shop/Combat-Komfort:
1. Doppelschuss soll **teurer + verbesserbar** sein (statt Einmalkauf 120): Stufe 1
   „Doppelschuss" 5000, Stufe 2 „Dreifachschuss" 20000.
2. Die **Angriffsreichweite** soll so begrenzt sein, dass man Gegner **immer sieht, wenn
   sie sterben** (der Kamera-Zoom ADR 020/§ schneidet den Rand ab).
3. **Aufgeben** (Pause → Hauptmenü) soll das im Lauf verdiente **Gold behalten**.

## Decision
1. **Gestufter Doppelschuss:** von Einmalkauf (`save["bought"]`) auf **gestuftes Upgrade**
   (`save["upgrades"]["doppelschuss"]`, 0–2) umgestellt. Eigene Kostenliste
   `[COST_DOPPELSCHUSS=5000, COST_DREIFACHSCHUSS=20000]`, max. Stufe 2. Im Shop **eine** Karte
   („Doppelschuss Lv.x/2") in Reihe 1 neben „Goldene Kugeln" (2×2-Layout bleibt). Neue
   `_TIERED`-Kategorie im Menü (capped, eigene Kostenliste je Stufe). Im Gameplay feuert die
   Stufe `n` zusätzliche, **gerade aufs Ziel** verzögerte Schüsse (`pending_shots`,
   `DOPPELSCHUSS_DELAY·k`) → trifft anders als der Multishot-**Fächer** auch Einzelziele/Bosse.
2. **Begrenzte Angriffsreichweite:** `nearest_enemy_pos()` erhält `max_range`; der Turm zielt
   nur auf Gegner innerhalb `PLAYER_ATTACK_RANGE = (SCREEN_HEIGHT/2)/CAMERA_ZOOM ·
   ATTACK_RANGE_FRAC` (0.92). Damit liegt jeder anvisierte (und getötete) Gegner im sichtbaren
   Rechteck. Leitet sich automatisch aus `CAMERA_ZOOM` ab.
3. **Aufgeben bucht Gold:** im Pause→Hauptmenü-Pfad wird `gs["coins"]` ins `total_coins`
   gebucht (+ `best_wave`/`best_coins`, `sd.save`) — gespiegelt vom Game-Over/Sieg-Pfad.

## Alternatives
- **Doppelschuss als zwei Einmalkäufe** (Doppel + separates Dreifach, prerequisite-gated): hätte
  eine 3. Karte in Reihe 1 erzwungen → Layout-Umbau auf 3 Spalten. Eine gestufte Karte ist
  kompakter und trifft „verbesserbar" besser.
- **Reichweite als feste Pixelzahl in balance.py:** würde bei Zoom-Änderung manuell nachgezogen
  werden müssen. Ableitung aus `CAMERA_ZOOM` (Anteil-Regler `ATTACK_RANGE_FRAC`) passt sich selbst an.
- **Aufgeben ohne Gold (Status quo):** verwarf der Nutzer — Fortschritt soll nie verloren gehen.

## Consequences
- **Positiv:** Shop hat einen ersten **mehrstufigen** Kauf (Muster für weitere); Dreifachschuss
  aus dem Shop hilft auch gegen Bosse (Einzelziel); Kills sind immer sichtbar; Aufgeben ist
  „sicher".
- **Negativ / Bindung:**
  - **Begriffs-Kollision:** Es gibt jetzt **zwei** „Dreifach"-Dinge — die Levelup-Karte
    „Dreifachschuss" (Fächer, gegen Schwärme) und Doppelschuss Lv.2 „Dreifachschuss" (gerade
    Schüsse, gegen Bosse). Bei Bedarf umbenennen.
  - **Reichweite koppelt an Zoom:** Gegner kommen näher, bevor sie beschossen werden (etwas
    gefährlicher) — bewusst.
  - **Save-Format:** `upgrades.doppelschuss` (0–2) neu im Default; alte `bought`-Einträge für
    Doppelschuss werden nicht mehr gelesen (Save war ohnehin zurückgesetzt).
- **Verifikation:** Shop-Kauf headless getestet (0→1→2, dann max, korrekte Abzüge 5000/20000);
  `PLAYER_ATTACK_RANGE` ~236 px (sichtbar ~257); Aufgeben bucht Gold (Treiber: 36→41); voller
  Treiber-Flow bis Sieg crashfrei.

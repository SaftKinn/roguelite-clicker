# ADR 025 — Karten-Farbgruppen (ROT/BLAU/GOLD/WEISS) + neue Effekt-Karten

- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** `game/upgrade_menu.py`, `game/balance.py`, `main.py`, `game/player.py`; ergänzt ADR 008/009; Shop-Pendant ADR 026

## Context
Die Karten waren ein flacher Pool aus 7 Offensiv-/HP-Karten mit nur „Red"/„Blue"-Button-Bildern;
Lifesteal war eine globale Konstante (`LIFESTEAL_PER_HIT`), keine Wahl. Der Nutzer wollte echte
Build-Achsen über **vier Farbgruppen** — ROT=Schaden, BLAU=Verteidigung, GOLD=Geld, WEISS=XP —
und mehr Effekte (u. a. Lifesteal als Karte).

## Decision
1. **Gruppen als zentrale Quelle:** `GROUP_COLORS`/`GROUP_TITLES` in `balance.py` (genutzt von
   Karten UND Shop, kein Farb-Drift). Jede Karte trägt ein `group`-Feld.
2. **Getöntes Rundrechteck-Rendering** statt Button-Asset (Gold/Weiß haben keine PNGs): dunkler
   Körper + farbiges Kopfband + Akzent-Rahmen je Gruppe. Asset-frei, alle 4 Gruppen einheitlich,
   eigene Grafiken später nachrüstbar. `_TEXT_MAX_W` auf ~86 % Kartenbreite erhöht (breiteres Feld).
3. **Neue Karten** (Werte in `balance.py`): ROT `lifesteal_pct` „Lebensraub" (+5 % Schaden als HP/
   Treffer) und `lifesteal_flat` „Vampirschlag" (+2 HP/Treffer) — beide stapelbar, gedeckelt auf
   max_hp; BLAU `armor` (−6 %/Stufe, Cap 75 %), `hp_regen` (2 HP/s), `thorns` (20 % Reflect, Cap 100 %),
   `dodge` (5 %/Stufe, Cap 50 %); GOLD `coin_boost` (+15 % Münzen/Lauf); WEISS `xp_boost` (+15 % XP/
   Lauf), `reroll` (+1 Neuwurf-Charge).
4. **Effekt-Hooks:** neue `gs["stats"]`-Felder; `apply_upgrade` setzt sie und ruft
   `_sync_player_defense` (spiegelt Defense/Lifesteal auf `player`, damit die Treffer-Funktionen sie
   ohne stats-Durchreichung kennen). Lifesteal in `check_projectile_hits`
   (`base + flat + damage·pct`). Armor/Dodge in `Player.take_damage` (Dodge-Roll, dann `·(1−armor)`).
   Dornen in `check_enemy_contact` (gibt Dornen-Kills zurück → zählen als Kills für Münzen/XP/Sound).
   HP-Regen als Akku-Tick im PLAYING-Sub-Tick-Loop, an `fps_value` gekoppelt (FPS-/Zeitraffer-stabil).
5. **Reroll = Button** im Levelup-Screen (aus `gs["stats"]["rerolls"]`), nicht als verbrauchbare
   Karte. Ein Mechanismus deckt Karten-Charges (WEISS) und Shop-Gratis-Rerolls (ADR 026) ab.
6. **Boss-Kontakt bleibt tödlich** — der Oneshot setzt `player.hp = 0` direkt (umgeht Armor/Dodge),
   sonst würden Defensiv-Builds Bosse trivialisieren.

## Alternatives
- **Button-PNGs auch für Gold/Weiß:** kein passendes Asset im Tiny-Swords-Pack → Mischlook/Tönung
  nötig. Einheitliche Tönung ist konsistenter und asset-frei.
- **Lifesteal als 5 % vom Max-HP pro Kill:** verworfen (Nutzer wollte „5 % + flat 2" → zwei Karten,
  prozentual vom Schaden + flach).
- **Rüstung multiplikativ stapelnd:** weniger transparent; additiv + Cap ist mit einem balance-Wert tunebar.
- **Dornen auch im Fernkampf:** bräuchte Projektil-Owner-Tracking; bewusst nur Nahkampf.
- **Reroll als Karte:** verbraucht einen Kartenslot/Wahl; Button ist klarer und teilt die Logik mit dem Shop.

## Consequences
- **Positiv:** vier klar getrennte Build-Achsen; Lifesteal/Defensive/Eco wählbar; visuell sofort
  lesbare Gruppen ohne neue Assets; ein Reroll-Mechanismus für Karten + Shop.
- **Negativ / offen:** %-Werte (5 %/6 %/20 % …) sind ungetestet-balanciert (Playtest mit Defensiv-
  Build nötig); neue Karten teilen sich `Icon_05/06` (eigene Icons fehlen); der Pool ist größer →
  eine bestimmte Karte erscheint seltener (Gewichtung könnte später nötig werden).
- **Verifikation:** Render-Shots (`render_cards4.png` alle 4 Gruppen + Reroll-Button; `render_stats.png`
  alle neuen Stat-Zeilen, bedingt). Deterministisch: Armor `40·(1−0,5)=20`; Dodge 100 % → 0 Schaden;
  Lifesteal `50→66` (1+5+10); Dornen-Kill wird zurückgegeben. Voller Treiber-Flow bis Sieg crashfrei.

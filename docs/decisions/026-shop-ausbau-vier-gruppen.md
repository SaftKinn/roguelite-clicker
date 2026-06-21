# ADR 026 — Shop-Ausbau: neue Dauer-Stats, globale Meta-Multiplikatoren, 4-Gruppen-Layout

- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** `game/main_menu.py`, `game/balance.py`, `game/save_data.py`, `main.py`; Karten-Pendant ADR 025; ergänzt ADR 018/022

## Context
Der Münz-Shop hatte vier Käufe (Startschaden, Start-HP, Doppelschuss, Goldene Kugeln) in einem
2-Zeilen-Raster nach Kauf-Typ (∞/gestuft/einmalig). Der Nutzer wollte den Shop deutlich erweitern
und ihn in dieselben vier Farbgruppen wie die Karten gliedern (ADR 025).

## Decision
1. **Neue Käufe** (Preise/Effekte in `balance.py`):
   - **∞ Dauer-Stats:** Start-Tempo (`start_attack_speed`), Start-Kugelgröße (`start_bullet_size`),
     Start-Lebensraub (`start_lifesteal`) — analog zu Startschaden/Start-HP, in `apply_permanent_bonuses`.
   - **∞ globale Meta-Multiplikatoren:** Münz-Meister (`coin_mult`, +5 %/Stufe) und Weisheit
     (`xp_mult`, +5 %/Stufe) — gelten über ALLE Läufe, werden direkt im Münz-/XP-Drop gelesen
     (`1 + lvl·PER_LEVEL`), NICHT als Lauf-Startwert.
   - **∞ Glückshand** (`free_rerolls`): X Gratis-Reroll-Charges pro Lauf (speist `gs["stats"]["rerolls"]`).
   - **Einmalig Vierte Karte** (`extra_card`): Levelup zeigt dauerhaft 4 statt 3 Karten
     (`_card_count(save)` in `main.py`, `roll(count)`).
2. **4-Gruppen-Layout:** eine Spalte je Farbgruppe (Schaden/Verteidigung/Geld/XP) mit farbiger
   Überschrift; Käufe untereinander. Ein gemeinsamer Iterator **`_iter_shop_slots()`** liefert
   `(rect, kind, entry)` und wird von `draw()` UND `handle_click()` genutzt → kein Layout-Drift.
   Kauf-Validierung in einem `_entry_state(kind, entry, save)` (state ∈ buyable/locked/bought/maxed).
3. **Persistenz:** `save_data._DEFAULT["upgrades"]` um die neuen ∞-Zähler erweitert (default 0).
   Alt-Saves ohne diese Subkeys sind unkritisch, weil der Code durchgängig `upgrades.get(key, 0)` nutzt
   (`_read` setzt nur Top-Level-Keys per `setdefault`). `extra_card` lebt in `save["bought"]`.

## Alternatives
- **Kategorie-Zeilen beibehalten (∞/gestuft/einmalig):** skaliert nicht auf ~11 Käufe und passt
  nicht zum gewünschten Farbgruppen-Thema.
- **coin_mult/xp_mult als Lauf-Startwert in stats:** falsch — es sind Faktoren, kein additiver Start;
  daher direkt im Drop multipliziert.
- **Getrennte draw-/click-Layouts:** Drift-Risiko zwischen sichtbarem Slot und Klick-Trefferfläche →
  ein gemeinsamer Iterator ist die robuste Lösung.

## Consequences
- **Positiv:** tieferer Meta-Fortschritt (Eco-Multiplikatoren, mehr Start-Stats, 4. Karte/Rerolls);
  Shop visuell konsistent mit den Karten; Klick/Zeichnung garantiert deckungsgleich; neue Käufe sind
  fast reine Daten (generische Kauf-/Render-Pfade).
- **Negativ / offen:** Preise/Stufen-Effekte ungetestet-balanciert; globale Multiplikatoren können den
  Eco-Loop beschleunigen (Playtest); Rot-Spalte ist mit 5 Käufen am vollsten (Layout bei weiteren
  Käufen prüfen).
- **Verifikation:** `render_shop.png` (4 farbcodierte Spalten, Levels, Preise, „zu teuer", „Gekauft");
  handle_click end-to-end für alle Kauf-Typen (∞/gestuft/einmalig) + Zu-teuer-Sperre, korrekte
  Münz-Abbuchung (100000 → 93480). Voller Treiber-Flow crashfrei.
  Hinweis: der Kauftest schrieb versehentlich in Speicherslot 1 — Slot 1 danach auf einen sauberen
  Standard-Speicherstand zurückgesetzt.

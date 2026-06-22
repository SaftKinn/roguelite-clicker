# ADR 030 — Tanker (Lancer) & Heiler (Monk) als Tier-Reskins

- **Status:** Accepted
- **Date:** 2026-06-22
- **Refs:** `game/enemy.py`, `main.py`; erweitert ADR 024 (Tier-Roster)

## Context
Im Tier-System (ADR 024) bekamen nur 5 der 7 Rollen pro Tier einen eigenen Skin. **tanker
(Lancer) und monk (Monk)** blieben über alle Tiers ihr Tiny-Swords-Original — sie liefen also
auch in der Dämonen- (W51–100) und Drachenwelt (W101–150) als Menschen-Sprites, der sichtbarste
Stilbruch. Anders als die 5 Rollen haben Lancer/Monk reiche **Spezial-Animationen** (Lancer:
5-Richtungs-Lanzenangriff; Monk: Heil-Animation + Heil-FX), die ein Reskin nicht verlieren darf.

## Decision
1. **Nur die Lauf-Frames reskinnen.** Zwei Basisklassen `_LancerReskin(Lancer)` /
   `_MonkReskin(Monk)` überschreiben `_load_sprites`: `super()._load_sprites()` lädt zuerst das
   **Original** (Walk + Spezial-Animationen), danach werden — **nur wenn** `assets/custom/
   <SPRITE_NAME>_run.png` existiert — die Lauf-Frames ersetzt. Spezial-Animationen bleiben immer
   das Original.
2. **Fallback = Original, kein Primitiv.** Fehlt das PNG, bleibt der Tiny-Swords-Look — also
   **keine Regression** (anders als die 5 Rollen, die ohne PNG zum Farbkreis werden). Die Reskins
   sind damit „code-first": einsetzbar, lange bevor die Assets existieren.
3. **Pro-Leaf-Caches.** Jede der 6 Tier-Klassen (SkeletonLancer/Monk, DemonLancer/Monk,
   DrakeLancer/Monk) deklariert ihre Sprite-Caches (`_frames_r/_frames_l`, Lancer: `_lancer_atk`,
   Monk: `_heal_frames_*/_heal_fx_frames`) neu auf `None`, sonst teilen sich die Tiers über die
   Klassenhierarchie versehentlich einen Skin.
4. **Roster-getrieben.** `TIER_ROSTER` bekommt `tanker`/`monk`-Keys je Tier; der Sonderfall in
   `spawn_enemy_for_wave` (`if kind=="tanker": Lancer(...)`) entfällt → `enemy =
   TIER_ROSTER[tier][kind](...)` für ALLE Rollen. Stats unverändert (gleiche `__init__`).

## Alternatives
- **Eigenes Attack/Heal-Sprite je Tier mitreskinnen:** deutlich mehr Assets (5 Lanzen-Richtungen!)
  für wenig Sichtbarkeit; Lauf-Frame-Tausch reicht optisch.
- **Über `_CustomSpriteMixin` wie die 5 Rollen:** würde die Spezial-Animationen platt machen
  (Mixin setzt Attack-Frames leer) und ohne PNG zum Primitiv-Kreis degradieren (Regression).
- **tanker/monk nur in Tier 2+3 reskinnen:** Tier 1 (Mensch vs. Untote) ist weniger störend, aber
  roster-einheitlich für alle 3 Tiers ist konsistenter und kostet durch den Original-Fallback nichts.

## Consequences
- **Positiv:** alle 7 Rollen pro Tier reskinbar; null Regression bis Assets da sind; reine
  Roster-Daten beim Spawn; Cache-Isolation getestet.
- **Negativ / offen:** **6 PNGs fehlen** (`skeleton_lancer`, `skeleton_monk`, `demon_lancer`,
  `demon_monk`, `drake_lancer`, `drake_monk` je `_run.png`, extern via Leonardo) — bis dahin sehen
  tanker/monk in allen Tiers wie das Original aus. Spezial-Animationen bleiben Original-Optik, auch
  nach Reskin (bewusst). Lexikon listet die Reskins (noch) nicht.
- **Verifikation:** 6 Klassen bauen/laden/zeichnen headless → Original-Fallback (Lancer 6 / Monk 4
  Frames), Caches getrennt; `spawn_enemy_for_wave` liefert je Tier die richtige Klasse; 300 Spawns
  über alle Tiers crashfrei (21 Typen).

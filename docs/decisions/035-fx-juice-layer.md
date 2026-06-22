# ADR 035 — FX-/„Juice"-Layer (Partikel, Treffer-Flash, Turm-Animation, Screenshake)

Status: akzeptiert · 2026-06-22

## Kontext

Die Sprites wirkten statisch/steif: der Walk ist nur ein prozeduraler Squash/Stretch
eines Standbilds (`tools/animate_walk.py`), Treffer hatten kein visuelles Feedback,
der Turm war komplett statisch, Kills verpufften ohne Effekt. Der Nutzer wollte das
Spiel „professioneller" aussehen lassen — und fragte, ob dafür **mehrere Ansichten**
(4-/8-Richtungs-Sprites) nötig seien.

Entscheidung gegen Multi-Ansichten: Bei der Seitenansicht-Kamera (Sprite zeigt rechts,
`_both_dirs()` spiegelt für links) bringen Blickwinkel nichts sichtbar ein, kosten aber
das 4–8-fache an Kunst (vgl. Vampire Survivors / Brotato — alle nur L/R-Flip).
„Professionell" entsteht hier aus **Bewegung + Wucht**, nicht aus Winkel-Anzahl.

## Optionen für den FX-Layer

1. **Lose `fx`-Liste parallel zu `dmg_numbers`** (in `main.py`), Effekt-Objekte mit
   einheitlichem `update()`/`alive`/`draw(screen)`-Protokoll, plus Spawner-Funktionen.
2. **Zentraler `FXManager`-Singleton** mit eigener Registry/Lifecycle.

## Entscheidung

**Option 1.** Es existiert bereits genau dieses Muster zweimal im Code: `DamageNumber`
(`game/fx.py`) und Monks `_heal_effects`. Ein neuer FXManager wäre ein paralleles
Subsystem ohne Mehrwert — die Game-Loop verwaltet Effekt-Listen schon idiomatisch
inline (Update an den 3 Sub-Tick-Stellen, Filter, Draw in `world_surf`). Die `fx`-Liste
hängt **nicht** an `gs` (wie `dmg_numbers`), bleibt also außerhalb des Spielzustands
und kann nie einen Crash auslösen (Golden Rule 5).

Konkrete Effekte (Etappen, je per `python main.py` verifiziert):
- **Death-Poof** (`fx.Particle` + `spawn_death_poof`): radialer Partikel-Burst beim Kill;
  Boss/SuperBoss größer/farbig. Gespawnt in der Kill-Schleife (`main.py`).
- **Treffer-Flash** (`Warrior._hit_flash` + `_apply_hit_flash`): getroffenes Sprite
  blitzt ~5 Ticks weiß. Technik: Frame-**Kopie** mit `BLEND_RGB_ADD` — addiert nur RGB,
  lässt die **Alpha-Maske** unangetastet (kein Halo); nur während des Flashs teuer.
  In `_blit_sprite` (alle Läufer) **und** den Spezial-Frame-Blits (Archer/Lancer/Monk/
  Boss/SuperBoss) eingehängt → universell.
- **Turm-Animation** (`game/player.py`): Idle-Puls (sin-Scale ±3 %), Recoil-Pop +
  Versatz entgegen Schussrichtung (`trigger_recoil` vom Loop bei jedem Schuss),
  Overdrive-Glühen (`BLEND_RGB_ADD`). Rein Transform/Tint des vorhandenen
  `player_tower.png`; Fallback-Kreis bleibt.
- **Mündungsblitz** (`fx.MuzzleFlash`, additiv): an beiden Turm-Schussstellen.
  Wichtig: `BLEND_RGB_ADD` ignoriert Quell-Alpha → RGB mit Restlebensdauer skalieren,
  sonst fadet der Blitz nicht.
- **Projektil-Trail** (`fx.TrailDot`): pro Geschoss je Sub-Tick ein fadender Punkt.
- **Screenshake** (`balance.SHAKE_*`): Boss-Tod versetzt die Gameplay-Ebene um einen
  kleinen Zufalls-Offset (`blit_world_zoomed(..., offset)`); der Boden liegt darunter
  und füllt die Ränder → kein Loch. Amplitude pro Sub-Tick um `SHAKE_DECAY` abklingend
  (zeitraffer-stabil), an allen 3 FX-Update-Stellen dekrementiert (auch WAVE_CLEAR/
  UPGRADE, sonst würde der Shake bei sofortigem Wellen-Clear hängen bleiben).

## Konsequenzen

- **+** Sofort sichtbarer „Feel"-Sprung auf ALLE Gegner, ohne neue Kunst.
- **+** Null Gameplay-Kopplung: FX leben außerhalb von `gs`, sind rein additiv/Alpha,
  Ausfall ist folgenlos.
- **+** Konsistent mit bestehendem `DamageNumber`-/`_heal_effects`-Muster.
- **−** Tuningwerte liegen teils in `fx.py`/`player.py` als Modulkonstanten (rein visuell),
  nur die gameplay-nahen Shake-Werte in `balance.py` — bewusste Aufteilung.
- **Offen:** echte KI-Frame-Animationen für Helden-Motive (Bosse/Turm) als nächste Etappe
  (gleiches Strip-Format `_load_custom_strip`, kein Code nötig); optional Lauf-Staub,
  Gegner-Muzzle-Fallback. Hintergrund-Animation bewusst zuletzt.

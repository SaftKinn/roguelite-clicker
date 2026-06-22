# ADR 036 — 3D-Pre-Render statt 2D-Animation für Helden-Motive

Status: akzeptiert · 2026-06-22

## Kontext

ADR 035 hielt als offene Etappe fest: „echte KI-Frame-Animationen für Helden-Motive
(Bosse/Turm)". Die bis dahin gebauten 2D-Wege wurden am **Tier-2-Boss** durchgespielt
und vom Nutzer der Reihe nach als **minderwertig** verworfen:

1. **KI-Video (Ludo.ai, image-to-video):** das `_static.png` wird animiert. Ergebnis
   matschig (Video-Modelle rechnen intern klein + temporal geglättet → die scharfen
   Leonardo-Details verwischen) und das Modell erfand ein Ende (Brust-Blitz) → Loop-Naht
   sprang. Zusätzlich rendert Ludo ein graues Transparenz-Schachbrett ins MP4 (Keying-Stress).
2. **Prozedural (`tools/animate_walk.py`):** scharf, aber nur Bob/Sway/Stauchen eines
   Standbilds — vom Nutzer als „Wackeln" / billig empfunden.
3. **Cutout-Rig (Sprite in Teile schneiden, an Knochen drehen; Prototyp gebaut):** scharf
   + echte Beinbewegung, aber **Naht-Risse** an Schultern/Hüften. Grund ist fundamental:
   ein flaches Bild kennt seine **verdeckten Flächen** nicht — bewegt sich ein Glied,
   klafft dahinter ein Loch (ohne manuelles Nachmalen nicht lösbar).

Gemeinsamer Kern des Scheiterns: **2D-Animation aus EINEM Bild hat keine Information über
verdeckte Geometrie.** Bewegung braucht genau diese Information.

## Entscheidung

**3D-Pre-Render.** Das Motiv wird als 3D-Modell besorgt, in 3D animiert und **frontal als
transparente 2D-Sprite-Sequenz gerendert** — die klassische „pre-rendered"-Technik (Donkey
Kong Country, Diablo 1). Die 3D-Quelle **hat** die verdeckten Flächen, also ist jeder
gerenderte Frame korrekt: scharf, lochfrei, echter Schritt, perfekter Loop. Im Spiel läuft
weiterhin nur eine billige 2D-PNG — **kein 3D zur Laufzeit**, Pygame bleibt 2D.

Pipeline (Tier-2 erstmals durchgezogen):
1. **Bild → 3D + Animation:** Meshy.ai (image-to-3D). Liefert auto-gerigtes Modell **inkl.
   fertiger Clips** (Walking/Running/RunFast/Attack/Elbow_Strike) als GLB — Mixamo entfiel.
2. **Render:** neues **`tools/blender_sprite_render.py`** (Blender 5.1 headless): GLB
   importieren, **orthographische Frontalkamera** (an die Bounding-Box gefittet), Film
   transparent, EEVEE, Animations-Framebereich aus der Action → PNG-Sequenz. Flags `--test`
   (1 Frame zum Ausrichten), `--back` (Kamera auf +Y), `--res`, `--frames-step`.
3. **Packen:** vorhandenes `tools/frames_from_clip.py <ordner> <name>_run.png --bg none
   --frames 12` (transparente Frames → kein Keying; Fußpunkt-Verankerung + gemeinsame
   Skalierung wie bei allen Strips).
4. **Einsetzen:** Datei nach `assets/custom/<name>_run.png` — der Loader (`SPRITE_NAME`)
   zieht sie automatisch. **Null Spielcode-Änderung.**

## Konsequenzen

- **+** Qualitätssprung: scharf wie das Original-Artwork, echte Schrittfolge, lochfrei,
  sauberer Loop. Im Spiel (F3 → Welle 60) bestätigt.
- **+** Nutzt die bestehende `_run.png`-Pipeline 1:1 weiter — nur die PNG wird getauscht.
- **+** Wiederverwendbar für alle Helden-Motive; Meshy liefert nebenbei Attack/Run-Clips,
  die später `<name>_atk.png`-Strips werden können (gleiche Pipeline, anderes GLB).
- **−** Der „3D-Look" ist **nicht 1:1** das gemalte Leonardo-Artwork (KI-Mesh = weichere
  Texturen, vereinfachte Details). Bewusster Tausch: exakte Bild-Treue ↔ perfekte Animation.
- **−** Externe Tools nötig (Meshy-Credits, Blender). Die 3D-Quellen sind groß (~39 MB/Boss)
  → `assets/custom/_meshy*/` ist gitignored; nur der fertige Strip kommt ins Repo.
- **−** Meshys Auto-Rig ist **humanoid** — Flügel/große Waffen flattern nicht von selbst und
  wirken steif; schlichte humanoide Silhouetten rigen am besten.
- **Offen:** Tier-1/Tier-3 + die 3 SuperBosse hängen noch am prozeduralen `animate_walk`
  und können nach derselben Pipeline ersetzt werden; In-Game-Lauftempo der 12 Frames im
  echten Feel ungeprüft; Attack-Strips noch nicht gebaut.

> Hinweis: Aus demselben Meshy-Modell ist parallel ein **separates** Godot-3D-Experiment
> entstanden (steuerbarer Charakter, laufen/angreifen) — eigenes Projekt **außerhalb dieses
> Repos**, nicht Teil des Roguelite-Clickers.

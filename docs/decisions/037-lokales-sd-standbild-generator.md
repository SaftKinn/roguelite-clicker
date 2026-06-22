# ADR 037 — Lokales Stable Diffusion als Standbild-Generator

Status: akzeptiert · 2026-06-22

## Kontext

Die Sprite-Pipeline hatte bisher genau **eine Lücke**: den Schritt, der das *Bild selbst*
erzeugt. Freistellen (`key_black_bg.py`), Animieren (`animate_walk.py`, 3D-Prerender nach
ADR 036) und das Packen zum Loader-Strip (`frames_from_clip.py`) existieren — das Standbild
kam aber von Hand aus **Leonardo.ai** (Cloud, Credits, online, ein Bild nach dem anderen).

Der Wunsch: diesen Generator-Schritt **lokal, skriptbar und kostenfrei pro Bild** machen
(eigene GPU), damit ganze Gegner-Sätze als Batch entstehen — im einheitlichen Tiny-Swords-Stil
aus `docs/sprite-prompts.md`.

Beim Abstecken kam die ehrliche Frage auf: *„Bekommen wir damit professionelle Assets?"*
Antwort getrennt nach zwei Fähigkeiten von SD:

- **Einzel-Standbilder:** ja, professionell erreichbar (guter Cartoon-Checkpoint + fester
  Stil-Prompt/Referenz + Kuration mehrerer Kandidaten). Das ist SD's *starke* Seite.
- **Animations-Frames mit frame-genauer Konsistenz:** riskant — SD generiert jeden Frame neu
  und neigt zu Flimmern/Drift. Genau dafür hat **ADR 036** bereits den sicheren Weg gewählt
  (3D-Prerender).

## Entscheidung

**Lokales Stable Diffusion erzeugt nur das Standbild** — `assets/custom/<name>_static.png` —
und rastet damit in den **bestehenden** Workflow ein (`sprite-prompts.md` Schritt 1 → 2):
das Standbild wird wie gehabt animiert (`animate_walk.py` prozedural oder 3D-Prerender für
Helden-Motive). **Die Animation bleibt unangetastet.** SD ersetzt nur Leonardo als
Bild-Quelle, nicht den Animations-Weg.

Technischer Aufbau (alles neu unter `tools/`, rein additiv — kein Spielcode berührt):

1. **Stack: ComfyUI als separater Prozess**, angesprochen über die lokale HTTP/WS-API
   (`127.0.0.1:8188`). Damit bleibt **torch/CUDA komplett aus dem Spiel** — `python main.py`
   und die Pflicht-Dep (pygame) ändern sich nicht. Der Workflow-Graph liegt als JSON vor
   (reproduzierbar, fixer Seed).
2. **`tools/sd_style.py`** — Stil-Wahrheit (single source): `STYLE_PREFIX`, `NEGATIVE_PROMPT`
   (1:1 aus `sprite-prompts.md`), die 15 `SUBJECTS`, `ARCHETYPE_PRESETS`, Sampler-Defaults.
   Neuer Gegner = ein Eintrag, kein verstreuter Prompt (keine Magic Numbers).
3. **`tools/sd_comfy.py`** — dünner Client (`is_up`, `load_workflow`, `set_inputs`, `run`).
4. **`tools/sd_gen.py`** — Orchestrator + CLI: erzeugt **mehrere Kandidaten** je Gegner
   (txt2img, optional IP-Adapter-Stil-Referenz für Familien-Look), keyt jeden frei
   (`key_black_bg.key_black` Magenta **oder** `--matte rembg`), legt ein **Kontaktblatt**
   zur Auswahl an. `--pick N` befördert den gewählten Kandidaten zu `<name>_static.png`.

**Stil-Konsistenz** zuerst über Prompt-Prefix (+ optional Stil-Referenzbild). Reicht der
Familien-Look nicht, folgt **LoRA** auf dem externen Master-Asset-Ordner (eigene spätere
Entscheidung, nicht Teil dieses ADR).

## Konsequenzen

- **+** Bild-Erzeugung wird lokal, offline, gratis pro Bild und **batch-fähig** (alle 15
  Gegner auf einmal), im festen Stil.
- **+** Spielt SD's starke Seite (Standbilder) aus und **umgeht** das Animations-Konsistenz-
  Risiko, das ADR 036 dokumentiert hat.
- **+** Null Spielcode-Änderung; klinkt sich in die bestehende `_static.png → _run.png`-Kette.
  `key_black_bg.py` wird unverändert wiederverwendet.
- **+** Kuration eingebaut (mehrere Kandidaten + Kontaktblatt) → „professionell" ist eine
  Frage der Auswahl, nicht des Glücks beim ersten Treffer.
- **−** Qualität steht und fällt mit dem **Checkpoint** (nacktes SD-Basismodell reicht nicht;
  gepflegter Cartoon-/Stylized-Checkpoint nötig) und dem Stil-Setup. Ohne das nur Mittelmaß.
- **−** Einmaliges **Setup auf der GPU-Maschine** (ComfyUI + CUDA + Modelle, mehrere GB) ist
  Nutzer-Aufgabe; die Tools prüfen Erreichbarkeit (`is_up`) und melden sauber statt zu crashen.
- **−** SD-Modelle/Checkpoints sind groß → wie die Meshy-Quellen (ADR 036) **gitignored**;
  nur die fertigen `<name>_static.png` kommen ins Repo.
- **Offen:** Animation für Helden-Motive bleibt 3D-Prerender (ADR 036); volle SD-Animation
  (OpenPose/AnimateDiff) ist bewusst zurückgestellt; LoRA erst falls der Stil-Prompt nicht reicht.

> Abgrenzung zu ADR 036: 036 löst *Animation* (3D-Prerender). 037 löst *Bild-Erzeugung*
> (lokales SD statt Leonardo). Sie ergänzen sich; keiner ersetzt den anderen.

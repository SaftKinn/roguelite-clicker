# Lokaler SD-Standbild-Generator — Setup & Nutzung (ADR 037)

Erzeugt professionelle Einzel-Sprites (`assets/custom/<name>_static.png`) lokal mit
Stable Diffusion, im Tiny-Swords-Stil aus `docs/sprite-prompts.md`. **Animation** läuft
unverändert über `tools/animate_walk.py` bzw. 3D-Prerender (ADR 036) — SD ersetzt nur den
Bild-Schritt (vorher Leonardo).

Das Spiel selbst bleibt unberührt: `python main.py` braucht **kein** torch/ComfyUI.

---

## Architektur in einem Satz

`tools/sd_gen.py` → spricht per HTTP die lokal laufende **ComfyUI** an (eigener Prozess,
bringt torch/CUDA mit) → bekommt Kandidaten-Bilder → stellt sie frei → du wählst den besten.

```
sd_style.py   (Stil/Prompts, single source)
     │
sd_gen.py ──HTTP──▶ ComfyUI (127.0.0.1:8188)  ──▶  Roh-Bilder
     │                                              │
     └── freistellen (key_black_bg / rembg) ◀───────┘
     └── Kontaktblatt ─▶ --pick N ─▶ assets/custom/<name>_static.png
```

---

## Einmaliges Setup (GPU-Maschine)

1. **ComfyUI installieren** (eigenes venv, NICHT das Spiel-venv):
   https://github.com/comfyanonymous/ComfyUI — Windows-Portable oder `git clone` + venv.
   Mit GPU/CUDA-torch starten. ComfyUI lauscht dann auf `http://127.0.0.1:8188`.

2. **Checkpoint besorgen** (entscheidet 80 % der Qualität — NICHT das nackte SD-Basismodell):
   einen gepflegten Cartoon-/Stylized-SD-1.5-Checkpoint von civitai.com nach
   `ComfyUI/models/checkpoints/` legen. Dateinamen merken → an `sd_gen.py --ckpt` übergeben
   (oder `SD_CKPT`-Env setzen). Default erwartet `cartoon_style.safetensors`.

3. **Tool-Deps ins Spiel-venv** (leichtgewichtig, kein torch):
   ```bash
   pip install -r tools/requirements-sd.txt
   ```

4. **(Optional) rembg** für `--matte rembg` (farbkritische Roben, z. B. Lich):
   ```bash
   pip install rembg onnxruntime
   ```

5. **(Optional) IP-Adapter** für stärkeren Familien-Look über ein Stil-Referenzbild.
   Der Workflow `workflows/still_ipadapter.json` ist **bereits gebaut** — `sd_gen.py` schaltet
   automatisch darauf um, sobald du `--ref <bild.png>` übergibst (ohne `--ref` bleibt es
   txt2img). Dafür in ComfyUI installieren:
   - **Erweiterung** `ComfyUI_IPAdapter_plus` (cubiq) über den ComfyUI-Manager.
   - **IP-Adapter-Modell** nach `ComfyUI/models/ipadapter/` und das passende
     **CLIP-Vision-Modell** nach `ComfyUI/models/clip_vision/` (Links im Repo der Erweiterung;
     das Preset „STANDARD (medium strength)" im Workflow zieht das Standard-SD-1.5-IP-Adapter-Modell).

   Stärke der Referenz: `--ip-weight` (Default 0.5; höher = treuer am Referenzstil, aber weniger
   Motiv-Vielfalt). Stimmt eine Node nicht mit deiner Plugin-Version überein, nur die betroffenen
   `inputs` in `still_ipadapter.json` anpassen.

---

## Nutzung

```bash
# 0) Erreichbarkeit prüfen:
python tools/sd_comfy.py

# 1) Trockenlauf — nur Prompt-Vorschau, kein ComfyUI nötig:
python tools/sd_gen.py --name skeleton_warrior --dry-run

# 2) Kandidaten erzeugen (ComfyUI muss laufen):
python tools/sd_gen.py --name skeleton_warrior --ckpt deinCheckpoint.safetensors
#    → assets/custom/_sd_raw/skeleton_warrior_contact.png ansehen

# 3) Besten Kandidaten übernehmen:
python tools/sd_gen.py --name skeleton_warrior --pick 3
#    → assets/custom/skeleton_warrior_static.png

# 3b) Mit Stil-Referenz für einheitlichen Familien-Look (nutzt IP-Adapter automatisch):
python tools/sd_gen.py --name imp_warrior --ref assets/custom/skeleton_warrior_static.png

# 4) Animieren wie gewohnt (unverändert):
python tools/animate_walk.py assets/custom/skeleton_warrior_static.png \
                             assets/custom/skeleton_warrior_run.png
```

Bekannte Gegner-Namen (aus `sd_style.SUBJECTS`): die 15 Tier-Gegner aus `sprite-prompts.md`.
Freies Motiv ohne Tabelle: `--subject "..." --archetype tank`.

### Wichtige Flags

| Flag | Bedeutung |
|---|---|
| `--name` | Gegner aus der Tabelle (füllt Motiv + Archetyp) |
| `--subject` / `--archetype` | freies Motiv überschreibt die Tabelle |
| `--candidates N` | wie viele Varianten (Default 6) |
| `--matte magenta\|rembg` | Freistell-Methode (sonst Archetyp-Default) |
| `--pick N` | Kandidat N → finales `<name>_static.png` |
| `--ckpt` | Checkpoint-Datei in ComfyUI |
| `--seed/--steps/--cfg/--size` | Sampler-Tuning |
| `--ref` | Stil-Referenzbild → schaltet automatisch auf den IP-Adapter-Workflow |
| `--ip-weight` | Stärke der Stil-Referenz (Default 0.5; nur mit `--ref`) |
| `--workflow` | Workflow-JSON erzwingen (überschreibt die Auto-Wahl) |
| `--dry-run` | nur Prompt zeigen |

---

## Qualität & Grenzen (ehrlich, siehe ADR 037)

- **Standbilder:** professionell erreichbar — mit gutem Checkpoint, festem Stil-Prompt und
  Kuration (mehrere Kandidaten, besten wählen). Das ist SD's starke Seite.
- **Animation NICHT über SD** in diesem Tool: frame-genaue Konsistenz ist SD's Schwäche
  (ADR 036). Bewegung kommt aus `animate_walk` / 3D-Prerender.
- Reicht der einheitliche Look nicht, ist der nächste Schritt **LoRA** auf dem externen
  Master-Asset-Ordner (eigene spätere Entscheidung, noch nicht gebaut).

## Dateien (alle additiv unter tools/, kein Spielcode berührt)

- `sd_style.py` — Stil/Prompt-Wahrheit (15 Motive, Prefix, Negative, Sampler-Defaults)
- `sd_comfy.py` — ComfyUI-HTTP-Client (`is_up`, `load_workflow`, `set_inputs`, `run`)
- `sd_gen.py` — Orchestrator + CLI
- `workflows/still_txt2img.json` — txt2img-Graph mit Platzhalter-Tokens
- `workflows/still_ipadapter.json` — wie txt2img + IP-Adapter-Stilreferenz (`--ref`)
- `requirements-sd.txt` — leichte Tool-Deps (kein torch)

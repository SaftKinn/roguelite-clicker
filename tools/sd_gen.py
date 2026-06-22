#!/usr/bin/env python3
"""Lokaler SD-Standbild-Generator für Tier-Gegner (ADR 037).

Erzeugt aus einem Gegner-Namen ein spielfertiges **Standbild** `assets/custom/<name>_static.png`
— genau die Datei, die der bestehende Workflow (sprite-prompts.md Schritt 1) erwartet und die
dann via `tools/animate_walk.py` (oder 3D-Prerender, ADR 036) zum `_run.png` animiert wird.

Ablauf:
  1. Stil + Motiv aus `tools/sd_style.py` zum vollen Prompt zusammensetzen.
  2. ComfyUI (lokal, eigener Prozess) erzeugt **mehrere Kandidaten** (txt2img, optional eine
     IP-Adapter-Stil-Referenz für den Familien-Look) — kuratieren statt Glück.
  3. Jeden Kandidaten **freistellen**: `--matte magenta` (Ecken-Flood-Fill via
     `tools/key_black_bg.py`) oder `--matte rembg` (inhaltsbasiert, für farbkritische Roben).
  4. **Kontaktblatt** aller freigestellten Kandidaten unter `assets/custom/_sd_raw/` ablegen.
  5. `--pick N` befördert Kandidat N zu `assets/custom/<name>_static.png`.

Beispiele:
    # Trockenlauf — zeigt nur den aufgelösten Prompt, braucht KEIN ComfyUI:
    python tools/sd_gen.py --name skeleton_warrior --dry-run

    # 6 Kandidaten erzeugen (ComfyUI muss laufen), dann Kontaktblatt ansehen:
    python tools/sd_gen.py --name skeleton_warrior

    # Kandidat 3 als finales Standbild übernehmen:
    python tools/sd_gen.py --name skeleton_warrior --pick 3

    # Freies Motiv ohne Tabellen-Eintrag:
    python tools/sd_gen.py --name boss_test --subject "A giant flaming skull boss" --archetype tank

Die schweren ML-Teile leben in ComfyUI (separater Prozess) — dieses Tool importiert nie torch.
`_sd_raw/` (Roh- + Kandidatenbilder) ist groß und gehört in .gitignore; nur das fertige
`<name>_static.png` kommt ins Repo.
"""
import argparse
import os

import sd_style
import sd_comfy

_OUT_DIR = os.path.join("assets", "custom")
_RAW_DIR = os.path.join(_OUT_DIR, "_sd_raw")
# Ohne Stil-Referenz reicht txt2img; mit --ref wird automatisch der IP-Adapter-Graph genutzt.
_WORKFLOW_PLAIN = "still_txt2img"
_WORKFLOW_REF = "still_ipadapter"
# Default-Checkpoint-Dateiname in ComfyUI/models/checkpoints/ — per --ckpt überschreibbar.
_DEFAULT_CKPT = os.environ.get("SD_CKPT", "cartoon_style.safetensors")


# --- Freistellen ---------------------------------------------------------------------

def _square_pad(img, pad: float = 0.06):
    """Auf Inhalt zuschneiden und zentriert auf ein Quadrat legen — loader-sicher (1 Frame,
    quadratisch). Gleiche Geometrie wie key_black_bg, hier für bereits transparente Bilder."""
    from PIL import Image
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    cw, ch = img.size
    side = int(max(cw, ch) * (1 + pad))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - cw) // 2, (side - ch) // 2), img)
    return canvas


def _freistellen(raw_path: str, dst_path: str, matte: str, thresh: int, enclosed: bool) -> None:
    """Einen Roh-Kandidaten freistellen → transparentes, quadratisches PNG."""
    if matte == "rembg":
        try:
            from rembg import remove
        except ImportError:
            raise SystemExit(
                "matte=rembg braucht `rembg` (+onnxruntime):\n"
                "    pip install rembg onnxruntime\n"
                "Oder --matte magenta nutzen (kein Extra-Paket).")
        from PIL import Image
        cut = remove(Image.open(raw_path).convert("RGBA"))
        _square_pad(cut).save(dst_path)
    else:  # magenta: bestehendes Tool unverändert wiederverwenden
        import key_black_bg
        key_black_bg.key_black(raw_path, dst_path, thresh=thresh, enclosed=enclosed)


# --- Kontaktblatt --------------------------------------------------------------------

def _contact_sheet(keyed_paths: list, dst: str, cell: int = 256) -> None:
    """Alle freigestellten Kandidaten nummeriert in ein Raster legen (zur Auswahl per --pick)."""
    from PIL import Image, ImageDraw
    import math
    n = len(keyed_paths)
    cols = min(n, 3)
    rows = math.ceil(n / cols)
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (40, 40, 48, 255))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(keyed_paths):
        img = Image.open(p).convert("RGBA")
        img.thumbnail((cell - 16, cell - 28), Image.LANCZOS)
        cx = (i % cols) * cell
        cy = (i // cols) * cell
        sheet.alpha_composite(img, (cx + (cell - img.width) // 2, cy + 24))
        draw.text((cx + 8, cy + 6), f"[{i}]", fill=(255, 230, 120, 255))
    sheet.save(dst)


# --- Hauptablauf ---------------------------------------------------------------------

def generate_still(name: str | None, subject: str | None, archetype: str | None,
                   candidates: int, matte: str | None, ref: str | None,
                   seed: int, steps: int, cfg: float, size: int, ckpt: str,
                   pick: int | None, thresh: int, enclosed: bool, dry_run: bool,
                   workflow: str | None, ip_weight: float) -> None:
    subj, arch = sd_style.resolve(name, subject, archetype)
    prompt = sd_style.build_prompt(subj, arch)
    matte = matte or sd_style.preset_for(arch)["matte"]
    tag = name or "sd_out"
    # Ohne expliziten --workflow: mit Stil-Referenz IP-Adapter, sonst schlichtes txt2img.
    if workflow is None:
        workflow = _WORKFLOW_REF if ref else _WORKFLOW_PLAIN

    print(f"\n# {tag}  [{arch}]  matte={matte}  Kandidaten={candidates}  seed={seed}")
    print(f"PROMPT:\n  {prompt}")
    print(f"NEGATIVE:\n  {sd_style.NEGATIVE_PROMPT}")
    print(f"PARAMS: steps={steps} cfg={cfg} size={size} ckpt={ckpt} "
          f"ref={ref or '-'} ip_weight={ip_weight} workflow={workflow}")

    if dry_run:
        print("\n[dry-run] Kein ComfyUI-Aufruf. Prompt-Vorschau oben.")
        return

    ok, msg = sd_comfy.is_up()
    print(f"\nComfyUI: {msg}")
    if not ok:
        raise SystemExit(1)

    os.makedirs(_RAW_DIR, exist_ok=True)
    wf_template = sd_comfy.load_workflow(workflow)
    ref_name = sd_comfy.upload_image(ref) if ref else None

    keyed_paths = []
    for i in range(candidates):
        wf = sd_comfy.set_inputs(
            wf_template, prompt=prompt, negative=sd_style.NEGATIVE_PROMPT,
            seed=seed + i, steps=steps, cfg=cfg, width=size, height=size,
            ckpt=ckpt, ref_image=ref_name, ipweight=ip_weight, batch=1)
        print(f"  Kandidat {i} (seed {seed + i}) …")
        imgs = sd_comfy.run(wf, client_id=f"{tag}_{i}")
        for j, img in enumerate(imgs):
            raw_path = os.path.join(_RAW_DIR, f"{tag}_cand{i}_{j}_raw.png")
            keyed_path = os.path.join(_RAW_DIR, f"{tag}_cand{len(keyed_paths)}.png")
            img.save(raw_path)
            _freistellen(raw_path, keyed_path, matte, thresh, enclosed)
            keyed_paths.append(keyed_path)

    contact = os.path.join(_RAW_DIR, f"{tag}_contact.png")
    _contact_sheet(keyed_paths, contact)
    print(f"\n{len(keyed_paths)} Kandidaten freigestellt. Kontaktblatt: {contact}")

    if pick is not None:
        if not 0 <= pick < len(keyed_paths):
            raise SystemExit(f"--pick {pick} außerhalb 0..{len(keyed_paths) - 1}")
        import shutil
        dst = os.path.join(_OUT_DIR, f"{tag}_static.png")
        shutil.copyfile(keyed_paths[pick], dst)
        print(f"Übernommen: Kandidat {pick} → {dst}")
        print(f"Nächster Schritt (Animation):\n"
              f"  python tools/animate_walk.py {dst} {os.path.join(_OUT_DIR, tag + '_run.png')}")
    else:
        print("Kontaktblatt ansehen, dann finalisieren:\n"
              f"  python tools/sd_gen.py --name {tag} --pick <N>")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Lokaler SD-Standbild-Generator (ADR 037)")
    ap.add_argument("--name", help="Gegner-Name aus sd_style.SUBJECTS (z. B. skeleton_warrior)")
    ap.add_argument("--subject", help="freies Motiv (überschreibt die Tabelle)")
    ap.add_argument("--archetype", choices=list(sd_style.ARCHETYPE_PRESETS),
                    help="melee/swarm/ranged/tank/caster (sonst aus der Tabelle)")
    ap.add_argument("--candidates", type=int, default=sd_style.DEFAULT_CANDIDATES)
    ap.add_argument("--matte", choices=["magenta", "rembg"],
                    help="Freistell-Methode (sonst Archetyp-Default)")
    ap.add_argument("--ref", help="Stil-Referenzbild (IP-Adapter) für den Familien-Look")
    ap.add_argument("--ip-weight", type=float, default=sd_style.IP_ADAPTER_WEIGHT,
                    dest="ip_weight", help="Stärke der IP-Adapter-Stilreferenz (nur mit --ref)")
    ap.add_argument("--seed", type=int, default=sd_style.DEFAULT_SEED)
    ap.add_argument("--steps", type=int, default=sd_style.DEFAULT_STEPS)
    ap.add_argument("--cfg", type=float, default=sd_style.DEFAULT_CFG)
    ap.add_argument("--size", type=int, default=sd_style.DEFAULT_SIZE)
    ap.add_argument("--ckpt", default=_DEFAULT_CKPT, help="Checkpoint-Datei in ComfyUI")
    ap.add_argument("--pick", type=int, help="Kandidat-Index → final als <name>_static.png")
    ap.add_argument("--thresh", type=int, default=60, help="Magenta-Keying-Toleranz")
    ap.add_argument("--enclosed", action="store_true",
                    help="umschlossene BG-Taschen mitkeyen (Magenta-Matte)")
    ap.add_argument("--dry-run", action="store_true",
                    help="nur Prompt zeigen, kein ComfyUI nötig")
    ap.add_argument("--workflow", default=None,
                    help="Workflow-JSON in tools/workflows/ (Default: still_ipadapter mit --ref, "
                         "sonst still_txt2img)")
    a = ap.parse_args()
    generate_still(a.name, a.subject, a.archetype, a.candidates, a.matte, a.ref,
                   a.seed, a.steps, a.cfg, a.size, a.ckpt, a.pick, a.thresh,
                   a.enclosed, a.dry_run, a.workflow, a.ip_weight)

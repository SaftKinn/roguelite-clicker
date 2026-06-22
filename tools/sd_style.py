#!/usr/bin/env python3
"""Stil-Wahrheit für den lokalen SD-Standbild-Generator (ADR 037).

EIN Ort für alles, was den einheitlichen Tiny-Swords-Look ausmacht: Prompt-Prefix,
Negative-Prompt, die 15 Tier-Gegner-Motive und die Sampler-Defaults. `tools/sd_gen.py`
importiert nur von hier — so bleibt der Stil konsistent und ein neuer Gegner ist *ein*
Eintrag, kein verstreuter Prompt (Golden Rule 2: keine Magic Numbers im Code).

Quelle der Texte: `docs/sprite-prompts.md` (ADR 024). Einziger bewusster Unterschied:
Der Hintergrund ist hier **einfarbig Magenta `#FF00FF`** (statt nur „plain solid"), weil
unser lokales Freistellen (`tools/key_black_bg.py`) genau diesen Ton wegkeyt — siehe
Nutzer-Konvention „alle Sprite-Prompts: BG #FF00FF, kein Boden".
"""

# --- Stil-Bausteine (für ALLE Motive gleich) -----------------------------------------

# Look-Beschreibung 1:1 aus sprite-prompts.md (vor dem motiv-spezifischen Satz).
STYLE_PREFIX = (
    "2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, "
    "bold clean black outlines, soft cel shading, vibrant saturated colors, "
    "chunky rounded proportions, slight top-down side view facing RIGHT, "
    "full body standing on the ground with feet at the very bottom, "
    "single centered character, sharp crisp edges, high detail"
)

# Hintergrund-Klausel: erzwingt den keybaren Magenta-Ton, kein Boden, kein Schatten.
BG_CLAUSE = "plain solid magenta #FF00FF background, no ground, no shadow"

# Negative-Prompt 1:1 aus sprite-prompts.md (für ALLE 15 gleich).
NEGATIVE_PROMPT = (
    "background scenery, ground shadow, text, watermark, logo, multiple characters, "
    "blurry, realistic photo, 3d render, front view, facing camera, cropped limbs, "
    "extra limbs, floating weapons, motion blur"
)

# --- Sampler-Defaults ----------------------------------------------------------------

DEFAULT_SEED = 42          # fester Seed → reproduzierbar; --seed im CLI überschreibt
DEFAULT_STEPS = 30
DEFAULT_CFG = 7.0
DEFAULT_SIZE = 768         # quadratisch; SD 1.5 mag 512–768, Cartoon-Checkpoints 768 ok
DEFAULT_CANDIDATES = 6     # mehrere Kandidaten je Gegner → kuratieren statt Glück
IP_ADAPTER_WEIGHT = 0.5    # Stärke der optionalen Stil-Referenz (Familien-Look)

# --- Archetyp-Presets: kleiner motiv-übergreifender Feinschliff + Default-Matte -------
# `matte` = wie freigestellt wird: "magenta" (Ecken-Flood-Fill) oder "rembg" (inhaltsbasiert,
# für farbkritische Figuren wie die lila Lich-Robe, wo Magenta-Keying Figurteile fräße).

ARCHETYPE_PRESETS = {
    "melee":  {"hint": "dynamic battle-ready stance",        "matte": "magenta"},
    "swarm":  {"hint": "small, low and quick silhouette",    "matte": "magenta"},
    "ranged": {"hint": "clear ranged weapon readable",       "matte": "magenta"},
    "tank":   {"hint": "huge heavy imposing silhouette",     "matte": "magenta"},
    "caster": {"hint": "arcane glow, hovering pose",         "matte": "rembg"},
}

# --- Die 15 Tier-Gegner (Motiv + Archetyp) — Texte aus sprite-prompts.md --------------

SUBJECTS = {
    # Tier 1 — Untote / Knochen-Legion
    "skeleton_warrior": {"archetype": "melee", "subject": (
        "A skeletal warrior soldier, rusty iron sword and round wooden shield, "
        "tattered dark cloak, glowing eye sockets, bony armor plates.")},
    "bone_swarmling": {"archetype": "swarm", "subject": (
        "A small fast skeletal creature scuttling low, tiny clawed bones, "
        "glowing green eye sockets, lightweight and quick, hunched.")},
    "skeleton_archer": {"archetype": "ranged", "subject": (
        "A skeleton archer drawing a worn wooden bow, quiver of arrows on back, "
        "ragged grey hood, bony fingers nocking an arrow.")},
    "bone_colossus": {"archetype": "tank", "subject": (
        "A huge hulking bone giant fused from many skulls and ribs, massive heavy frame, "
        "towering and slow, cracked bones, dim red glow.")},
    "lich": {"archetype": "caster", "subject": (
        "A floating undead lich sorcerer, tattered purple robe, ornate skull crown, "
        "glowing magic staff, ghostly green aura, hovering above ground.")},
    # Tier 2 — Dämonen / Höllenbrut
    "imp_warrior": {"archetype": "melee", "subject": (
        "A red-skinned demon warrior, curved black horns, jagged obsidian blade, "
        "muscular, burning ember cracks glowing on the skin.")},
    "hellhound": {"archetype": "swarm", "subject": (
        "A small fast four-legged hellhound beast, fiery mane, glowing orange eyes, "
        "smoking paws, lean lunging pose.")},
    "demon_caster": {"archetype": "ranged", "subject": (
        "A demon fire-mage hurling a fireball, dark robe with molten orange runes, "
        "horned head, clawed hands wreathed in flame.")},
    "pit_brute": {"archetype": "tank", "subject": (
        "A massive armored demon brute, thick stone-like dark hide, huge fists, "
        "heavy spiked shoulder plates, towering and slow.")},
    "demon_summoner": {"archetype": "caster", "subject": (
        "A robed demon cultist summoner, glowing red summoning circle at the hands, "
        "horned bone mask, dark ceremonial robes, hovering slightly.")},
    # Tier 3 — Drachen-Brut / Schuppen
    "drake_warrior": {"archetype": "melee", "subject": (
        "A draconian dragon-man warrior, green scaled skin, plated steel armor, "
        "large curved sword, folded leathery wings, fierce reptilian face.")},
    "wyrmling": {"archetype": "swarm", "subject": (
        "A small fast baby dragon on stubby legs, tiny wings, bright glossy scales, "
        "glowing eyes, scuttling quickly, lizard-like.")},
    "drake_archer": {"archetype": "ranged", "subject": (
        "A draconian skirmisher breathing a small focused fire-bolt, scaled body, "
        "light leather armor, half-spread wings, lean.")},
    "scale_titan": {"archetype": "tank", "subject": (
        "A colossal armored dragon titan, massive thick overlapping scale plates, "
        "huge spiked tail, towering heavy frame, slow and mighty.")},
    "dragon_priest": {"archetype": "caster", "subject": (
        "A draconic high priest sorcerer, ornate horned headdress, flowing dark-gold robes, "
        "glowing arcane orb, draconic staff, hovering with energy.")},
}


def preset_for(archetype: str) -> dict:
    """Archetyp-Preset (hint + Default-Matte); unbekannt → 'melee' als sichere Vorgabe."""
    return ARCHETYPE_PRESETS.get(archetype, ARCHETYPE_PRESETS["melee"])


def resolve(name: str | None, subject: str | None, archetype: str | None) -> tuple[str, str]:
    """Motiv + Archetyp auflösen: bekannter `name` füllt beide aus SUBJECTS; freier
    `--subject`/`--archetype` überschreibt. Gibt (subject_text, archetype) zurück."""
    entry = SUBJECTS.get(name or "", {})
    subj = subject or entry.get("subject")
    arch = archetype or entry.get("archetype") or "melee"
    if not subj:
        raise ValueError(
            f"Kein Motiv für '{name}'. Bekannte Namen: {', '.join(sorted(SUBJECTS))}.\n"
            f"Oder ein freies Motiv via --subject \"...\" angeben.")
    return subj, arch


def build_prompt(subject: str, archetype: str) -> str:
    """Vollständigen Positive-Prompt zusammensetzen: Stil + Archetyp-Hint + Motiv + BG."""
    hint = preset_for(archetype)["hint"]
    subject = subject.strip()
    if subject and subject[-1] not in ".!?":   # freie Motive ohne Satzende glätten
        subject += "."
    return f"{STYLE_PREFIX}, {hint}. {subject} {BG_CLAUSE}."


if __name__ == "__main__":
    # Selbsttest ohne SD: zeigt den aufgelösten Prompt je Gegner (zum Prüfen der Texte).
    import argparse
    ap = argparse.ArgumentParser(description="Prompt-Vorschau (kein SD nötig)")
    ap.add_argument("name", nargs="?", help="Gegner-Name; leer = alle auflisten")
    a = ap.parse_args()
    names = [a.name] if a.name else sorted(SUBJECTS)
    for nm in names:
        subj, arch = resolve(nm, None, None)
        print(f"\n# {nm}  [{arch}]\n{build_prompt(subj, arch)}")

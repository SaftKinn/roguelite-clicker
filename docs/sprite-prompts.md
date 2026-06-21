# Sprite-Prompts (Leonardo.ai) — 15 Tier-Gegner

Bild-Generierungs-Prompts für die 15 reskinnten Tier-Gegner (ADR 024): 3 Wellen-Abschnitte
× 5 Archetypen, einheitlicher **Tiny-Swords-Stil**. Erzeugt werden **Einzel-Standbilder**;
`tools/animate_walk.py` baut daraus den Lauf-Strip (siehe unten). Die Prompt-Texte sind
bewusst **Englisch** (beste Bildqualität), Beschreibungen frei austauschbar.

## Leonardo-Einstellungen
- **Modell:** Leonardo Phoenix (kann Alpha) — alternativ Lightning XL
- **Seitenverhältnis:** 1:1 (quadratisch)
- **Transparenz:** „Transparency: Foreground" aktivieren — sonst auf flachem, einfarbigem
  Hintergrund generieren und danach „Remove Background" anwenden
- **Negative Prompt** (für ALLE 15 gleich, einmal eintragen):
```
background scenery, ground shadow, text, watermark, logo, multiple characters, blurry, realistic photo, 3d render, front view, facing camera, cropped limbs, extra limbs, floating weapons, motion blur
```

---

## Tier 1 — Untote / Knochen-Legion (Welle 1–50)

### 1. `skeleton_warrior` — Nahkämpfer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A skeletal warrior soldier, rusty iron sword and round wooden shield, tattered dark cloak, glowing eye sockets, bony armor plates.
```

### 2. `bone_swarmling` — Schwarm
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A small fast skeletal creature scuttling low, tiny clawed bones, glowing green eye sockets, lightweight and quick, hunched.
```

### 3. `skeleton_archer` — Fernkämpfer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A skeleton archer drawing a worn wooden bow, quiver of arrows on back, ragged grey hood, bony fingers nocking an arrow.
```

### 4. `bone_colossus` — Tank/Brecher
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A huge hulking bone giant fused from many skulls and ribs, massive heavy frame, towering and slow, cracked bones, dim red glow.
```

### 5. `lich` — Beschwörer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A floating undead lich sorcerer, tattered purple robe, ornate skull crown, glowing magic staff, ghostly green aura, hovering above ground.
```

---

## Tier 2 — Dämonen / Höllenbrut (Welle 51–100)

### 6. `imp_warrior` — Nahkämpfer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A red-skinned demon warrior, curved black horns, jagged obsidian blade, muscular, burning ember cracks glowing on the skin.
```

### 7. `hellhound` — Schwarm
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A small fast four-legged hellhound beast, fiery mane, glowing orange eyes, smoking paws, lean lunging pose.
```

### 8. `demon_caster` — Fernkämpfer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A demon fire-mage hurling a fireball, dark robe with molten orange runes, horned head, clawed hands wreathed in flame.
```

### 9. `pit_brute` — Tank/Brecher
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A massive armored demon brute, thick stone-like dark hide, huge fists, heavy spiked shoulder plates, towering and slow.
```

### 10. `demon_summoner` — Beschwörer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A robed demon cultist summoner, glowing red summoning circle at the hands, horned bone mask, dark ceremonial robes, hovering slightly.
```

---

## Tier 3 — Drachen-Brut / Schuppen (Welle 101–150)

### 11. `drake_warrior` — Nahkämpfer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A draconian dragon-man warrior, green scaled skin, plated steel armor, large curved sword, folded leathery wings, fierce reptilian face.
```

### 12. `wyrmling` — Schwarm
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A small fast baby dragon on stubby legs, tiny wings, bright glossy scales, glowing eyes, scuttling quickly, lizard-like.
```

### 13. `drake_archer` — Fernkämpfer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A draconian skirmisher breathing a small focused fire-bolt, scaled body, light leather armor, half-spread wings, lean.
```

### 14. `scale_titan` — Tank/Brecher
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A colossal armored dragon titan, massive thick overlapping scale plates, huge spiked tail, towering heavy frame, slow and mighty.
```

### 15. `dragon_priest` — Beschwörer
```
2D game enemy character, Tiny Swords art style, hand-painted fantasy cartoon, bold clean black outlines, soft cel shading, vibrant saturated colors, chunky rounded proportions, slight top-down side view facing RIGHT, full body standing on the ground with feet at the very bottom, single centered character, plain flat solid background, sharp crisp edges, high detail. A draconic high priest sorcerer, ornate horned headdress, flowing dark-gold robes, glowing arcane orb, draconic staff, hovering with energy.
```

---

## Workflow: vom Bild zum spielbaren Gegner

1. Bild in Leonardo erzeugen (Einstellungen oben), als **transparente PNG** speichern unter
   `assets/custom/<name>_static.png` (`<name>` = der Code-Tag über jedem Prompt, z. B. `lich`).
2. Lauf-Strip erzeugen (Preset je Archetyp):
   ```bash
   # Standard (Nahkampf / Fernkampf):
   python tools/animate_walk.py assets/custom/<name>_static.png assets/custom/<name>_run.png
   # Tank/Brecher (schwerer Stampf):
   python tools/animate_walk.py assets/custom/scale_titan_static.png assets/custom/scale_titan_run.png --bob 0.04 --squash 0.10
   # Beschwörer (schwebend, kein Stauchen):
   python tools/animate_walk.py assets/custom/lich_static.png assets/custom/lich_run.png --bounces 1 --squash 0
   # Schwarm (flink, mehr Wippen):
   python tools/animate_walk.py assets/custom/wyrmling_static.png assets/custom/wyrmling_run.png --bob 0.08
   ```
3. `python main.py` starten — der Gegner ersetzt automatisch seinen Fallback-Kreis. Kein
   Code-Change nötig (`sprite_loader.load_custom_enemy` lädt `<name>_run.png` über die
   `SPRITE_NAME`-Zuordnung in `game/enemy.py`).

**Wichtig:** Pose immer **nach RECHTS** blickend, **Füße ganz unten** im Bild (der Animator
verankert am Fußpunkt). Hovernde Gegner (Lich/Beschwörer) trotzdem mit sichtbarer Unterkante
zeichnen — das Schweben macht das `--bounces 1 --squash 0`-Preset.

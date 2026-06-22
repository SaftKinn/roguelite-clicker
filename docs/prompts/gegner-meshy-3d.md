# Gegner-Prompts (Leonardo) — schlankes, bewährtes Rezept

Format wie beim Boss-Kit, das super funktioniert hat: **einfacher Prompt, frontale
Ganzkörper-Heldenpose**, Leonardo Phoenix, Hintergrund danach lokal mit **`rembg`**
entfernen. Keine überladenen Spezial-Anweisungen — die haben mehr kaputtgemacht als gebracht.

## Workflow
1. **Leonardo Phoenix** (oder Lucid Realism), **Preset „3D Render" oder „None"** (NICHT
   „Illustration" → das wird Cartoon), **Hochformat 2:3 oder 3:4** (damit die Beine
   reinpassen), 4 Bilder, bestes wählen.
2. **Universal Upscaler** drüber (Creativity ~0.2) → die feine, realistische Schärfe
   wie im Referenzbild.
3. Hintergrund weg: `rembg i bild.png <SPRITE_NAME>_static.png` (offline, gratis).
4. Weiter: Meshy (Image-to-3D) **oder** `tools/animate_walk.py` für den 2D-Walk.

## Stil-Block (an jedes Subject anhängen)
```
digital 3D rendering, realistic detailed textures, single character standing upright, full body front view, whole body from head to feet visible including both legs and feet, strict orthographic front view, perfectly symmetrical frontal pose, a single full-body character holding only one single weapon, the entire body facing directly toward the camera with no rotation and no tilt, shoulders and hips squared straight to the camera, head facing straight forward, plain light gray background, soft lighting casting subtle shadows on the ground, centered composition, imposing presence, high detail, sharp focus
```

## Negative (für alle gleich)
```
three-quarter view, side view, profile view, turned to the side, angled pose, tilted body, leaning, contrapposto, hip tilt, twisted torso, rotated body, dynamic pose, looking away, cartoon, anime, flat 2d, painting, cel shaded, stylized, cropped, cut off, legs cut off, out of frame, multiple characters, two bows, multiple bows, duplicate weapon, two weapons, extra weapon, arrow in hand, nocked arrow, drawing the bow, hand holding an arrow, arrow on the bow, arrow on the bowstring, loaded bow, arrow attached to the bow, loaded crossbow, bolt loaded in the crossbow, two crossbows, multiple crossbows, multiple bowstrings, double bowstring, two bowstrings, tangled bowstring, extra strings, broken bowstring, floating bow, bow not in hand, dropped bow, bow lying on the ground, bow leaning against the body, bow separate from the hand, quiver on the hip, quiver at the side, oversized quiver, huge quiver, bulky equipment, string touching the body, bow on the left side of the frame, tail, extra limbs, deformed hands, extra fingers, missing fingers, ground plane, terrain, scenery, text, watermark, blurry, low quality
```

---

## Tier 1 — Untote / Knochen-Legion (Knochenweiß, giftgrüner Glow)
```
skeleton_warrior  → an undead skeleton warrior, bleached white bone, tattered grey loincloth, holding a short rusty sword,
skeleton_archer   → an undead skeleton archer, pale bone, a small compact leather quiver of crossbow bolts strapped to the upper back, holding a wooden crossbow with both bony hands across the front of the chest, the crossbow held horizontally so its full shape is clearly visible and not hidden behind the torso,
skeleton_lancer   → a tall heavy undead skeleton soldier, bleached bone, iron pauldrons, holding a long spear,
skeleton_monk     → an undead skeleton priest, bone body, tattered dark grey hooded robe, faint sickly green glow,
bone_colossus     → a massive hulking undead bone golem, oversized rib cage and broad shoulders, very bulky build,
lich              → an undead lich sorcerer, gaunt skeletal body, sickly green glow, ornate dark tattered mage robe, small bone crown,
bone_swarmling    → a small undead bone imp, pale green-tinged bone, small build,
```

## Tier 2 — Dämonen / Höllenbrut (Höllenrot, Glut-Orange)
```
imp_warrior   → a small red-skinned demon warrior, lean muscular body, small horns, holding a short jagged blade,
demon_caster  → a slender crimson demon sorcerer, ridged horns, dark infernal robe with glowing orange runes,
demon_lancer  → a tall heavily armored demon brute, charred black-and-red plate armor, large horns, holding a long infernal spear,
demon_monk    → a robed demon acolyte, deep crimson hooded robe, hooved feet, faint ember glow,
pit_brute     → a colossal hulking dark-red demon brute, enormous muscular shoulders and arms, stubby horns, very bulky build,
demon_summoner→ a tall pink-red demon summoner, ornate horned headdress, layered dark ceremonial robe with glowing accents,
hellhound     → SONDERBLOCK (Seitenansicht) ganz unten — Vierbeiner brauchen Profil + eigenen Negative
```

## Tier 3 — Drachen-Brut / Schuppen (Schuppengrün/Teal, Gold-Priester)
```
drake_warrior → a humanoid green-scaled dragon warrior, lizard-like head, holding a curved sword, sturdy build,
drake_archer  → a humanoid teal-scaled dragon archer, slender body, sharp snout, a small compact leather quiver of crossbow bolts strapped to the upper back, holding a wooden crossbow with both clawed hands across the front of the chest, the crossbow held horizontally so its full shape is clearly visible and not hidden behind the torso,
drake_lancer  → a tall heavily armored dragonkin soldier, thick bronze-green scale armor, holding a long halberd,
drake_monk    → a robed dragonkin priest, ornate ceremonial robe over teal scaled skin,
scale_titan   → a gigantic armored dragon titan, massive dark-teal scaled muscular body, heavy plated shoulders, very bulky build,
dragon_priest → a tall golden-scaled draconic high priest, horned crowned head, flowing gold-and-green ceremonial robe,
wyrmling      → SONDERBLOCK (Vierbeiner-Seitenansicht) ganz unten — auf allen vieren, Profil
```

---

## Beispiel komplett (skeleton_warrior)
**Positive:**
```
an undead skeleton warrior, bleached white bone, tattered grey loincloth, holding a short rusty sword, digital 3D rendering, realistic detailed textures, single character standing upright, full body front view, whole body from head to feet visible including both legs and feet, strict orthographic front view, perfectly symmetrical frontal pose, a single full-body character holding only one single weapon, the entire body facing directly toward the camera with no rotation and no tilt, shoulders and hips squared straight to the camera, head facing straight forward, plain light gray background, soft lighting casting subtle shadows on the ground, centered composition, imposing presence, high detail, sharp focus
```
**Negative:**
```
three-quarter view, side view, profile view, turned to the side, angled pose, tilted body, leaning, contrapposto, hip tilt, twisted torso, rotated body, dynamic pose, looking away, cartoon, anime, flat 2d, painting, cel shaded, stylized, cropped, cut off, legs cut off, out of frame, multiple characters, two bows, multiple bows, duplicate weapon, two weapons, extra weapon, arrow in hand, nocked arrow, drawing the bow, hand holding an arrow, arrow on the bow, arrow on the bowstring, loaded bow, arrow attached to the bow, loaded crossbow, bolt loaded in the crossbow, two crossbows, multiple crossbows, multiple bowstrings, double bowstring, two bowstrings, tangled bowstring, extra strings, broken bowstring, floating bow, bow not in hand, dropped bow, bow lying on the ground, bow leaning against the body, bow separate from the hand, quiver on the hip, quiver at the side, oversized quiver, huge quiver, bulky equipment, string touching the body, bow on the left side of the frame, tail, extra limbs, deformed hands, extra fingers, missing fingers, ground plane, terrain, scenery, text, watermark, blurry, low quality
```

---

## Vierbeiner — Seitenansicht (hellhound, wyrmling)
Vierbeiner gehören ins **Profil** (alle 4 Beine sichtbar, ideal für `animate_walk`).
Kopf blickt nach vorn in Laufrichtung, **nicht** in die Kamera. Eigener Negative
(der gemeinsame verbietet ja „side view")! Schwanz hier erlaubt (natürlich beim Tier).

**hellhound — Positive:**
```
a fierce four-legged demon hound, muscular canine body, glowing orange eyes and mane, digital 3D rendering, realistic detailed textures, single creature standing on all four legs, full body strict side profile view, complete side view from the left, the whole body and the head in profile facing to the left in the walking direction, all four legs and paws visible, head looking straight ahead in profile and not toward the camera, plain light gray background, soft lighting casting subtle shadows on the ground, centered composition, high detail, sharp focus
```

**wyrmling — Positive:**
```
a small young green dragon, compact four-legged scaled body, small wings folded against the back, digital 3D rendering, realistic detailed textures, single creature standing on all four legs, full body strict side profile view, complete side view from the left, the whole body and the head in profile facing to the left in the walking direction, all four legs and clawed feet visible, head looking straight ahead in profile and not toward the camera, plain light gray background, soft lighting casting subtle shadows on the ground, centered composition, high detail, sharp focus
```

**Negative (für beide Vierbeiner gleich):**
```
front view, facing the camera, looking at the camera, head turned toward the viewer, eye contact, three-quarter view, foreshortening, bipedal, standing on two legs, cartoon, anime, flat 2d, painting, cel shaded, stylized, cropped, cut off, legs cut off, out of frame, multiple characters, extra limbs, deformed paws, ground plane, terrain, scenery, text, watermark, blurry, low quality
```

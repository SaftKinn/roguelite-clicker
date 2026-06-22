# Shop-Symbole — Leonardo.ai-Prompts (kompletter Satz, 11 Stück)

Stil: **wie die vier vorhandenen Gruppen-Embleme** (`assets/custom/icon_red/blue/gold/white.png`)
— rundes, ziertes Metallrahmen-Wappen, farbige Email-Scheibe, zentrales Symbol, malerischer
Tiny-Swords-Look, weiche Schattierung, leichtes Inneres Glühen.

**Speichern als** `assets/custom/shop_icons/<id>.png` (Dateiname = die `id` in der Tabelle).
Liegt dort ein PNG, übernimmt es das Spiel automatisch (überschreibt das Interim-Icon).

**Bei jedem Prompt gleich (zum Anhängen):**
> `, ornate circular metal-framed emblem game icon, painterly Tiny Swords art style, soft
> shading, subtle inner glow, single centered subject filling ~80% of frame, solid flat
> magenta #FF00FF background, no ground, no drop shadow, crisp clean edges for cutout,
> high detail, 512x512`

Farb-Leitfaden je Gruppe (für den Rahmen/die Scheibe):
- **Schaden (rot):** warm red enamel disc, bronze-gold ornate frame
- **Verteidigung (blau):** deep blue enamel disc, polished steel-silver ornate frame
- **Geld (gold):** amber-gold enamel disc, gold ornate frame
- **XP (teal):** teal enamel disc, silver ornate frame

---

## Schaden (rot)

**`start_damage.png` — Startschaden**
> A single upright gleaming steel sword blade with a bright impact spark at the tip, warm red enamel disc, bronze-gold ornate frame + [Suffix]

**`start_attack_speed.png` — Start-Tempo**
> A feathered arrow streaking forward with sweeping white wind/speed lines, sense of rapid fire, warm red enamel disc, bronze-gold ornate frame + [Suffix]

**`start_bullet_size.png` — Start-Kugelgröße**
> One big glowing iron cannonball with a soft energy aura, oversized heavy projectile, warm red enamel disc, bronze-gold ornate frame + [Suffix]

**`start_lifesteal.png` — Start-Lebensraub**
> A steel sword piercing a glowing red heart with a few crimson droplets, life-drain vibe, warm red enamel disc, bronze-gold ornate frame + [Suffix]

**`doppelschuss.png` — Doppelschuss**
> Two parallel glowing arrows flying side by side, twin shot, warm red enamel disc, bronze-gold ornate frame + [Suffix]

---

## Verteidigung (blau)

**`start_hp.png` — Start-HP**
> A sturdy heraldic shield with a glowing red heart emblazoned at its center, vitality and protection, deep blue enamel disc, polished steel-silver ornate frame + [Suffix]

---

## Geld (gold)

**`coin_mult.png` — Münz-Meister**
> An overflowing leather money pouch spilling shiny gold coins, wealth multiplier, amber-gold enamel disc, gold ornate frame + [Suffix]

**`gold_boost.png` — Goldene Kugeln**
> A glowing golden cannonball wreathed by a few gold coins, golden ammunition, amber-gold enamel disc, gold ornate frame + [Suffix]

---

## XP (teal)

**`xp_mult.png` — Weisheit**
> An open glowing spellbook/tome with a radiant star rising from its pages, knowledge and wisdom, teal enamel disc, silver ornate frame + [Suffix]

**`free_rerolls.png` — Glückshand**
> A pair of white-and-gold lucky dice with a small green four-leaf clover, good-luck charm, teal enamel disc, silver ornate frame + [Suffix]

**`extra_card.png` — Vierte Karte**
> A fanned spread of four arcane cards, the fourth card glowing brightest, extra choice, teal enamel disc, silver ornate frame + [Suffix]

---

### Tipps für Leonardo
- Model: ein „Illustration/Concept-Art"-Preset; **Guidance ~7–8**.
- Wenn der Rahmen abgeschnitten wird: Motiv etwas kleiner anweisen (`fills ~70% of frame`).
- Magenta-BG (`#FF00FF`) macht das Freistellen sauber — siehe Regel
  `leonardo-magenta-bg-no-ground`. Danach PNG mit Alpha exportieren / Magenta entfernen.
- Für maximale Konsistenz alle 11 in **einem** Batch mit gleichem Seed-Stil erzeugen.

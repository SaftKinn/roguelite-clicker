# progress.md

Wo wir stehen, was als Nächstes kommt. Diese Datei ist die laufende Wahrheit über
den Projektzustand — am Ende jeder Session aktualisieren.

---

## Current focus

**Lokaler SD-Standbild-Generator — ADR 037 (2026-06-22).** Antwort auf „kannst du eine KI
bauen, die mir 2D-Asset-Sets generiert?". Geklärt im Dialog: Backend = **lokales Stable
Diffusion**; Umfang nach Nachfrage bewusst auf **NUR Standbilder** eingegrenzt (SD's starke
Seite), Animation bleibt bei `animate_walk`/3D-Prerender (ADR 036) — denn frame-genaue
Konsistenz ist SD's Schwäche. SD ersetzt also nur den **Bild-Schritt** (vorher Leonardo),
erzeugt `assets/custom/<name>_static.png` und rastet in den bestehenden Workflow
(`sprite-prompts.md` Schritt 1→2) ein. **Architektur:** ComfyUI läuft als **separater Prozess**
(bringt torch/CUDA mit), die Tools sprechen nur dessen HTTP-API auf `127.0.0.1:8188` an →
**Spiel bleibt torch-frei** (`python main.py` unverändert). Neu unter `tools/` (rein additiv,
kein Spielcode berührt): **`sd_style.py`** (Stil-Wahrheit: Prefix + Negative + 15 Motive aus
`sprite-prompts.md`, BG auf Magenta `#FF00FF` für Keying, Sampler-Defaults, `build_prompt/
resolve`), **`sd_comfy.py`** (dünner Client: `is_up/load_workflow/set_inputs/run`, Platzhalter-
Token-Ersetzung `%PROMPT%` etc., websocket- ODER History-Polling, `requests` lazy → dry-run
braucht es nie), **`sd_gen.py`** (Orchestrator + CLI: N Kandidaten → Freistellen via
`key_black_bg` Magenta ODER `--matte rembg` → Kontaktblatt → `--pick N` finalisiert),
**`workflows/still_txt2img.json`** (txt2img-Graph mit Tokens) **+ `workflows/still_ipadapter.json`**
(IP-Adapter-Stilreferenz: `--ref` schaltet automatisch darauf um, `%IPWEIGHT%`/`--ip-weight`,
KSampler-Modell aus der IPAdapter-Kette — braucht ComfyUI-Erweiterung `ComfyUI_IPAdapter_plus` +
IP-Adapter/CLIP-Vision-Modelle), **`requirements-sd.txt`** (leichte Deps, kein torch),
**`README-sd.md`** (Setup-Anleitung). `_sd_raw/` gitignored;
`*_static.png` war schon gitignored. **Verifiziert (ohne GPU):** `sd_style`/`sd_gen --dry-run`
lösen Prompts korrekt auf; `load_workflow`+`set_inputs` füllen alle Tokens typrichtig (seed=int,
cfg=float), `_comment` wird entfernt, jeder Node hat `class_type`; alle Tools `py_compile` sauber;
kein `game/`-Modul importiert torch/SD-Tools → Spiel unberührt. **Offen / Nutzer-Schritt:**
ComfyUI + Cartoon-Checkpoint + Tool-Deps auf der GPU-Maschine installieren (siehe `README-sd.md`),
dann echter End-to-End-Lauf für `skeleton_warrior` (A/B gegen vorhandenes Standbild); optional
IP-Adapter-Workflow für stärkeren Familien-Look; LoRA erst falls der Stil-Prompt nicht reicht.

---

**3D-Pre-Render-Walk für Tier-2-Boss — ADR 036 (2026-06-22).** Die offene ADR-035-Etappe
„echte Helden-Animationen" gelöst — aber **anders als geplant**. Am Tier-2-Boss reihum
durchgespielt und vom Nutzer als minderwertig verworfen: KI-Video (Ludo, matschig + erfand
Brust-Blitz + graues Schachbrett im MP4), prozedurales `animate_walk` („Wackeln"), Cutout-Rig
(scharf, aber Naht-Risse — flaches Bild kennt verdeckte Flächen nicht). **Gewinner: 3D-Pre-Render.**
Pipeline: **Meshy.ai** (image-to-3D, liefert auto-gerigtes GLB **inkl. Walking/Running/Attack/
Elbow_Strike** → Mixamo entfiel) → neues **`tools/blender_sprite_render.py`** (Blender 5.1
headless: GLB importieren, **orthographische Frontalkamera** an Bounding-Box gefittet, Film
transparent, EEVEE, Animations-Framebereich aus der Action → PNG-Sequenz; Flags `--test/--back/
--res/--frames-step`) → `tools/frames_from_clip.py … --bg none --frames 12` (transparent → kein
Keying, Fußpunkt-Anker) → **`assets/custom/tier2_boss_run.png`** (12 Frames). Loader zieht sie
automatisch (`SPRITE_NAME="tier2_boss"`), **null Spielcode-Änderung**. **Verifiziert im Spiel**
(F3 → Welle 60, Boss läuft scharf/lochfrei auf den Turm zu). 3D-Quellen `assets/custom/_meshy*/`
(~39 MB) **gitignored**, nur der Strip kommt ins Repo. Neuer Verifikations-Treiber
`.claude/skills/run-roguelite-clicker/driver_boss60.py` (F3→W60, Serien-Screenshots).
**Offen:** Tier-1/Tier-3 + 3 SuperBosse hängen noch am prozeduralen `animate_walk` → gleiche
Pipeline; Meshy-Attack-Clips ungenutzt (→ später `<name>_atk.png`); 12-Frame-Lauftempo im
echten Feel ungeprüft; KI-Mesh ≠ exaktes Leonardo-Artwork (weichere Texturen); Flügel-/Waffen-
Motive rigen beim Humanoid-Auto-Rig schlecht.

> **Separates Experiment (NICHT in diesem Repo):** Aus demselben Meshy-Modell wurde ein
> **Godot-3D-Projekt** (`C:\Users\kings\Desktop\Marshstalker3D\`) aufgesetzt — steuerbarer
> Charakter (WASD laufen, Shift rennen, Maus-Orbit-Kamera + Scroll-Zoom, Maus/Leertaste
> angreifen, 4K-Vollbild). Eigenes Spiel, eigener Ordner; berührt den Clicker nicht. Godot
> beim Nutzer noch zu installieren.

---

**FX-/„Juice"-Layer: Partikel + Treffer-Flash + Turm-Animation + Screenshake (2026-06-22) — ADR 035.**
Erster Schritt von „alles animieren, damit es professioneller aussieht". Vorab geklärt:
**keine Multi-Ansichten** nötig (Seitenansicht-Kamera, L/R-Flip wie Vampire Survivors) —
„professionell" kommt aus Bewegung + Wucht. Umgesetzt als lose `fx`-Liste in `main.py`
**parallel zu `dmg_numbers`** (nicht an `gs`, kein FXManager — spiegelt das vorhandene
`DamageNumber`/Monk-`_heal_effects`-Muster), Update an den 3 Sub-Tick-Stellen, Draw in
`world_surf` vor `blit_world_zoomed`. Neu in **`game/fx.py`**: `Particle`/`MuzzleFlash`/
`TrailDot` + Spawner (`spawn_death_poof/_muzzle_flash/_trail/_dust`), FX-Konstanten.
Effekte: **Death-Poof** (Kill-Schleife, Boss größer/farbig), **Treffer-Flash** (`Warrior.
_hit_flash` + `_apply_hit_flash` via `BLEND_RGB_ADD`-Kopie → kein Halo; in `_blit_sprite`
**und** allen Spezial-Frame-Blits Archer/Lancer/Monk/Boss/SuperBoss), **Turm-Animation**
(`player.py`: Idle-Puls, `trigger_recoil` an beiden Schussstellen, Overdrive-Glühen — reine
Transform/Tint), **Mündungsblitz** (Turm), **Projektil-Trail**, **Screenshake** (`balance.
SHAKE_*`, Boss-Tod, Offset im `blit_world_zoomed`, an allen 3 FX-Stellen abklingend).
**Verifiziert:** `py_compile` sauber; FX-Optik isoliert gerendert (Poof/Muzzle/Trail
korrekt fadend, Treffer-Flash mit erhaltener Silhouette, Turm Idle/Recoil/Overdrive
unterscheidbar); voller Treiber-Flow (Menü→Levelup→W150→Sieg) **mehrfach crashfrei**;
Overdrive-Turm-Glühen im Live-Combat-Screenshot bestätigt. Betroffen: `game/fx.py`,
`game/enemy.py`, `game/player.py`, `game/balance.py`, `main.py`. **FX-Layer committet `5e1f8d0`**
(Hook bündelte ihn mit der bereits im Tree liegenden Audio-/Shop-Icon-Arbeit).

**Folge-Arbeit dieselbe Session:**
- **Lauf-Staub** ergänzt (Etappe 6): `Warrior._stepped`/`_step_tick` (gesetzt im Bewegungszweig,
  `_DUST_EVERY=16`), `main.py` liest das Flag nach `e.update(pc)` → `fxmod.spawn_dust` an den
  Füßen. Gegner-Muzzle-Fallback bewusst weggelassen (Sprite-Muzzle deckt alle 6 Fernkämpfer ab).
- **KI-Frame-Pipeline gebaut** (statt nur geplant): **`tools/frames_from_clip.py`** wandelt einen
  echten KI-Bewegungsclip (GIF/animiertes WEBP/APNG, Bilderordner, `--grid`-Standbild oder Video
  via optionalem `imageio`) in das Strip-Format von `_load_custom_strip`: je Frame Magenta-Keying
  (Ecken-Flood-Fill wie `key_black_bg.py`), zuschneiden, **gemeinsame Skalierung** aus der größten
  Content-Höhe (kein Größen-Springen) + Fußpunkt-Verankerung → `cell·N × cell`-Strip. `--frames N`
  tastet ab. Workflow-Doc **`docs/ki-frame-pipeline.md`**. **Verifiziert:** synthetisches Magenta-GIF
  → Strip 1024×128 (8 Frames), Keying transparent, **echter Loader liest 8 Frames + Flip**.
**Offen:** der Nutzer erzeugt die echten KI-Clips (Leonardo Motion o. ä.) für Helden-Motive
(Turm, 6 Bosse, Signatur-Gegner) und füttert sie durch das Tool — **kein Code mehr nötig**.
Hintergrund-Animation zuletzt. FX-Tuning (Partikelzahl/Shake-Amplitude) ungeprüft im echten
Lauf-Feel.

---

**Audio-Pipeline für echte SFX + zwei neue Musik-Tracks (2026-06-22).** `game/sounds.py`
auf einen daten­getriebenen SFX-Loader umgestellt: `_SFX_FILES` (dict name→Dateiname) +
`_SFX_DIR`; die `__init__`-Schleife lädt jede vorhandene Datei aus `assets/audio/sfx/` und
überschreibt den prozeduralen Default, fehlt sie bleibt der synthetisierte Klang (Golden
Rule 5). **Zehn SFX-Slots** sind damit für echte ElevenLabs-Dateien vorbereitet:
`shoot/hit/kill/kill_tanker/wave_clear/overdrive/game_over/boss_intro/kill_boss/kill_superboss.ogg`
(plus bestehende `shop_buy.ogg`, `zipclick.flac`). Zwei neue Musik-Methoden:
`start_victory_music()` (Pfad `Music/Victory.ogg`) + `start_shop_music()` (`Music/Shop.ogg`).
**Verdrahtung in `main.py`:** Sieg (W150 geräumt) ruft `start_victory_music()`; Eintritt in
den **IMPROVEMENTS**-Meta-Shop ruft `start_shop_music()`, „Zurück" stellt Menü-Musik wieder
her. Bewusst **nicht** an den In-Run-`UPGRADE`-Karten-Pick gehängt (feuert pro Levelup →
ständiger Track-Neustart wäre störend). Alles über `_play_music`-Fallback: fehlt eine
Track-Datei, ist der Aufruf ein No-Op (kein Crash, Menü-/Run-Musik läuft weiter).
**Verifiziert:** `py_compile` sauber + voller Headless-Treiber-Flow bis VICTORY ohne
Fehler (Victory-Musik-Aufruf dispatcht). **Offen:** der User generiert die 10 SFX +
`Victory.ogg`/`Shop.ogg` in ElevenLabs (Prompts geliefert); ElevenLabs liefert MP3 →
für SFX (`mixer.Sound`) nach **.ogg/.wav konvertieren** (ffmpeg), dann liegen sie nur noch
im Ordner. **Noch nicht committet.**

---

**Shop-Symbole + restliche UI-Klicks (2026-06-22).** Jeder Shop-Slot zeigt jetzt links
ein 50px-Symbol. Neuer Loader `ui_loader.draw_shop_icon(entry_id, group, …)` mit
Auflösungskette: `assets/custom/shop_icons/<id>.png` (Override) → registrierte Pack-Quelle
(`_SHOP_ICON_SRC`) → Gruppen-Emblem `icon_<group>.png` → nichts (Golden Rule 5).
Pack-Mapping: Schwert/Schild/Geldsack/Buch (`icon_red/blue/gold/white`), `Cannonball.png`
(Kugelgröße), Tiny-Swords-Icons 03/04/05/08. `_draw_slot` um `entry_id`+`group` erweitert,
Text um Icon-Breite nach rechts gerückt. **3 echte Lücken** (Start-Tempo, Glückshand, Vierte
Karte teilen sich Interim-Icons) → Leonardo-Prompts in `docs/shop_icon_prompts.md` (Stil an
4 Gruppen-Emblemen, Magenta-BG). Asset-Suchregel als Memory `asset-search-folders`.
Außerdem `ui_click` ergänzt für **Shop-Zurück**, **Lauf-Starten**, **Quit** (Quit mit
`pygame.time.delay(140)`, damit der Klick vorm Schließen hörbar bleibt). **Verifiziert:**
headless Shop-Render (`shots/_shop_icons.png`, alle 11 Slots mit Icon) + `py_compile`.
**Noch nicht committet.**

---

**Klicksound `zipclick` + Shop-Kaufsound (2026-06-22).** UI-Klick: externer Master
`…\sounds\zipclick.flac` → `assets/audio/sfx/zipclick.flac`, ersetzt im `SoundManager`
den prozeduralen `ui_click`-Slot (Load mit `os.path.exists` + `try/except`; fehlt die
Datei, bleibt der prozedurale Sinus → Golden Rule 5). **Nur ein Klick gleichzeitig:**
`play("ui_click")` merkt sich den von `Sound.play()` zurückgegebenen Channel und ruft
beim nächsten Klick `stop()`, falls noch `get_busy()` → schnelle Klicks überlagern sich
nicht. Datei-Load läuft jetzt über eine Schleife `(("shop_buy", …), ("ui_click", …))`.
**Verifiziert:** headless Load (beide im Dict, `ui_click` ist die längere Datei),
Doppel-`play` ohne Crash, `py_compile`. **Noch nicht committet.**

---

**Shop-Kaufsound (2026-06-22).** Externer Master `aselfmade assets\rougelite clicker
assets\sounds\shop_buysound.ogg` → kopiert nach `assets/audio/sfx/shop_buy.ogg` (erste
**echte** SFX-Datei; alle anderen Effekte sind prozedural). `SoundManager.__init__` lädt
sie lazy mit `os.path.exists`-Guard + `try/except pygame.error` → fehlt sie, bleibt der
Slot leer und `play("shop_buy")` ist No-Op (Golden Rule 5). Trigger über das vorhandene
Rückgabe-Signal-Muster: `ImprovementsMenu.handle_click` gibt bei erfolgreichem Kauf jetzt
`"bought"` zurück (statt `None`); `main.py` (State `IMPROVEMENTS`) spielt darauf
`snd.play("shop_buy")` — Audio bleibt in der Game-Loop zentralisiert. **Verifiziert:**
headless `SoundManager`-Load (`shop_buy` im Dict, `play` ohne Crash) + `py_compile` der
drei geänderten Module. **Noch nicht committet.**

---

**Bild-Hintergrund im Hauptmenü (2026-06-22).** Leonardo-Key-Art (Turm auf Hügel, Sonnenuntergang,
drei Tier-Reiche am Horizont) als `assets/custom/menu_bg.png` (1280×720, aus externem Master
`aselfmade assets\rougelite clicker assets\cover\` via Pillow/System.Drawing skaliert). In
`game/theme.py` die Vignette in `_build_vignette()` ausgelagert und zwei Primitive ergänzt:
`vignette()` (Overlay über ein Bild) + `top_scrim()` (dunkles Verlaufsband oben, hebt den
Gold-Titel ab; Default frac 0.42 / alpha 160). `MainMenu` lädt das PNG lazy (`_load_bg`,
`_bg_surf`) und zeichnet **nur im Hauptmenü** Bild → Vignette → Titel-Scrim, mit **Fallback** auf
`theme.backdrop` (Golden Rule 5). Andere Screens behalten den prozeduralen Verlauf. **Verifiziert:**
direkter `MainMenu.draw`-Render headless → Bild/Titel/Buttons sauber (`shots/menu_bg_test.png`).
Neue Memory-Regel für Szenen-/Menü-Hintergrund-Prompts angelegt. **Offen:** ggf. Scrim-Stärke
nachschärfen, falls „CLICKER" über dem hellsten Himmel zu schwach wirkt. **Noch nicht committet.**

---

**Overdrive — erste aktivierbare Spieler-Fähigkeit (2026-06-22) — ADR 034.** Gegen den rein
passiven Auto-Combat (ADR 010, offene Genre-Frage „woher kommt aktive Spannung?"): **Leertaste**
zündet einen 5-s-Burst mit **×2 Angriffstempo + ×1.5 Schaden**, danach 18 s Cooldown (ab
Aktivierung → 13 s echte Abklingzeit). Umsetzung minimal-invasiv: zwei Timer in `gs`
(`overdrive_active`/`overdrive_cd`, Ticks aus Sekunden × Live-FPS, **pro Sub-Tick** dekrementiert
→ FPS- **und** Zeitraffer-stabil wie `fire_timer`); Auslöser im KEYDOWN-Block; Effekt als reiner
Multiplikator an genau zwei Stellen (`attack_speed × od_atk` beim `fire_timer`-Reset +
`spawn_projectiles(..., damage_mult=od_dmg)`, neuer Default-Param 1.0 → **keine** persistente
`stats`-Mutation). HUD-Balken oben mittig (orange=aktiv / grau=lädt / grün=bereit), Werte in
`balance.OVERDRIVE_*`, eigener prozeduraler Sound `"overdrive"`. CONTROLS-Screen + Treiber
(Leertasten-Schritt `02b_overdrive.png`) nachgezogen. **Verifiziert:** voller Flow crashfrei,
Balken-Wechsel grün→orange im Screenshot. **Offen:** Balance (5/18 s, ×2/×1.5) ungetestet — das
Boss-DPS-Modell kennt Overdrive noch nicht. **Noch nicht committet.**

---

**UI-Redesign „Glass-Hybrid" + zentrales Theme-Modul (2026-06-22) — ADR 033.** Das ganze
Front-End wurde von flach-gezeichnet auf einen modernen, kohärenten Look gehoben. Neu:
**`game/theme.py`** als einzige Quelle des UI-Looks — Palette + gecachte „Glass"-Primitive
(`backdrop`+Vignette, `panel` mit Verlauf/Highlight, `drop_shadow`/`accent_glow` via
smoothscale-Blur, `text`/`text_center` mit Schatten, `pill`, `font` mit optionaler
Display-TTF, Fallback Arial). Die geteilte **`Button`-Klasse** (`main_menu.py`) nutzt sie →
**alle** Menü-Buttons gehoben an einer Stelle. Umgestellt: Hauptmenü (Backdrop, Logo-PNG mit
Fallback, Münz-/Rekord-Pills), Shop (Glass-Slots + Gruppen-Chips), Level-up-Karten (Glass +
Schatten/Glow, **4 Gruppen-Icons** statt 2 geteilte, Fallback auf Tiny-Swords-Icons),
Slot-Auswahl, Optionen, Lexikon, sowie In-Game-Overlays (Pause/Game-Over/Sieg/„Welle
geschafft" als zentrierte Glass-Card mit Glow-Titel). Gruppen-Farben bleiben in `balance.py`.
**Verifiziert:** Headless-Renders aller Screens + voller Treiber-Flow (Slot→Menü→PLAYING→
F7-Karten→Sieg) **crashfrei**. **5 Leonardo-PNGs jetzt eingebaut** (Wappen + 4 Gruppen-Icons,
Master extern, via Pillow tight-cropped + Icons quadratisch zentriert → `assets/custom/
menu_logo.png` + `icon_{red,blue,gold,white}.png`): Hauptmenü zeigt das Wappen über dem
Schriftzug (Logo per Höhe+Breite-Box skaliert, Buttons tiefer), Karten zeigen je Gruppen-Icon.
Live-Loop bestätigt. **Display-TTF jetzt drin:** Cinzel (OFL, Variable-Font Regular/Bold/Black)
unter `assets/fonts/Cinzel.ttf` (+ `OFL.txt`); `theme._find_display_font()` greift sie zur
Importzeit → alle 8 `display=True`-Titel rendern in Roman-Versalien statt Arial (Menü- und
Level-up-Titel im Screenshot bestätigt). **Kein Code nötig** (Wiring stand schon).
**Noch nicht committet** (Icons/Logo/Font sind tracked — nicht von der `*_static/_shot/_cast`-
gitignore-Regel erfasst, wie die Tier-Böden).

---

**Dev-Controls umbelegt + Unverwundbarkeit (2026-06-22).** Dev-Tasten neu, damit man
gezielt jede Boss-Welle testen kann: **F1–F6** springen zu W10/50/60/100/110/150
(`DEV_WAVE_KEYS`-Dict in `main.py`, einheitlicher Sprung „Ziel−1 + Clear erzwingen"),
**F7** = Levelup erzwingen (war F5), **F8** = alle Gegner töten (war F1), **U** =
Unverwundbarkeit an/aus (`player.invuln`: early-return in `Player.take_damage` + Guard am
Boss-Oneshot in `check_enemy_contact`; grüner „UNVERWUNDBAR"-Indikator unten links).
CONTROLS-Overlay + CLAUDE.md + Skill-`driver.py` (Levelup→F7, Sieg-Flow F6→F8) nachgezogen.
**Verifiziert:** DEV_WAVE_KEYS-Mapping + Invuln (take_damage & Oneshot geblockt) per Unit-Test;
voller Treiber-Flow crashfrei (F7→Karten „Ausweichen", F6→F8→SIEG Welle 150). Dev-only, kein ADR.

---

**Eigene Boss- & SuperBoss-Sprites pro Tier (2026-06-22) — ADR 032.** Alle 6 Endgegner
haben jetzt eigene Leonardo-Sprites (frontale Pose, transparent freigestellt):
- **Reguläre Bosse** (alle 10 Wellen): `Tier1Boss`/`Tier2Boss`/`Tier3Boss` (`enemy.py`) setzen
  `SPRITE_NAME` → `assets/custom/tier{1,2,3}_boss_run.png`; `Boss` ist tier-fähig gemacht
  (`SPRITE_NAME`/`SPRITE_PX`-Felder, `_load_sprites`-Verzweigung, Black-Lancer als Fallback).
  Spawn via neuer Liste `TIER_BOSS` in `main.py` (statt pauschal `Boss(...)`).
- **SuperBosse:** `UndeadSuperBoss`/`DemonSuperBoss` greifen automatisch (`SPRITE_NAME` war schon
  gesetzt). `DragonSuperBoss` von Seitenansicht **auf frontalen `dragon_boss` umgestellt** (alter
  Seitenansicht-Drache bleibt als `SPRITE_NAME=None`-Fallback).
- **Animation:** `tools/animate_walk.py` → 8-Frame-Walk je Boss; geflügelte SuperBosse mit
  `--fill 0.80-0.82 --tilt 1.2` (extra Rand gegen Flügel-Clip), reguläre `--fill 0.86 --tilt 2.0`.
- **Flügel-Crop gelöst im Prompt:** Motiv ~40-45 % der Leinwand + Flügel angelegt (Memory
  `leonardo-winged-boss-framing`). **Verifiziert:** alle 6 laden 8 Frames, Render-Montage korrekt
  (`shots/boss_*.png`), Live-Flow W10/50/150 crashfrei. Master-`*_static.png` bleiben extern.

---

**Boden-Schärfe + Lancer/Monk-Reskins (2026-06-22) — ADR 030/031.**
- **Boden scharf (ADR 031):** Der 1,4×-Kamera-Zoom hatte die Boden-Textur hochskaliert → leicht
  unscharf. Jetzt wird der Boden **nativ direkt auf `screen`** gezeichnet, nur die Gameplay-Ebene
  (`world_surf`, jetzt **SRCALPHA**) liegt gezoomt drüber (`blit_world_zoomed` blittet alpha-erhaltend
  statt in den Screen zu schreiben). Texturen auf exakt **1280×720** re-importiert, `load_tier_background`
  gibt 1:1 zurück (kein Runtime-Resample). Verifiziert: `02_playing.png` sichtbar schärfer, Flow crashfrei.
- **Lancer/Monk-Reskins (ADR 030):** tanker/monk sind jetzt **pro Tier reskinbar** (im `TIER_ROSTER`,
  Spawn-Sonderfall entfernt). `_LancerReskin`/`_MonkReskin` tauschen **nur die Lauf-Frames**, behalten
  die Spezial-Animationen, und fallen ohne PNG auf das **Original** zurück (keine Regression). **6 PNGs
  fehlen:** `skeleton_lancer`, `skeleton_monk`, `demon_lancer`, `demon_monk`, `drake_lancer`, `drake_monk`
  (je `_run.png`, extern via Leonardo, Magenta-BG). Verifiziert: Spawn-Mapping je Tier korrekt, Caches
  getrennt, 300 Spawns crashfrei.

---

**Tier-Boden-Texturen drin (2026-06-22) — ADR 029.** Jedes 50-Wellen-Tier hat jetzt eigenen
Boden: Tier 1 Friedhofspflaster, Tier 2 Lava-Basalt, Tier 3 Eis-Schiefer (Leonardo, Top-Down,
Tiny-Swords-Stil). Voll-Textur **bildschirmfüllend gebacken** (COVER+Crop, keine Naht) statt
Kachel-Raster — die Bilder sind zusammenhängende Szenen, kein gleichmäßiges Tileset.
`sprite_loader.load_tier_background(tier,size)` lädt `assets/custom/tier{1,2,3}_ground.png`;
`Terrain(tier=…)` skippt im Tier-Modus die Tiny-Swords-Decos (Textur bringt Knochen/Lava/Kristalle
selbst mit), Fallback auf Gras+Decos bleibt. Biom-Wechsel im `WAVE_CLEAR` gegen den geladenen
`terrain.tier` geprüft (robust auch bei Dev-Sprüngen). **Verifiziert** (Renders je Tier, In-Game
`02_playing.png`, voller Treiber-Flow crashfrei). Offen: 3× 1280²-PNG im Repo; Tier-3-Schneerand
sichtbar (als Arena-Rand akzeptiert).

---

**Playtest läuft (2026-06-22) — zwei Fixes eingespielt, Balance der neuen XP-Kurve offen.**
- **Necromancer/Lich-Soft-Lock behoben (D40):** Beschwörer kitete auf `ATTACK_RANGE = 240`,
  knapp JENSEITS der Turm-Reichweite (~236 px) → unerreichbar, sobald letzter Gegner + `SUMMON_MAX`
  erreicht (Spieler meldete „hört auf zu beschwören UND Turm greift nicht mehr an" = Soft-Lock).
  Fix: `ATTACK_RANGE → 220` + **Übergangs-Pfeilangriff** (`SHOOT_EVERY = 110`, `pop_shots()`, reicht
  via `EnemyProjectile(..., sprite=SPRITE_NAME)` sein eigenes Geschoss-Sprite mit, ADR 027). Vererbt
  sich auf alle Tier-Summoner via `_CustomSummoner`; `main.py` sammelt die Pfeile im Necro-Zweig.
- **XP-Kurve quadratisch (ADR 028):** `xp_to_next = 8 + 1.0·(level-1)² + 10·wave` (war linear
  `+7/Stufe +2/Welle`). **Level 100 ≈ 10000 XP** (war ~850), Modell-Endlevel **~72/Lauf** (war ~195,
  194 → 71 Levelups). Bewusster Tradeoff (Option A, vom Nutzer gewählt): „10000@100" und „bis Level
  100 kommen" schließen sich beim XP-Budget (~161.800) aus → Level 100 wird Fernziel. **Noch nicht im
  echten Lauf getestet** — Hebel `XP_PER_LEVEL_SQ` (↓ = mehr Level); Wechselwirkung mit Boss-DPS-Wand.

---

**Fernkämpfer-Geschosse: eigenes Sprite je Schütze + Mündungs-Flash — ADR 027.**
Code-Wiring steht UND **alle 12 PNGs importiert** (Leonardo.ai, freigestellt via
`key_black_bg`, die 6 Pfeile via `tools/rotate_flat.py` nach rechts ausgerichtet — neues
Tool, `--auto` PCA-Geradezug + `--flip`). In `assets/custom/`. Verifiziert: alle 6
Geschoss-Sprites + 6 Cast-Flashes laden (kein Goldpfeil), Geschosse zeigen nach rechts,
voller Treiber-Flow crashfrei. Bisher feuerten
alle Fernkämpfer denselben Goldpfeil; jetzt reicht jeder Schütze sein `SPRITE_NAME` ans
`EnemyProjectile` (`sprite=getattr(self,"SPRITE_NAME",None)`), das daraus
`assets/custom/<name>_shot.png` (Geschoss, rotiert zur Flugrichtung) + `<name>_cast.png`
(Mündungs-Flash, an die Projektil-Lebenszeit gekoppelt, fadet über `MUZZLE_TICKS=7`)
lädt. Loader `sprite_loader.load_enemy_shot`/`load_enemy_muzzle`. **`main.py`
unangetastet.** Fallback-Kette: eigenes Sprite → Goldpfeil → Kreise (Golden Rule 5,
verifiziert: voller Treiber-Flow crashfrei ohne PNGs). Betroffen: die **6 spawnenden
Tier-Fernkämpfer** (`skeleton_archer`, `lich`, `demon_caster`, `demon_summoner`,
`drake_archer`, `dragon_priest`). **Prompt-Kit** (2 Stil-Blöcke + Negative + je 6
`_shot`/`_cast`-Zeilen) im Plan-File `ich-m-chte-f-r-die-twinkling-candy`.

**Davor — Gegner-Roster-Erweiterung (Tier-System) + Welle 150 — ADR 024.** Gameplay-
Grundgerüst steht (jetzt **Wellen 1–150**, Sieg, XP/Level, Karten, Shop, Elites, Meta-Gate
ADR 018). Diese Session kam die **15-Gegner-Tier-Welle** dazu:
- **3 Wellen-Tiers × 5 Archetypen = 15 reskinnte Gegner** (ADR 024): Tier 1 Untote (W1–50),
  Tier 2 Dämonen (W51–100), Tier 3 Drachen-Brut (W101–150). Erben die Mechanik der 5 Rollen-
  Klassen (`Warrior/Goblin/Archer/OrcBerserker/Necromancer`) via `_CustomSpriteMixin`,
  tauschen nur Optik. `TIER_ROSTER` + `tier_for_wave` in `main.py` wählen die Klasse je Tier;
  **Rollen-Spawn-Gewichte unverändert**. `tanker`(Lancer)/`monk`(Monk) bleiben Original.
  `Necromancer.SUMMON_CLASS`-Hook → Beschwörer rufen ihren Tier-Schwarm.
- **Welle 150** (`WIN_WAVE 100→150`); SuperBoss bei 50/100/150; Siegestext + Dev-Taste **F4**
  jetzt `WIN_WAVE`-abgeleitet statt hartkodiert.
- **Lexikon-Scroll:** 24 Einträge → Mausrad-Scrolling in `BestiaryMenu` (Kopf-/Fußband-Maske,
  Sichtfenster-Cull). Neue Tier-Einträge mit Wellen-Label (z. B. „Nahkämpfer · W101–150").
- **Sprite-Workflow:** PNGs entstehen extern (Leonardo.ai) als **Einzel-Standbild** →
  `tools/animate_walk.py` → `assets/custom/<name>_run.png`. Generischer Loader
  `sprite_loader.load_custom_enemy`. **Prompt-Kit** liegt im Plan-File `ich-will-mehr-png-s-*`.

**Bekannte Risiken/offene Fragen:** (a) **15 PNGs sind jetzt da** (Leonardo.ai, freigestellt via
`key_black_bg --enclosed`, animiert, committet `2c7b856`) — Lexikon rendert 24/24 fehlerfrei.
Rest: viele Posen eher frontal statt strikt Seitenprofil (beim Spiegeln unkritisch). (b) **W101–150
ungetestet-balanciert** — HP-Formel skaliert weiter, könnte HP-Wand statt DPS-Rennen werden;
Hebel `ENEMY_HP_PER_WAVE_SQ`/Tier-3-Härte. (c) **Originale Warrior/Archer/Goblin/Orc/Necro spawnen
nicht mehr direkt** (nur Basisklasse + Summon-Default), bleiben aber im Lexikon. (d) FPS 140 ist
frame-basiert (~1,87× schneller als 75); Zeitraffer x20 = Sound-Kakofonie (akzeptiert). (e) echter
1→150-Playtest steht aus. (f) Parallel-Session editiert dieselben Dateien — Tree teils gemischt.
(g) **Karten-Farbgruppen + Shop-Ausbau sind drin (ADR 025/026), aber balance-ungetestet** — die
%-Werte (Lifesteal/Armor/Dornen/Dodge, Coin-/XP-Mult) und neuen Shop-Preise brauchen einen Playtest,
v. a. Defensiv-Build (Armor+Dodge+Regen+Dornen) gegen die Endgame-Wand. Neue Karten teilen sich noch
`Icon_05/06` (eigene Icons fehlen).

## Last session

2026-06-22 (Teil 23) — **Meshy-3D-Gegner-Prompt-Kit + Beleuchtung in den Backlog:**
- **`docs/prompts/gegner-meshy-3d.md`** angelegt: fertige Leonardo-Prompts für alle 21 Gegner als
  **Input-PNG für Meshy.ai (Image-to-3D)**, anschließend ADR-036-Pipeline (GLB → Blender → Strip).
  An das Roster (`enemy.py`) verankert: Tier-Farben + Proportionen je Rolle. Look-Profil =
  **realistischer 3D-Render** (aus einem vom Nutzer favorisierten Referenzbild abgeleitet), nicht
  Cartoon; 19 Gegner **frontal**, 2 Vierbeiner (hellhound/wyrmling) in **Seitenansicht** mit eigenem
  Negative. Archer tragen jetzt **Armbrust** (zweihändig vorm Körper — umgeht Bogen/Sehne/Links-
  Rechts-Bugs). Pipeline-Settings: Phoenix · „3D Render" · Hochformat 3:4 · Guidance 8 · Universal
  Upscaler · `rembg`.
- **Prompt-Erkenntnisse** als Memory `leonardo-prompt-techniken` festgehalten (Vollbild=Hochformat,
  Verneinung nur im Negative, Hand über Bildseite, kein „reference sheet", Pose=Auswahl-Problem).
- **Beleuchtung im Spiel** als geplantes Feature in den neuen Abschnitt „Geplante Features / Backlog"
  aufgenommen (additive 2D-Light-Layer im Geist von ADR 035, noch kein ADR).
- Kein Spielcode berührt; reine Doku/Asset-Workflow-Arbeit.

2026-06-22 (Teil 22) — **Lokaler SD-Standbild-Generator (ADR 037):**
- Auf „kannst du eine KI bauen, die 2D-Asset-Sets generiert?" im Dialog Scope geschärft:
  Backend **lokales Stable Diffusion**, bewusst **nur Standbilder** (SD-Stärke), Animation
  bleibt `animate_walk`/3D-Prerender (ADR 036). SD ersetzt nur den Bild-Schritt (vorher Leonardo).
- **ADR 037** geschrieben (Abgrenzung zu 036: 036 = Animation, 037 = Bild-Erzeugung).
- Neu unter `tools/` (additiv, kein Spielcode): `sd_style.py` (Stil/Prompt-Wahrheit, 15 Motive),
  `sd_comfy.py` (ComfyUI-HTTP-Client, Token-Ersetzung), `sd_gen.py` (Orchestrator + CLI:
  Kandidaten → Freistellen → Kontaktblatt → `--pick`), `workflows/still_txt2img.json`,
  `requirements-sd.txt`, `README-sd.md`. ComfyUI als separater Prozess → **Spiel bleibt torch-frei**.
- **Verifiziert ohne GPU:** Prompt-Auflösung + `--dry-run`, Token-Füllung typrichtig, Workflow-
  Nodes valide, `py_compile` sauber, kein `game/`-Import von torch/SD-Tools. Echter Lauf =
  Nutzer-Schritt (ComfyUI-Setup, siehe Next concrete step).

2026-06-22 (Teil 21) — **3D-Pre-Render-Walk für Tier-2-Boss (ADR 036):**
- **Vier Animations-Wege am Tier-2 durchprobiert**, drei vom Nutzer als minderwertig verworfen
  (KI-Video/Ludo matschig + Blitz-Ende; prozedurales „Wackeln"; Cutout-Rig mit Naht-Rissen) →
  Entscheidung **3D-Pre-Render** (klassisch „pre-rendered", DKC/Diablo).
- **`tools/blender_sprite_render.py`** (neu): Blender-headless rendert ein animiertes GLB als
  transparente Frontal-Sprite-Sequenz (Ortho-Kamera an BBox gefittet, EEVEE, `--test/--back/
  --res/--frames-step`). Quelle = Meshy.ai-GLB (auto-gerigt, Walking/Attack/… fertig).
- **Pack-Schritt** über bestehendes `frames_from_clip.py … --bg none --frames 12` → `assets/
  custom/tier2_boss_run.png` (12 Frames). Loader unverändert (`SPRITE_NAME`), kein Spielcode.
- **`.gitignore`:** `assets/custom/_meshy*/` (3D-Quellen ~39 MB) raus; nur der Strip ins Repo.
- **Verifikation:** neuer Treiber `driver_boss60.py` (F3 → Welle 60, Serien-Screenshots) →
  Boss läuft scharf, lochfrei, sauberer Loop auf den Turm zu. `imageio`+`imageio-ffmpeg`
  installiert (für MP4-Input von `frames_from_clip`). Cutout-Experiment-Reste (`rig_walk.py`,
  Temp-PNGs) wieder entfernt; Preview-GIF aus dem Repo-Root gelöscht.
- **Separat (außerhalb Repo):** Godot-3D-Projekt `Desktop\Marshstalker3D\` aus demselben
  Modell (spielbarer Charakter, laufen/angreifen, Orbit-Kamera/Zoom, 4K-Vollbild) — eigenes
  Spiel, kein Teil des Clickers.

2026-06-22 (Teil 20) — **FX-/„Juice"-Layer (ADR 035):**
- **Frage des Nutzers vorab beantwortet:** Multi-Ansichten (4-/8-Richtungen) sind bei der
  Seitenansicht-Kamera unnötig (L/R-Flip via `_both_dirs()` reicht; vgl. Vampire Survivors).
  Plan: FX-Layer zuerst, danach echte KI-Frames für Helden, Turm-Animation — prozeduraler
  Ausbau bewusst weggelassen.
- **`game/fx.py`:** neue Klassen `Particle`/`MuzzleFlash`/`TrailDot` (Protokoll wie
  `DamageNumber`) + Spawner + FX-Konstanten. Additive Effekte skalieren RGB mit der
  Restlebensdauer (`BLEND_RGB_ADD` ignoriert Quell-Alpha).
- **`main.py`:** lose `fx`-Liste + `shake`-Float neben `dmg_numbers` (nonlocal in `start_run`,
  Update/Filter an den 3 Sub-Tick-Stellen, Draw in `world_surf`). Death-Poof in der
  Kill-Schleife (Boss/SuperBoss größer/farbig + Shake), Mündungsblitz + `trigger_recoil` an
  beiden Schussstellen, Trail pro Geschoss, `player.update(od_on)` pro Sub-Tick,
  Shake-Offset im `blit_world_zoomed` (neuer `offset`-Param).
- **`game/enemy.py`:** `Warrior._hit_flash` (Set in `take_damage`, Decrement in `update`) +
  Helfer `_apply_hit_flash` (weiße `BLEND_RGB_ADD`-Kopie, Silhouette erhalten); eingehängt in
  `_blit_sprite` **und** den 5 Spezial-Frame-Blits (Archer/Lancer/Monk/Boss/SuperBoss).
- **`game/player.py`:** Turm nicht mehr statisch — Idle-Puls (sin-Scale), Recoil-Pop +
  Versatz (`trigger_recoil`), Overdrive-Glühen; reine Transform/Tint des `player_tower.png`,
  Fallback-Kreis bleibt.
- **`game/balance.py`:** `SHAKE_BOSS_DEATH/_HIT/_DECAY` (Render-Feel-Sektion).
- **Verifikation:** `py_compile` aller Module; isolierte Direkt-Renders (FX-Primitive,
  Treffer-Flash an echtem Goblin-Sprite, Turm-Zustände) optisch korrekt; voller Treiber-Flow
  mehrfach crashfrei bis Sieg; Overdrive-Turm-Glühen im Live-Combat bestätigt. Ad-hoc-Test-
  skripte nach Gebrauch entfernt. **Noch nicht committet.**

2026-06-22 (Teil 19) — **Display-Titel-Font eingesetzt (Folgeschritt zu ADR 033):**
- **Cinzel** (Google Fonts, OFL 1.1 — darf gebündelt werden) nach `assets/fonts/Cinzel.ttf`
  geladen, `OFL.txt` (Lizenz) dazu. Variable-Font; pygame/SDL_ttf lädt die Regular-Instanz.
- **Kein Code geändert:** `theme.font(..., display=True)` + `_find_display_font()` (Verzeichnis-
  Scan zur Importzeit) waren schon verdrahtet (8 Titel-Stellen: Hauptmenü, Slot-Auswahl,
  Optionen, Lexikon, Pause/Overlays, Shop, In-Game-Sieg-Titel, Level-up-Karten). Untertexte/
  Buttons bleiben bewusst Arial.
- **Verifikation:** `theme._DISPLAY_FONT_FILE` zeigt auf Cinzel, Display-Font ≠ Arial (headless
  geprüft); voller Treiber-Flow crashfrei, Menü- + Level-up-Titel in Roman-Versalien bestätigt
  (`shots/01_menu.png`, `03_levelup.png`). **Noch nicht committet.**
- Kein ADR (ADR 033 hatte die Display-TTF als optionalen, bereits entschiedenen Punkt vermerkt).

2026-06-22 (Teil 18) — **Overdrive: erste aktivierbare Fähigkeit (ADR 034):**
- **Leertaste → 5-s-Burst** (×2 Angriffstempo, ×1.5 Schaden), 18 s Cooldown ab Aktivierung.
  Erster Schritt gegen die offene Genre-Frage (aktiver Eingriff im sonst passiven Auto-Combat).
- **`balance.py`:** Sektion `OVERDRIVE_*` (`DURATION_S=5`, `COOLDOWN_S=18`, `ATTACK_MULT=2.0`,
  `DAMAGE_MULT=1.5`). **`sounds.py`:** prozeduraler `"overdrive"`-Sweep.
- **`main.py`:** Timer `overdrive_active`/`overdrive_cd` in `fresh_game_state`; Auslöser im
  KEYDOWN-Block (Leertaste, nur wenn `overdrive_cd<=0`); im PLAYING-Update pro Sub-Tick
  dekrementiert + Multiplikatoren `od_atk`/`od_dmg` (1.0 außerhalb des Bursts); `spawn_projectiles`
  bekam `damage_mult`-Param. HUD: `draw_overdrive_bar` (oben mittig, orange/grau/grün).
  CONTROLS-Zeile ergänzt. Treiber: Leertasten-Schritt `02b_overdrive.png`.
- **Verifikation:** `py_compile` ok; voller Treiber-Flow crashfrei (inkl. Overdrive zünden →
  Balken grün→orange bestätigt, bis Sieg). **Noch nicht committet.** Offen: Balance-Tuning + das
  Boss-DPS-Modell kennt Overdrive noch nicht.

2026-06-22 (Teil 17) — **UI-Redesign „Glass-Hybrid" (ADR 033):**
- **Neues `game/theme.py`** (Palette + gecachte Glass-Primitive: `backdrop`/`backdrop_region`,
  `panel`, `drop_shadow`, `accent_glow`, `text`/`text_center`, `pill`, `header_band`, `font`).
  Schatten/Glows via Down-/Upscale-Blur (`smoothscale`), pro Form gecacht.
- **`Button`-Klasse** (`main_menu.py`) auf Theme umgestellt → alle Menü-Buttons gehoben.
- **Reskins:** Hauptmenü (Logo-PNG-Fallback, Pills), Shop (Glass-Slots + Gruppen-Chips),
  Karten (Glass + Schatten/Glow + **4 Gruppen-Icons** mit Tiny-Swords-Fallback), Slot-Auswahl,
  Optionen, Lexikon (Backdrop-Region als Scroll-Maske), End-Overlays (`_draw_end_overlay` —
  Glass-Card + Glow-Titel; `★` entfernt, da Arial-Fallback es als Kästchen rendert).
- **Bug gefunden+behoben:** weißer Hover-Overlay via `pygame.draw.rect` auf SRCALPHA-Karte
  **überschrieb** das Alpha (draw blendet nicht) → Karteninhalt grau ausgewaschen; entfernt,
  Hover signalisiert jetzt `accent_glow` + dickerer Rahmen.
- **Verifikation:** Headless-Renders aller Screens (`media/_ui_*.png`) + voller Treiber-Flow
  crashfrei (`shots/`). 5 Leonardo-PNGs (Logo + 4 Icons) + optionale Display-TTF noch offen
  (extern), Fallbacks aktiv. **Noch nicht committet.**

2026-06-22 (Teil 16) — **Player-Turm-Sprite getauscht + Fernkämpfer-Geschosse importiert (ADR 027):**
- **Neuer Turm:** kristallgekrönte Stein-Bastion (Leonardo, `key_black_bg` freigestellt) →
  `assets/custom/player_tower.png`; `player._TURM_PATH` darauf repointet (Pack-`Turm.png`
  unangetastet). `_TOWER_SIZE 110 → 135` (rein visuell, Trefferzone = `PLAYER_RADIUS`).
- **Alle 12 Geschoss-/Cast-PNGs eingesetzt** (6 Pfeile via neuem `tools/rotate_flat.py`
  nach rechts ausgerichtet — `--auto` PCA + `--flip`). Nach Nutzer-Bild-Tausch komplett neu
  freigestellt/ausgerichtet/verifiziert: alle 6 shot + 6 cast laden, Geschosse zeigen rechts,
  voller Treiber-Flow crashfrei bis VICTORY.

2026-06-22 (Teil 15) — **Playtest-Fixes: Necromancer-Soft-Lock + XP-Kurve (ADR 028):**
- **Necromancer/Lich greift wieder an (D40):** Wurzel war `Necromancer.ATTACK_RANGE = 240` >
  `PLAYER_ATTACK_RANGE ≈ 236,6` ((720/2)/1.4·0.92) → der Kiter parkte ~3,4 px außerhalb der
  Turm-Reichweite, unkillbar als letzter Gegner nach `SUMMON_MAX`. Fix: `ATTACK_RANGE → 220` +
  Pfeilangriff (`SHOOT_EVERY = 110`, `_shots`/`pop_shots()`, `EnemyProjectile(..., sprite=SPRITE_NAME)`).
  `main.py` Necro-Zweig sammelt `pop_shots()` zusätzlich zu `pop_summons()`. Vererbt auf alle Tier-Summoner.
- **XP-Kurve linear → quadratisch (ADR 028):** `xp_to_next = XP_BASE + XP_PER_LEVEL_SQ·(level-1)² +
  XP_PER_WAVE·wave`; `XP_PER_LEVEL_SQ = 1.0`, `XP_PER_WAVE 2→10`. Level 100 = 10809 XP (war 851),
  Modell 194→71 Levelups (Endlevel ~195→~72). Option A vom Nutzer gewählt (Tradeoff dokumentiert in ADR).
  `tools/balance_model.py`-Print auf `PER_LEVEL_SQ` angepasst.
- **Verifikation:** `xp_to_next(100,100)=10809`; Modell-Endlevel ~72; voller Treiber-Flow bis Sieg
  crashfrei (auch nach der externen `EnemyProjectile`-Sprite-Änderung der Parallel-Session/Teil 14).
- **Doku-Sync:** ADR 028 + README-Index; `architecture.md` Necromancer-Eintrag (ATTACK_RANGE 220 +
  Pfeil) + §5 XP-Formel + §11 Level-Inflation-Update; D40 im Decision-Log. **Committet diese Session.**

2026-06-22 (Teil 14) — **Fernkämpfer-Geschosse: Code-Wiring (ADR 027):**
- `EnemyProjectile` (`game/enemy.py`) lernt `sprite`-Parameter + Per-Name-Caches
  (`_shot_cache`/`_muzzle_cache`), Modul-Konstante `MUZZLE_TICKS=7`; `draw()` blendet
  Cast-Flash am Abschussort aus und blittet das eigene/rotierte Geschoss (Fallback-Kette).
- `sprite_loader._load_single` + `load_enemy_shot`/`load_enemy_muzzle` (Einzel-PNG,
  zugeschnitten/skaliert wie `load_cannonball`).
- Schützen reichen `SPRITE_NAME` durch (Archer 3 Stellen + Necromancer 1 Stelle); die
  6 Tier-Reskins unverändert (haben `SPRITE_NAME` schon).
- **Offen:** 12 PNGs (6 `_shot` + 6 `_cast`) müssen noch generiert werden — Prompts im
  Plan-File. Bis dahin überall Goldpfeil-Fallback. **Noch nicht committet.**
- Verifikation: `ast.parse` ok; voller Treiber-Flow (→ Welle 99/100 Tier-2-Dämonen →
  Sieg) crashfrei.

2026-06-21 (Teil 13) — **15 Tier-Sprites importiert (Leonardo.ai → Spiel):**
- 15 generierte Bilder den Gegnern zugeordnet (Sichtprüfung), je **freigestellt** mit
  `key_black_bg --enclosed` (neuer Pass entfernt Körper↔Arm-Taschen; Schwarz- UND Weiß-BG,
  ohne helle Skelette/dunkle Roben anzufressen) → `<name>_static.png`, dann `animate_walk.py`
  mit Archetyp-Preset → `<name>_run.png`. **30 Assets committet `2c7b856`.**
- Verifikation: Lexikon rendert **24/24 mit echten Sprites, null Lade-Fehler** (Kontaktbogen +
  Bestiary-Render geprüft); voller Treiber-Flow crashfrei bis Sieg. Offen: Posen oft frontal
  statt Seitenprofil; W150-Boss-HP (×100) laut Modell nur mit Dreifachschuss schaffbar.
- Auch committet: Prompt-Kit `docs/sprite-prompts.md` (`4f4b306`), `key_black_bg --enclosed`
  (`9b996bf`), Boss-HP ×5 (`d92d1c9`).

2026-06-21 (Teil 12) — **Karten-Farbgruppen + Shop-Ausbau (ADR 025, 026):**
- **4 Farbgruppen** (ROT Schaden / BLAU Verteidigung / GOLD Geld / WEISS XP), zentral in
  `balance.GROUP_COLORS`/`GROUP_TITLES` (Karten + Shop). Karten rendern als **getöntes
  Rundrechteck** je Akzentfarbe (asset-frei; Gold/Weiß hatten keine Button-PNGs).
- **Neue Karten (ADR 025):** ROT `lifesteal_pct` (+5% Schaden als HP) + `lifesteal_flat` (+2 HP/
  Treffer); BLAU `armor` (−6%/Stufe, Cap 75%), `hp_regen` (2 HP/s), `thorns` (20% Reflect),
  `dodge` (5%/Stufe, Cap 50%); GOLD `coin_boost`; WEISS `xp_boost` + `reroll`. Hooks:
  `_sync_player_defense` (Spiegelung auf `player`); Lifesteal in `check_projectile_hits`;
  Armor/Dodge in `Player.take_damage`; Dornen in `check_enemy_contact` (gibt Dornen-Kills zurück
  → Münzen/XP/Sound); HP-Regen FPS-stabiler Akku-Tick. **Boss-Oneshot** `player.hp = 0` (umgeht
  Armor/Dodge bewusst). **Reroll = Button** im Levelup-Overlay (`gs["stats"]["rerolls"]`).
- **Shop-Ausbau (ADR 026):** ∞-Käufe Start-Tempo/Start-Kugelgröße/Start-Lebensraub + globale
  Meta-Mult `coin_mult`/`xp_mult` (über alle Läufe, im Drop) + `free_rerolls`; Einmalkauf „Vierte
  Karte" (`extra_card` → 4 statt 3 via `_card_count`). **4-Spalten-Layout** nach Farbgruppe;
  draw + handle_click teilen `_iter_shop_slots()` (kein Drift). `save_data`-Defaults erweitert.
- **Verifikation:** Render-Shots (`render_cards4`/`render_shop`/`render_stats`); deterministisch
  Armor 40→20, Dodge 100%→0, Lifesteal 50→66, Dornen-Kill; Shop-Kauf aller Typen + Zu-teuer-Sperre
  (100000→93480). **Treiber-Menü-Fix** (Start-Klick aus echtem MainMenu-Layout abgeleitet). Voller
  Treiber-Flow bis Sieg crashfrei. **Hinweis:** Kauftest schrieb in Slot 1 → auf sauberen Standard
  zurückgesetzt. Noch nicht committet.

2026-06-21 (Teil 11) — **Tier-Roster: 15 reskinnte Gegner + Welle 150 (ADR 024):**
- **15 Gegner via Vererbung:** `_CustomSpriteMixin` (lädt `assets/custom/<name>_run.png`,
  Fallback-Primitiv bei fehlendem PNG) + 5 Rollen-Basisklassen (`_CustomMelee/_Swarm/_Ranged/
  _Tank/_Summoner`) + 15 konkrete Tier-Klassen in `game/enemy.py`. `Necromancer` bekam
  `SUMMON_CLASS`-Hook (Default `Goblin`); Beschwörer rufen Tier-Schwarm.
- **Spawn:** `TIER_ROSTER` (3×5) + `tier_for_wave` in `main.py`; `spawn_enemy_for_wave` behält
  Rollen-Gewichte, wählt Klasse je Tier. `tanker`/`monk` bleiben Original.
- **Welle 150:** `WIN_WAVE 100→150` (`balance.py`); Siegestext + F4 auf `WIN_WAVE` umgestellt.
- **Lexikon:** 15 Katalog-Einträge (Wellen-Label) + **Mausrad-Scrolling** in `BestiaryMenu`
  (`scroll()`, Offset in `_card_rect`, Kopf-/Fußband-Maske, Cull) + `MOUSEWHEEL`-Handler in `main.py`.
- **sprite_loader:** generischer `load_custom_enemy(name, px)`.
- **Verifikation:** `py_compile` (5 Dateien) ok; Headless-Instanziierung aller 15 Klassen →
  korrekte vererbte Stats + Summon-Hooks; **voller Treiber-Flow crashfrei bis Sieg „SuperBoss in
  Welle 150 bezwungen" (Screenshot)**; Lexikon oben + ganz unten gerendert, alle 24 erreichbar.
  **Offen:** 15 PNGs fehlen (Fallback-Kreise); Prompt-Kit im Plan-File. Committet auf Nutzerwunsch.

2026-06-21 (Teil 10) — **Spawn über festes 10-s-Wandzeit-Fenster (ADR 023):**
- Auf Nutzerwunsch („eine Welle dauert 10 s, bis dahin alle Gegner gespawnt"): fixes
  `BASE_SPAWN_INTERVAL` ersetzt durch `spawn_interval_ticks(wave, fps) =
  round(WAVE_SPAWN_SECONDS·fps / enemies_for_wave(wave))` in `game/balance.py`
  (`WAVE_SPAWN_SECONDS = 10.0`). An **Live-FPS** gekoppelt → echtes Sekunden-Fenster,
  FPS-Regler-stabil. Bosswellen (N=1): Sonderfall sofort. `diff_mod["spawn_bonus"]`
  bleibt additiver Nudge. Berechnung in `main.py` in den PLAYING-Block verschoben
  (gs ist im Menü None → NoneType-Crash gefixt). `BASE_SPAWN_INTERVAL` = nur noch Alt-Doku.
- Verifikation: deterministische Sim (W1/5/99 @ FPS 75 & 140 → letzter Spawn ~10,0 s, alle N;
  Boss ~0,01 s). **Achtung:** Headless-Treiber kam nicht über das Menü hinaus (Lauf-Starten-
  Klick griff nicht — wirkt wie ein paralleler Menü-Flow-Bruch, NICHT von dieser Änderung);
  PLAYING-Pfad daher nur per Simulation geprüft, nicht per Screenshot.

2026-06-21 (Teil 9) — Tuning-Sprint + Shop-/Combat-Features (ADR 021, 022):
- **Reine Werte (Nutzer-Tuning, iterativ):** Spieler-Basisschaden 10→15 (`BASE_DAMAGE`, +50%);
  Gegner langsamer (`enemy_speed_for_wave = min(1.1+wave·0.10, 2.4)`); `CAMERA_ZOOM 1.2→1.4`;
  **XP +70%** (`XP_GAIN_MULT=1.7`, alle Gegner) + **Münzen +50%** (`COIN_GAIN_MULT=1.5`);
  **Elite-HP gestuft** (`elite_hp_mult`: Basis ×3, +100%/10 Wellen additiv → W100 ×33);
  **Boss/SuperBoss +100%** (`BOSS_HP_MULT 6→12`, `SUPERBOSS_HP_MULT 10→20`). (Parallel vom
  Nutzer: `ENEMY_HP_GLOBAL_MULT` auf 0.25 gesenkt, `WAVE_TIER_MULT` auf 1.0/aus.)
- **Gestufter Doppelschuss-Shop (ADR 022):** Einmalkauf → gestuftes Upgrade
  (`upgrades.doppelschuss` 0–2), Stufe 1 „Doppelschuss" 5000 / Stufe 2 „Dreifachschuss" 20000;
  neue `_TIERED`-Shop-Kategorie (capped, eigene Kostenliste); Gameplay feuert `Stufe` gerade
  Extra-Schüsse (trifft auch Bosse). Karten-Text „3 Kugeln"→„3 Schuss".
- **Begrenzte Angriffsreichweite (ADR 022):** `PLAYER_ATTACK_RANGE` aus `CAMERA_ZOOM` abgeleitet
  (`ATTACK_RANGE_FRAC=0.92`); Turm zielt nur in Sichtweite → Kills immer im Bild.
- **Aufgeben behält Gold (ADR 022):** Pause→Hauptmenü bucht `gs["coins"]` ins `total_coins`.
- **SessionStart-Hook (ADR 021):** `tools/session_status.py` + `.claude/settings.json` → Status
  (Current focus/Next step + neuestes ADR) automatisch bei jedem Session-Start im Kontext.
- **Verifikation:** `py_compile` aller berührten Module; Headless-Tests (Shop 0→1→2/max, Reichweite
  ~236px, Aufgeben 36→41 Gold, XP/HP/Münz-Werte); voller Treiber-Flow bis Sieg crashfrei.
  **Alles uncommitted; Parallel-Session editiert dieselben Dateien (Tree gemischt).**

2026-06-21 (Teil 8) — Komfort-/QoL-Welle + Drache läuft (ADR 016 akt., 019, 020):
- **Drache (ADR 016 aktualisiert):** vom Schweben auf **geerdeten Walk-Zyklus** umgestellt —
  detailliertes KI-Drachenbild freigestellt (`key_black_bg` + strikter „nur reines Schwarz"-Pass
  gegen die eingeschlossene Flügel-Tasche), prozedural fußverankert animiert →
  `drache_superboss_walk.png` (8 Frames); `SuperBoss` ohne `FLY_LIFT`/Bob. Plus Code-only
  **Angriffs-Lunge** (sin-Hüllkurve: Vorstoß + Scale + Aura-Clench; rein visuell).
- **FPS (ADR 020):** Standard 75→140 (`constants.py`); **FPS-Regler** in den Optionen
  (Schiebebalken, 30–240), treibt `clock.tick` **und** die Feuerrate (`fps_value`). **Speed-/
  Zeitraffer-Button** x1/x5/x10/x20 im HUD: die gesamte Gameplay-Update-Logik läuft N×/Frame
  (Update-Block in `for _ in range(time_scale)` gewrappt) → alles gleichmäßig schneller,
  Balance identisch.
- **Speicherstände (ADR 019):** `save_data` auf **Mehr-Slot-Modell** (aktiver Slot; bestehende
  `sd.save(save)`-Aufrufe unverändert). 3 Slots `save_slot<N>.json`, **SlotSelectMenu** als
  erster State **vor dem Hauptmenü** (Auswahl/Löschen, Migration der Alt-`save.json` in Slot 1).
  `save_slot*.json` gitignored.
- **Lexikon:** `BestiaryMenu` + Hauptmenü-Button + `BESTIARY`-State; Katalog aller 9 Gegner mit
  Stats + Sprite-Thumbnail (lazy aus den Klassen-Loadern), nur **gesehene** enthüllt
  (`seen_enemies` je Slot persistiert, beim Spawn markiert).
- **Balance (reine Werte):** Elite-HP `ELITE_HP_MULT 10→3`; **+10 % XP je Welle**
  (`xp_round_mult = 1 + 0.10·wave`, linear → W100 ×11); kurz eingebaute Wellen-Härte
  (+40 %/10 Wellen kompoundierend) auf Nutzerwunsch **zurückgesetzt** (`WAVE_TIER_MULT=1.0`).
- **Verifikation:** headless Renders (FPS-Regler, Lexikon, Slot-Screen, Drache geerdet, Speed x20
  → schneller Levelup) + voller Treiber Slot→Menü→Spiel→Sieg crashfrei. Treiber um Slot-Pick
  erweitert.
- **Commit:** `cdbb01d` bündelt den Großteil (auf Wunsch „alles", inkl. paralleler ADR-017/018-
  Arbeit). Danach: Drache-Walk, Speed-Button, XP/Elite/Wellen-Härte-Reset noch **uncommitted**.

2026-06-21 (Teil 7) — Feel-/Meta-Balance-Umbau + Sprites animiert (ADR 018):
- **Sprites:** 3 KI-Charaktere (schwarzer BG) via `tools/key_black_bg.py` gekeyt + via
  `tools/animate_walk.py` zu 8-Frame-Walk-Strips animiert (Bob/Squash/Tilt; Presets je
  Klasse). DragonBones/DesignPanel geprüft + verworfen (totes Flash-2015-Tool).
- **Feel (Nutzerwünsche):** `enemy_speed_for_wave` ~30 % langsamer (`min(1.5+wave·0.13, 3.2)`);
  `CAMERA_ZOOM 1.2→1.4` (alles größer via Post-Render-Zoom, Hitboxen unberührt); neue
  Gegner-HP **×10** (Goblin 0.25→2.5, Ork 2.5→**25**, Nekro 0.6→6.0 der Basis); `save.json`
  auf Defaults zurückgesetzt.
- **Meta-Gate „~5 Läufe bis Welle 100" (ADR 018):** neues Mehr-Lauf-Modell
  `tools/balance_model_runs.py` (Boss-Wand = Todeswelle, Münzen→permanenter Startschaden→Wand
  wandert). Brüchige Klippe entdeckt (Boss-Mult allein: 2→65→nie) → vier Hebel zusammen:
  `BOSS_HP_MULT 2→6`, `SUPERBOSS_HP_MULT 3→10`, `PERMANENT_DAMAGE_PER_LEVEL 15→25`,
  `COST_MULT 1.65→1.4`. Modell: Todeswelle 10→50→80→90→100 = **5 Läufe** (4 mit Goldenen
  Kugeln). Revidiert das „kein-Wall"-Ziel von ADR 013/014 bewusst.
- **VORBEHALT:** Modell misst nur die Boss-DPS-Wand, **nicht** den HP-Tod durch die ×10-zähen
  Normalgegner → real evtl. mehr Läufe. Playtest entscheidet; Gegenhebel = neue-Gegner-HP
  runter oder Modell um Clear-/Überlebensrate erweitern.
- **Verifikation:** Modell LIVE = 5 Läufe; `py_compile` OK; voller Treiber-Flow bis Sieg
  crashfrei; Zoom 1.4 + Walk-Frames im Screenshot bestätigt. **alles uncommitted.**

2026-06-21 (Teil 6) — Drei neue Gegnerklassen + Leonardo-Prompts (ADR 017):
- **Leonardo Phoenix 1.0** empfohlen (Style „Illustration", Contrast 3.5, Transparency an,
  Pixel-Art-Style explizit **aus** — Tiny Swords ist glatter 2.5D-Cartoon). Copy-paste-Prompts
  (positiv + gemeinsamer Negative/Stil-Suffix, „facing right" für `_load_custom_strip`) für
  Goblin, Ork-Berserker, Nekromant geliefert.
- **`game/enemy.py`** + 3 Klassen (alle subklassen `Warrior`, eigener `_frames_*`-Cache +
  `_load_sprites()`-Fallback, Golden Rule 5): `Goblin` (Schwarm, speed×1.6/hp×0.25),
  `OrcBerserker` (Brecher, speed×0.5/hp×2.5, `DAMAGE_MULT=2`, nutzt `orc_warrior`-Sheets),
  `Necromancer` (Beschwörer wie Monk auf Distanz, ruft Goblins via `SUMMON_*`/`SUMMON_MAX`,
  `pop_summons()`).
- **`game/sprite_loader.py`:** `load_goblin_run` + `load_necromancer_run`. **`main.py`:** Import
  erweitert, Spawn-Tabelle welleabhängig gewichtet (goblin ab W5, orc ab W8, necro ab W12);
  Necromancer-Summons **nach** der Update-Schleife angehängt (kein Mutieren während Iteration).
- **Verifikation:** `py_compile` OK; Headless-Unit-Test (Stats + Draw-Fallback + Beschwörung) OK;
  voller Treiber-Flow (F3→Welle 49) crashfrei mit aktiver Spawn-Tabelle; Fallback-Primitive
  gerendert (grün / grün-Ring / lila+Aura).
- **Sprites eingesetzt (Folge-Schritt, dieselbe Session):** Nutzer lieferte 3 KI-Charaktere
  (Leonardo, **schwarzer BG** — Transparency war aus) → neues `tools/key_black_bg.py`
  (Pillow-only: Ecken-Flood-Fill keyt nur rand-verbundenes Schwarz, schont innere Outlines;
  zuschneiden + auf Quadrat zentrieren, weil `_load_custom_strip` `subsurface((0,0,h,h))`
  macht → Hochformat würde crashen). Ablage als 1-Frame-Strips (1396²/1423²/1380²).
  **Bugfix:** `OrcBerserker._load_sprites` lädt run + attack jetzt in **getrennten**
  try/except — fehlendes Attack-Sheet riss vorher die Lauf-Sprites mit weg. Reale Sprites
  laden + rendern transparent (kein Halo/Löcher); voller Treiber-Flow bis Sieg crashfrei.
- **Walk-Animation gelöst (prozedural, dieselbe Session):** DragonBones-Routen geprüft +
  verworfen (DesignPanel = Flash-Plugin von 2015, tot; volles Rigging Overkill bei ~60 px).
  Stattdessen `tools/animate_walk.py` (Pillow-only): erzeugt aus jedem Standbild einen
  8-Frame-Strip — vertikaler **Bob am Fußpunkt** (verankert, kein Schweben), **Squash/Stretch**
  auf dem Stampf-Beat, leichter **Tilt**; `--bounces` (2=Marsch, 1=Schweben). Presets: Ork
  schwerer Stampf, Goblin flinkes Trippeln, Nekromant sanftes Schweben (bounces=1, squash=0).
  Frames per Kontaktbogen geprüft (Fuß auf Baseline, kein Clipping); `Warrior.update` cycelt
  sie automatisch; voller Treiber-Flow bis Sieg crashfrei. **uncommitted; Balance offen.**

2026-06-21 (Teil 5) — SuperBoss fliegt jetzt: animierter Drache (ADR 016, **ersetzt 015**):
- Nutzer lieferte ein sauberes **5×5-Spritesheet** (25 Frames Flug-/Lauf-Zyklus, **Alpha-
  Hintergrund, kein Wasserzeichen** — anders als das parallel gelieferte Walk-GIF) und den
  Wunsch „ihn etwas fliegen lassen". Sheet deterministisch zu einem **25-Frame-Strip** auf
  gemeinsamer Alpha-Bounding-Box (200×144) verarbeitet → `assets/custom/drache_superboss_fly.png`.
- `load_drache_superboss(target_w=240)` zerlegt den Strip und **`smoothscale`t** ihn
  (glattes Art, kein NEAREST mehr), Seitenverhältnis erhalten. Animation läuft **gratis** über
  `Warrior.update` (cycelt `_anim_frame`); die tote Lancer-Attack-Maschinerie entfernt.
- **„Fliegen" = rein visuell:** `SuperBoss.draw` versetzt die Zeichen-Position um `FLY_LIFT`
  (18) + `sin(tick·0.06)·11` Bob; `self.pos` bleibt am Boden → Stop-Distanz/Treffer/Aura fair.
  `SPRITE_PX` 170→240 (jetzt Zielbreite).
- **Verifikation:** headless (25 Frames, 240×173, Animation cycelt, HP 30k korrekt) + Render auf
  Terrain + voller Treiber-Flow bis Sieg crashfrei + **Live-Shot Welle 100** (Drache fliegt mit
  Aura/Boss-HP-Bar vom Rand auf den Turm zu). **uncommitted.**

2026-06-21 (Teil 4) — SuperBoss-Drache als Pixel-Art-Sprite (ADR 015, **abgelöst von 016**):
- Vorhandenes Drachen-Artwork deterministisch zu **Pixel-Art** heruntergerechnet (verkleinern
  + Palette reduzieren + Schwarz/Taschen transparent), Nutzer wählte die 96×96-Lava-Variante.
  Liegt als `assets/custom/drache_superboss.png`.
- `sprite_loader.load_drache_superboss()` lädt es **NEAREST-skaliert** (Pixel-Art scharf);
  `SuperBoss` nutzt es statt der Lancer-Sprites (`_lancer_atk=[]`, `RADIUS` 50→60,
  `SPRITE_PX=170`), **Spawn nur Ost/West** auf Turm-Höhe; pulsierende Aura-Ringe bleiben.
- **Verifikation:** headless Instanz (Rand-Spawn, Frame 170², R60, HP 30690) + Render auf
  Terrain (boss-groß, blickt zum Turm); voller Treiber-Flow bis Welle 100 → Sieg crashfrei.
- Bekannter Tradeoff: **Stil-Bruch** (Pixel-Boss vs. glatte Tiny-Swords-Gegner) — bewusst per
  Nutzerwunsch. Größe via `SPRITE_PX`/`RADIUS` tunebar.

2026-06-21 (Teil 3) — SuperBoss-Sprite aus KI-Video (Drachenlord) **verworfen**:
- Versuch, den SuperBoss als animierten Drachen aus einem Kling-MP4 zu setzen (Frame-Extraktion
  + Keying-Pipeline). **Vom Nutzer verworfen — Sprite gefiel optisch nicht**, alles rückgängig
  gemacht (enemy.py/sprite_loader.py via git checkout; Banner/Sieg-Text/Doku manuell zurück;
  Assets + Tool + nie committete ADR gelöscht). Ersetzt durch das Pixel-Art-Sprite oben
  (Teil 4). Die Balance-Arbeit (ADR 013/014) blieb unberührt.

2026-06-21 (Teil 2) — Zweiter Endgame-Hebel: XP-Wellenskalierung (ADR 014):
- **Modell um zwei Hebel erweitert** (`xp_wave_scale`/`xp_wave_div` = Lever B, `sq`-Override =
  Lever A) und Dosis gesweept. Befund: Lever A allein reicht nie (SQ 0,3 → noch 5/10 Bosse
  über Budget); voller Münzfaktor (XP wie Münzen, `//3`) überschießt → Level 164, triviales
  Endgame. Sweet Spot = gedämpftes Lever B.
- **Entscheidung (D27): „Root-Fix pur", `XP_WAVE_DIV=8`** → `gs["xp"] += enemy.coin_value *
  xp_wave_mult(wave)` mit `xp_wave_mult = 1+wave//8`. W1–7 unverändert (×1), W100 ×13. Modell:
  Endlevel ~98, 0/10 Bosse über Budget (W90 4,3 s/Bud 4,7 s; W100 6,5 s/Bud 8,2 s). Bewusst
  gegen HP-lastige Combos (niedrigeres Level, mehr Build-Vielfalt) zugunsten *einfacher* ein
  Hebel — Risiko Level-Inflation akzeptiert.
- **Verifikation:** `xp_wave_mult` headless (W1–7 ×1 … W100 ×13); Modell 0/10 über Budget;
  voller Treiber-Flow bis Sieg crashfrei.
- **Doku-Sync:** ADR 014 + README-Index; `architecture.md` §5 (XP-Formel) + §11 (beide Hebel,
  Level-Inflation-Risiko); dieser `progress.md`-Eintrag.

2026-06-21 — Boss-Wand per Balance-Modell entschärft (ADR 013):

2026-06-21 — Boss-Wand per Balance-Modell entschärft (ADR 013):
- **Read-only Balance-Modell** `tools/balance_model.py` gebaut (Analyse-Tool, kein Spiel-
  Code): importiert `balance.py`, simuliert XP/Level/DPS über einen 1→100-Lauf, berechnet
  Boss-TTK gegen das **Walk-Budget** (Anlaufzeit Rand→Mitte) + den „fairen" HP-Multiplikator
  je Boss-Welle. Zwei harte Befunde: (1) Spieler endet ~Level 33 (XP/Kill = Klassen-Basis
  1/3, ×5 Elite, **nicht** wellenskaliert — `main.py:644`); (2) Boss = DPS-Rennen gegen
  Anlaufzeit, HP/Lifesteal irrelevant (Bosse one-shotten). Alte ×8/×25 → TTK ~294 s fresh
  auf W100, unfaire Wand ab ~W40.
- **Boss-Multiplikatoren gesenkt (ADR 013):** `Boss ×8→×2`, `SuperBoss ×25→×3`, als benannte
  Konstanten `BOSS_HP_MULT`/`SUPERBOSS_HP_MULT` aus `enemy.py`-Magic-Numbers nach `balance.py`
  gezogen (Golden Rule 2). SuperBoss W100 30.690 HP (war 255.750). Bewusst nur dieser eine
  Hebel; W60+ bleibt fresh hart (zweiter Hebel offen).
- **Verifikation:** Boss-HP headless gegen Konstanten geprüft (alle OK); voller Treiber-Flow
  Menü→Lauf→F4→Welle 100/SuperBoss→Sieg crashfrei.
- **Doku-Sync:** ADR 013 + README-Index; `architecture.md` §11 (255k→31k, Level-33-Befund,
  Walk-Budget); dieser `progress.md`-Eintrag.

2026-06-20 — Reward + Endgame-Scaling + Stats-Overlay (ADR 012, Playtest-Session):

2026-06-20 — Reward + Endgame-Scaling + Stats-Overlay (ADR 012, Playtest-Session):
- **Elite-Reward (ADR 011 ergänzt):** `enemy.coin_value *= ELITE_REWARD_MULT=5` →
  ×5 Münzen UND XP (`coin_value` speist beides); ×5 statt ×10 HP, um Anti-Snowball nicht
  auszuhebeln. (Headless geprüft: Faktor 5; per `ELITE_SPAWN_CHANCE=0.5` temporär playtest-
  bar gemacht, danach zurück auf 0.10.)
- **Gegner-HP super-linear (ADR 012):** linear `30+Welle·10` → `Basis + Welle·12 +
  Welle²·0.9` (benannte Konstanten). Grund: Spielerkraft multiplikativ, linear holt das nie
  ein → Welle 100 war trivial (Level-17-Build via F4 schlug SuperBoss). W17→100 jetzt ~20×;
  SuperBoss 25,7k→255k HP. **Erkenntnis: F4 ist Debug-Sprung, kein Endgame-Balance-Test.**
- **Stats-Overlay (Taste C, D25):** `draw_stats_panel` zeigt Schaden/Angriffstempo/Kugel-
  Stats/Multishot/Durchschlag/Lifesteal/HP; liest direkt aus `gs["stats"]`+`balance`
  (selbst-dimensionierend). `show_stats`-Toggle, kein Dev-Key; Dev-Hint um „C Stats".
- **Verifikation:** Treiber crashfrei bis Welle 100; HP-Kurve + Reward + Panel headless/
  Render geprüft. Commits `9b3190c` (Reward) + `0722e1c` (Scaling+Panel), gepusht bis 9b3190c.
- **Doku-Sync (dieser Wrap-up):** ADR 012 angelegt + README-Index; `architecture.md` §6
  (super-lineare Formel) + §11 (Risiko aktualisiert); `CLAUDE.md` (Taste C, F4-Caveat).

2026-06-20 — Passiv-Combat + Elites + Anti-Snowball (ADR 010/011, frühere Session-Phase):
- **Voll-Auto-Feuer (ADR 010):** `mouse_held` komplett entfernt; Turm feuert bei
  `fire_timer<=0` **und** vorhandenem Ziel, sonst bleibt Timer ≤0 (Sofortschuss beim
  ersten Gegner). **Autoaim:** `nearest_enemy_pos(pc, enemies)` zielt auf den nächsten
  lebenden Gegner (Welt-Koord. = direkt nutzbar, Zoom zentriert → Richtung identisch).
- **LMB-Spam getötet:** kein `fire_timer=0`-Reset beim Klick mehr; allein der Timer taktet.
- **Angriffstempo-Karte additiv:** `attack_speed += 0.2` (war `×1.10`); `BASE_ATTACK_SPEED
  1.0→1.5`. Karten-Text aus `balance.py` → „+0.2/s Angriffstempo".
- **Elite-Gegner (ADR 011):** `ELITE_SPAWN_CHANCE=0.10`, `ELITE_HP_MULT=10`, `ELITE_COLOR`.
  Würfel im Nicht-Boss-Zweig von `spawn_enemy_for_wave` (Bosse ausgenommen); `elite`-
  Klassenattribut auf `Warrior` (alle Subklassen erben); roter Ring in der Draw-Schleife.
- **Sprites:** `ENEMY_SPRITE_SCALE=1.25` + neuer `_epx()` in `sprite_loader` — nur
  Gegner-Körper, Turm (`_TOWER_SIZE`) und Projektile unberührt.
- **Spawn:** `BASE_SPAWN_INTERVAL 40→60`, `MAX_ENEMIES_PER_WAVE 45→30` (weniger, gestreckter).
- **Anti-Snowball:** `XP_BASE 5→8`, `XP_PER_LEVEL 3→7` — XP bis Lvl 10 ~1.7×, später Levelup
  fast doppelt so teuer (gegen „ab Lvl 10 durchlaufen").
- **Verifikation:** Treiber (hält nie die Maus!) läuft fehlerfrei + Screenshot zeigt
  auto-abgefeuertes Projektil; Elite-Rate (0.103/4000), 10×-HP, Boss-Ausnahme + Elite-Ring
  headless geprüft. Spielgefühl/Balance per **Playtest** offen.

2026-06-20 — Playtest-Tuning (nach ADR 009, dieselbe Session):
- `BASE_ATTACK_SPEED 0.60 → 1.0` /s (ADR-009-Rationale „bewusst langsam" verworfen).
- `enemy_hp_for_wave` Scaling `·14 → ·10` (ADR-009-„steileres Scaling" zurückgenommen).
- `BASE_SPAWN_INTERVAL 58 → 40` (Gegner spawnen dichter).
- **Levelup-Klick-Sperre:** `LEVELUP_INPUT_LOCK_S = 0.75` s — `UpgradeMenu` blockt Klicks
  0.75 s nach Erscheinen des Karten-Screens (verhindert Fehlklick beim gehaltenen Feuer);
  Hover-Hint erscheint erst nach Ablauf.
- Code (ADR 006-009) + Tooling + Docs in 3 thematischen Commits (7de7165/099d8aa/488aea6);
  dieses Tuning + die Klick-Sperre sind noch **uncommitted**.

2026-06-20 — Combat-Umbau (ADR 009):
- **Auto-Feuer:** `mouse_held` (LMB) statt Einzelklick; im `PLAYING`-Update feuert
  `fire_timer<=0 & held` Richtung Maus, dann `fire_timer = FPS / attack_speed`.
  `stats["attack_speed"]` = Schüsse/Sek., Basis `BASE_ATTACK_SPEED=0.60`.
- **Karte „Angriffstempo"** (rot, repeatable): `attack_speed *= 1.10` (`UPGRADE_ATTACK_SPEED`).
- **Lifesteal:** `check_projectile_hits(..., player)` heilt `LIFESTEAL_PER_HIT=1` HP/Treffer.
- **Steileres Scaling:** `enemy_hp_for_wave = (30 + wave·14)·hp_mult` (war ·10).
- **Verifikation:** Treiber startet fehlerfrei; Feuer-Intervall (125f@Basis) + HP-Mathe
  headless geprüft; neue Karte im Pool. Auto-Feuer/Lifesteal per **Playtest** (Treiber
  feuert nicht, nutzt F-Tasten).
- **Doku:** ADR 009 + README; `architecture.md` §1/§3.2/§5; `CLAUDE.md` (Feuer-Beschreibung).

2026-06-20 — XP/Level-System (ADR 008):
- **Loop-Umbau:** Karten kommen jetzt aus **Level-ups**, nicht pro Welle.
  `WAVE_CLEAR` rückt direkt zur nächsten Welle vor (Banner/Boss-Musik dorthin);
  `UPGRADE` wird bei `pending_levelups>0` aus `PLAYING` betreten und erhöht KEINE Welle.
- **XP:** `gs["xp"] += enemy.coin_value` im Kill-Loop; `while xp>=xp_to_next: level++,
  pending_levelups++`. `balance.xp_to_next(level,wave) = XP_BASE+(level-1)·3+wave·2`.
  `fresh_game_state` um `xp/level/xp_to_next/pending_levelups` ergänzt.
- **HUD:** Level + XP-Bar (unten zentriert); `UpgradeMenu`-Titel „Level Up!".
- **Knackiger/tödlicher (revidiert ggü. ADR 007):** Cap 80→45, Interval 72→58,
  Concurrent 40→30, `WAVE_CLEAR_DELAY 120→70`, `ATTACK_DAMAGE 14→22`, Archer 11→16,
  Gegner schneller (2.2 + w·0.18, Cap 4.6), Player `MAX_HP 150→120`.
- **Dev F5** = Levelup erzwingen; Treiber-Flow nutzt es (`03_levelup`/`04_after_levelup`).
- **Verifikation:** Treiber startet fehlerfrei; Screenshots zeigen XP-Bar +
  „Level Up!"-Karten + intakten Sieg. XP-Mathe headless geprüft. **Balance per Playtest.**

2026-06-20 — ~2h-Rebalance + Render (ADR 007):
- **1.25x Speed:** `constants.FPS 60→75`.
- **Spawn-Floor-Rückgrat:** `BASE_SPAWN_INTERVAL 90→72`, `MAX_ENEMIES_PER_WAVE 40→80`,
  `MAX_CONCURRENT_ENEMIES 25→40` (Cap greift ab Welle 26). Modell: ~108min Spawn-Floor.
- **Gefährlicher/zäher:** `ATTACK_DAMAGE 10→14`, `EnemyProjectile.DAMAGE 8→11`,
  Player `MAX_HP 100→150`; Karten `UPGRADE_DAMAGE 10→15`/`_BULLET_SIZE 4→6`/
  `_BULLET_SPEED 3→4`/`_MAX_HP 25→40`; permanent `…DAMAGE 10→15`/`…HP 30→40`.
- **Kamera-Zoom 1.2x:** `blit_world_zoomed()` in `main.py` — Welt in `world_surf`,
  zentraler 1/zoom-Ausschnitt formatfüllend auf Screen; HUD/Cursor unskaliert obendrauf.
  Zielen bleibt korrekt (Skalierung um Mitte). **Tradeoff:** Gegner poppen am Rand herein.
- **Sprites 1.1x:** `SPRITE_SCALE` in `sprite_loader._px()` auf alle Lade-Größen + Turm.
- **Verifikation (Teil):** Treiber startet fehlerfrei, Werte live; Screenshots zeigen
  Zoom + größere Sprites. **2h-Spielzeit selbst nur per Playtest prüfbar.**

2026-06-20 — Phase 2 (Welle 100 + Sieg):
- **Wellen-Cap (ADR 006):** `enemies_for_wave = min(5+(Welle-1)·3, MAX_ENEMIES_PER_WAVE=40)`
  (Boss-Wellen bleiben 1); neuer **Concurrent-Cap** `MAX_CONCURRENT_ENEMIES=25` im
  Spawn-Gate (`main.py`). Welle 99: 299 → 40 gesamt, nie >25 gleichzeitig. Deckelt
  Performance **und** Belagerungs-DPS.
- **`VICTORY`-State:** an der Wellen-Clear-Stelle verzweigt — `gs["wave"] >= WIN_WAVE`
  (100) → Sieg statt `WAVE_CLEAR`. `best_wave`/`best_coins`/`total_coins` gebucht,
  `sd.save`. Event (R/M) teilt sich Logik mit `GAME_OVER`; Update No-Op; eigener
  `draw_victory`-Screen. Alle drei Phasen behandelt (Golden Rule 4).
- **Dev-Taste F4** → Welle 99 (nächste Clear → SuperBoss W100 → Sieg testen);
  Dev-Hint + `CLAUDE.md` ergänzt.
- **Neu in `balance.py`:** `WIN_WAVE`, `MAX_ENEMIES_PER_WAVE`, `MAX_CONCURRENT_ENEMIES`.
- **Verifikation (Teil):** Spiel startet fehlerfrei; Test bestätigt Cap-Logik
  (`enemies_for_wave(99)==40`, Boss-Wellen==1) + Konstanten. **Sieg-Screen selbst noch
  nicht durchgespielt** (headless nicht klickbar).
- **Doku-Sync:** `architecture.md` §3.1 (VICTORY-State), §3.2 (beide Run-Enden → `gs=None`),
  §5 (Sieg-Übergang + Spawn-Gate), §8 (MVP-Sieg konkretisiert); ADR 006 angelegt +
  README-Index; `CLAUDE.md` Dev-Tasten.

## Next concrete step

**ComfyUI auf der GPU-Maschine aufsetzen und den SD-Generator end-to-end testen (ADR 037).**
ComfyUI installieren (eigenes venv, CUDA-torch), einen gepflegten Cartoon-/Stylized-SD-1.5-
Checkpoint nach `ComfyUI/models/checkpoints/` legen, `pip install -r tools/requirements-sd.txt`.
Dann `python tools/sd_comfy.py` (Erreichbarkeit) → `python tools/sd_gen.py --name skeleton_warrior
--ckpt <datei>` → Kontaktblatt `assets/custom/_sd_raw/skeleton_warrior_contact.png` ansehen →
`--pick N` → `assets/custom/skeleton_warrior_static.png`. **A/B gegen das vorhandene Standbild**
entscheidet, ob „professionell genug". Voll dokumentiert in `tools/README-sd.md`.

**Danach offen (separater Strang, ADR 027):** die 12 Fernkämpfer-Angriffs-PNGs (`_shot`/`_cast`)
— Prompt-Kit im Plan-File `~/.claude/plans/ich-m-chte-f-r-die-twinkling-candy.md`. Details unten
im alten Eintrag aufgehoben:

**Die 12 Fernkämpfer-Angriffs-PNGs erzeugen (Leonardo.ai) und einsetzen (ADR 027).**
Pro der 6 spawnenden Tier-Fernkämpfer (`skeleton_archer`, `lich`, `demon_caster`,
`demon_summoner`, `drake_archer`, `dragon_priest`): ein Geschoss `<name>_shot.png`
(1:1, transparent, zeigt nach RECHTS) + ein Cast-Flash `<name>_cast.png` (radial) nach
`assets/custom/`. **Keine** `animate_walk.py`-Stufe (Standbilder, kein Strip). Prompt-Kit
(2 Stil-Blöcke + Negative-Prompt + je 6 `_shot`/`_cast`-Subjektzeilen, thematisch je
Gegner: Knochenpfeil/grüner Seelenschädel/Höllen-Feuerball/rotes Siegel/Drachen-Bolt/
Gold-Orb) im Plan-File `~/.claude/plans/ich-m-chte-f-r-die-twinkling-candy.md`. Jede PNG
ersetzt lautlos den Goldpfeil-Fallback. Danach im Spiel gegenchecken (F2/F3 → Tier-Fern-
kämpfer, Cast-Flash + Geschoss-Optik prüfen).

(Die 15 Tier-**Lauf**-Sprite-PNGs sind seit Teil 13 importiert — Prompt-Kit für etwaige
Nachzügler im Plan-File `~/.claude/plans/ich-will-mehr-png-s-virtual-balloon.md`, Workflow
Einzel-Standbild → `python tools/animate_walk.py <static> <name>_run.png` mit Archetyp-Preset.)
Danach: **Balance von W101–150** beobachten (Tier 3 ungetestet — HP-Wand-Risiko; Hebel
`ENEMY_HP_PER_WAVE_SQ`).

(Davor unverändert offen:) **Echter Playtest des 5-Läufe-Meta-Gates (ADR 018).** Kernfrage:
stimmt „~5 Läufe bis Welle 100" *im echten Spiel* — oder sind die ×10-zähen Normalgegner (v. a.
Ork ×25) die wahre Wand
(Turm überrannt = HP-Tod), die das Boss-Wand-Modell nicht kennt? Falls real >> 5 Läufe:
**Gegenhebel** = neue-Gegner-HP senken (Ork ×25 ist extrem) ODER `tools/balance_model_runs.py`
um eine Überlebens-/Clear-Rate erweitern (reguläre Gegner-DPS gegen Spieler-HP/Lifesteal).
Sekundär: tragen die neuen Gegner-Rollen den Druck, ist der Necro-Anteil ok (Summons umgehen
den Concurrent-Cap)? Reicht die prozedurale Bewegung optisch? Regler: `target_px` (Größe),
`animate_walk.py`-Presets (Bewegung), die vier ADR-018-Konstanten (Läufe-Zahl).

Parallel/danach: **Ein echter 1→100-Lauf (kein F4!)** mit allen Hebeln drin (ADR 013 ×2/×3 + ADR 014 XP-
Wellenskalierung). Leitfragen: (1) Fühlen sich die späten Bosse als knappes, faires DPS-
Rennen an (Modell: alle im Walk-Budget)? (2) **Fühlt sich ~Level 98 gut an oder nach „alles
mitnehmen"?** Wenn die Build-Entscheidung zu sehr verwässert, ist der Gegen-Hebel ein HP-
lastigeres Re-Tuning: größeres `XP_WAVE_DIV` (weniger Level) + niedrigeres
`ENEMY_HP_PER_WAVE_SQ` (z. B. `//20 + SQ 0,4` → Modell-Level ~61). Das Modell
(`python tools/balance_model.py`) rechnet Varianten vorab durch.

(Realitäts-Check: ein echter Lauf liefert die *tatsächliche* Level-Kurve — weicht sie stark
von ~Level 98 ab, Modell-Annahmen [Kartenpolitik, Elite-Rate] nachziehen.)

Danach **Phase 3 (Inhaltszuwachs):** naheliegend sind weitere Karten/Upgrades (Ideen-
Liste aus Brainstorm: Crit, Explosiv-/Kettenschuss, DoT, Regen, Dornen, „Gelehrter"
+XP, Reroll, permanente Start-Boni). Drei Achsen sauber trennen — Damage / Speed-Sustain
/ Spread — für echte Build-Entscheidungen. Viele dieser Karten brauchen kleine neue
`gs["stats"]`-Felder + Logik in `check_projectile_hits()`/`update` (kein reiner
Datentabellen-Eintrag mehr).

(Optionaler Nachzügler: Basis-Stats in `fresh_game_state()` und ein eigenes
`xp_value` je Gegnerklasse sind noch nicht in `balance.py`.)

## Open questions

- **Waffen-Mechanik (Part 2):** Arbeitsannahme „Waffe = anderes Schussverhalten"
  (z. B. Schrot/Laser/Bumerang). Noch nicht final bestätigt.
- **Waffen-Upgrades (Part 2):** Wie genau Waffen im Verbesserungsmenü upgradebar
  sind — offen.
- **Wellen-Skalierung:** ✅ Zahl gekappt (Hybrid-Cap, ADR 006) + HP super-linear
  (ADR 012) + Boss-Multiplikatoren ×2/×3 (ADR 013) + XP-Wellenskalierung (ADR 014). Modell:
  alle Bosse im Walk-Budget. Folge-Frage: trägt es über einen echten 1→100-Lauf? — offen.
- **Spieler-Progression (ADR 014):** ✅ Kill-XP skaliert jetzt mit der Welle (`1+wave//8`) →
  Modell-Endlevel ~98 statt 33. Folge-Frage: **Level-Inflation** — verwässert ~98 die Build-
  Entscheidung (fast alle Karten)? Gegen-Hebel = größeres `XP_WAVE_DIV` + niedrigeres `SQ`. —
  offen bis Playtest.
- **Elite-Reward (ADR 011):** ✅ Umgesetzt → `ELITE_REWARD_MULT=5` (×5 Münzen **und** XP).
  Folge-Frage: ist ×5 gegen ×10 HP der richtige Punkt? (Playtest-Regler.)
- **Autoaim-Priorisierung (ADR 010):** zielt simpel auf den **nächsten** Gegner. Reicht
  das, oder braucht es „gefährlichster/zähester zuerst" (z. B. Elites priorisieren)?
- **Genre-Identität:** Mit Passiv-Combat ist der „Clicker"-Anteil weg — woher kommt die
  aktive Spannung? **Teil-Antwort (ADR 034):** erste aktivierbare Fähigkeit **Overdrive**
  (Leertaste, Burst). Folge-Fragen: reicht eine Fähigkeit, oder braucht es mehrere (Meteor/
  Schockwelle waren die Alternativen)? Ist das Timing-Fenster spürbar? — offen bis Playtest.

## Geplante Features / Backlog

- **Beleuchtung im Spiel** (geplant, Visual-Polish-Strang im Geist von ADR 035 „Juice"). Ziel:
  dynamisches Licht für mehr Atmosphäre/Tiefe — z. B. ein weiches Licht/Glow am Turm, leuchtende
  Projektile/Mündungsblitze, ein dunkleres Arena-Vignetting mit Lichtinseln, ggf. tier-eigene
  Lichtstimmung (Friedhof kühl, Lava warm/rot, Eis blau). **Ansatz (zu klären):** 2D-Light-Layer
  als additive Surface (`BLEND_RGB_ADD`) über `world_surf` gerendert — passt zum bestehenden
  FX-Muster (`game/fx.py`, additive Partikel) und braucht keinen Shader. Offene Punkte: Umfang
  (nur Turm/Projektile vs. voll dynamisch), Performance bei Zeitraffer x20, Lesbarkeit der
  Gegner-Sprites bei abgedunkelter Szene. Noch kein ADR — entsteht beim Umsetzen, sobald
  Abwägung (Look ↔ Performance ↔ Lesbarkeit) ansteht.

## Decision log

Trivia-Entscheidungen (echte Abwägungen → ADR in `docs/decisions/`):

- **D31** — **Speicherstand-Slots vor dem Hauptmenü** → **ADR 019**. Aktiv-Slot-Modell in
  `save_data` (bestehende `sd.save`-Aufrufe unverändert), 3 `save_slot<N>.json`, `SLOT_SELECT`
  als Einstiegs-State, Migration der Alt-`save.json` in Slot 1. **Bugfix:** Migration löscht das
  Original + `delete(1)` entfernt auch die Legacy-Datei (sonst „untötbarer" Slot 1).
- **D32** — **FPS-Regler + Zeitraffer-Multiplikator** → **ADR 020**. FPS 75→140, Regler in den
  Optionen; Speed-Button als **ausklappbares Dropdown x1/x2/x3/x5/x10/x20** = Update-Block läuft
  N×/Frame (Balance identisch), **Taste B** → x1. FPS treibt `clock.tick` und Feuerrate. Ersetzt
  die erste „Spawn-Rate"-Button-Variante. Dazu ein **`CONTROLS`-Screen** (Pause-Menü-Button
  „Steuerung") mit allen Tasten/Bedienelementen.
- **D33** — **Lexikon/Bestiarium** (`BestiaryMenu`, `BESTIARY`-State): Gegner-Katalog mit Stats,
  nur gesehene enthüllt (`seen_enemies` je Slot). Reine UI/Daten, kein ADR (keine Abwägung).
- **D34** — **SuperBoss-Drache: Schweben → geerdeter Walk** (ADR 016 aktualisiert) + Code-only
  Angriffs-Lunge. Detailliertes KI-Bild freigestellt (strikter „nur reines Schwarz"-Pass gegen
  die eingeschlossene Flügel-Tasche), fußverankert animiert.
- **D35** — **Balance-Tweaks (reine Werte, Playtest-Regler):** `ELITE_HP_MULT 10→3`;
  **+10 % XP je Welle** (`xp_round_mult`, linear); Wellen-Härte (+40 %/10 W) auf Nutzerwunsch
  **zurückgesetzt** (`WAVE_TIER_MULT=1.0`); **Gegner „viel zu stark" → `ENEMY_HP_GLOBAL_MULT
  0.8→0.25`** (globaler Stärke-Regler stark runter).
- **D36** — **Tuning-Sprint (reine Werte):** `BASE_DAMAGE 10→15` (+50%); Gegner langsamer
  (`min(1.1+wave·0.10, 2.4)`); `CAMERA_ZOOM 1.2→1.4`; `XP_GAIN_MULT 1.7` (+70%);
  `COIN_GAIN_MULT 1.5` (+50%); Elite-HP gestuft (`elite_hp_mult`, +100%/10 W additiv);
  `BOSS_HP_MULT 6→12` / `SUPERBOSS_HP_MULT 10→20` (+100%). Alle als benannte Regler in balance.py.
- **D37** — **Gestufter Doppelschuss-Shop + begrenzte Angriffsreichweite + Aufgeben behält Gold**
  → **ADR 022**. Doppelschuss = capped Upgrade (5000/20000); `PLAYER_ATTACK_RANGE` aus Zoom
  abgeleitet (Kills im Bild); Pause→Hauptmenü bucht `gs["coins"]`.
- **D38** — **SessionStart-Hook** → **ADR 021**. `tools/session_status.py` + `.claude/settings.json`
  speisen den Projekt-Status (Current focus/Next step + neuestes ADR) bei jedem Start ein.
- **D39** — **Doc-Drift behoben (reine Doku, keine Abwägung), Commit `5830dfa`:** ADR-Index
  (`docs/decisions/README.md`) um **023–026** ergänzt; `roadmap.md` Sieg-Welle **100→150** (ADR 024)
  + Gate-Dev-Taste F3→F4; `architecture.md` §11 Boss-HP auf aktuelle **×5-Werte** (`BOSS_HP_MULT 60` /
  `SUPERBOSS_HP_MULT 100`, Quelle `balance.py:77-78`) + Dev-Tasten **F4/F5** ergänzt. Historie der
  alten Werte (ADR 013/018) bewusst stehen gelassen.
- **D40** — **Necromancer/Lich-Soft-Lock behoben (Bugfix, Playtest):** `ATTACK_RANGE 240→220`
  (musste `< PLAYER_ATTACK_RANGE ≈ 236,6` werden, sonst kitete der Beschwörer außer Turm-Reichweite
  → unkillbar als letzter Gegner nach `SUMMON_MAX`) + **Übergangs-Pfeilangriff** (`SHOOT_EVERY=110`,
  `pop_shots()`, eigenes Geschoss-Sprite via ADR 027). Reiner Fix, kein ADR.
- **D41** — **XP-Kurve linear → quadratisch** → **ADR 028**. `xp_to_next = 8 + 1.0·(level-1)² +
  10·wave`; Level 100 ≈ 10000 XP (war ~850), Modell-Endlevel ~72 statt ~195. Option A (10000 wörtlich,
  Level 100 = Fernziel) vom Nutzer gegen Option B/C gewählt; Tradeoff-Abwägung im ADR.
- **D42** — **Quell-/Geschoss-Sprite-PNGs aus Git genommen (Commit `91db61f`):** Master liegen extern
  in `C:\Users\kings\Desktop\aselfmade assets`; `.gitignore` ignoriert `assets/custom/*_static.png`
  (Tool-Quellen) + `*_shot.png`/`*_cast.png` (Geschosse/Cast). 31 Dateien via `git rm --cached`
  untrackt (lokal bleiben sie). Getrackt bleiben `_run`/`tier*_ground`/`player_tower`/`drache_*`.
  Folge: frische Clones zeigen für Geschosse den Goldpfeil-Fallback (Golden Rule 5).
- **D43** — **Overdrive: erste aktivierbare Spieler-Fähigkeit** → **ADR 034**. Leertaste zündet
  5-s-Burst (×2 Angriffstempo, ×1.5 Schaden), 18 s Cooldown. Multiplikator-an-der-Quelle (kein
  Mutieren von `gs["stats"]`), Timer Sub-Tick-getaktet (Zeitraffer-fest). Erster Schritt gegen die
  Genre-Frage; Alternativen Meteor/Schockwelle verworfen (Nutzerwahl: offensiver Burst).
- **D1** — Doku-Sprache: Deutsch (Code-Bezeichner bleiben Englisch).
- **D2** — Projektziel: Lernen mit echter Veröffentlichungs-Absicht später.
- **D3** — Zielplattform: Windows-Desktop `.exe` (z. B. itch.io). Browser/Mac/Linux
  Backlog. (Detail-Begründung in ADR 001.)
- **D4** — Typische Session: mittel, 15–30 Min.
- **D5** — Bestehende CLAUDE.md: technischer Inhalt → `architecture.md`, CLAUDE.md
  wird Ritual-Datei.
- **D6** — Repo-Struktur: Laufzeit-Module in ein `game/`-Package verschoben
  (`main.py` bleibt Root-Einstieg), `tools/` (generate_assets) und `media/clips/`
  ausgegliedert, `.gitignore` ergänzt. Umzug während Phase 0 passiert; Audio-Pfade
  (`assets/audio/` vs. altem `Gamesounds/`) noch nicht final konsolidiert.
- **D7** — Gegner-Klassen nach Sprite benannt (`Warrior`/`Archer`/`Lancer`); reine
  Umbenennung, die Spawn-Key-Strings `"rusher"`/`"tanker"` bleiben (keine Abwägung).
- **D8** — Gegner belagern den Turm statt bei Kontakt zu sterben → **ADR 005**.
- **D9** — Phase-1-Umzug: UI-Texte/Preise werden aus `balance.py`-Konstanten
  generiert (f-Strings) statt als Literale doppelt gepflegt — Single Source of
  Truth, keine Verhaltensänderung (keine Abwägung, fällt unter ADR 002).
- **D10** — Wellen-Skalierung Phase 2: Hybrid-Cap (Gesamtzahl ≤40 + Concurrent ≤25)
  → **ADR 006**. Sieg-Hook an die bestehende Wellen-Clear-Bedingung gehängt
  (`wave >= WIN_WAVE`), statt separater SuperBoss-Check.
- **D11** — Headless-Run-Skill `.claude/skills/run-roguelite-clicker/` (Treiber +
  SKILL.md): fährt das echte Spiel über SDL-Dummy + gepatchtes `mouse.get_pos`,
  Screenshots zur Verifikation. Agent-Tooling, kein Spiel-Code (keine Abwägung).
- **D12** — ~2h-Rebalance + 1.25x Speed + Kamera-Zoom 1.2x (Post-Render) + Sprites
  1.1x → **ADR 007**. Spielzeit-Rückgrat = deterministischer Spawn-Floor (Gegnerzahl ×
  Interval); Zoom als Post-Render-Schritt (entkoppelt Optik von Logik, Zielen bleibt
  korrekt). Werte kalibriert per Read-only-Modell, Feintuning per Playtest offen.
- **D13** — XP/Level-System: Karten kommen aus Level-ups statt pro Welle; XP = Gegner-
  Münzwert, Schwelle wellenabhängig → **ADR 008**. Dazu Mengen aus ADR 007 revidiert
  (kürzer/tödlicher: Cap 45, ATTACK 22, Player-HP 120). Balance = erster Wurf, Playtest.
- **D14** — Auto-Feuer (LMB halten, Angriffstempo/s) statt Klick + „Angriffstempo"-Karte
  (+10%) + Lifesteal (1 HP/Treffer) + steileres Gegner-HP (·14/Welle) → **ADR 009**.
  Lifesteal pro Treffer (nicht pro Schadenspunkt); Angriffstempo multiplikativ.
- **D15** — Playtest-Tuning (reine Werte): `BASE_ATTACK_SPEED 0.60→1.0`, Gegner-HP-Scaling
  `·14→·10`, `BASE_SPAWN_INTERVAL 58→40`. Kehrt zwei ADR-009-Kalibrierungen um;
  „Nachjustiert"-Hinweis in ADR 009 ergänzt.
- **D16** — Levelup-Karten-Screen 0.75 s klick-gesperrt (`LEVELUP_INPUT_LOCK_S`), damit
  gehaltenes Auto-Feuer keine Karte sofort fehl-wählt; Hover-Hint erst nach Ablauf.
- **D17** — **Voll-Auto-Feuer + Autoaim** (kein Halten/Maus-Zielen mehr; Turm feuert auf
  nächsten Gegner) → **ADR 010**. Löst das Feuer-Modell aus ADR 009 ab; LMB-Spam getötet
  (kein `fire_timer`-Reset beim Klick). `mouse_held` komplett entfernt.
- **D18** — Angriffstempo-Karte **additiv** `+0.2/s` (war `×1.10`) + `BASE_ATTACK_SPEED
  1.0→1.5` (reine Werte/Feel, unter ADR 010; additiv = planbar, kein Snowball).
- **D19** — Gegner-Sprites größer: `ENEMY_SPRITE_SCALE=1.25` via neuem `_epx()` —
  getrennt vom Turm (`_TOWER_SIZE`) und von Projektilen (keine Abwägung, Playtest-Knopf).
- **D20** — Weniger/gestreckter Spawn: `BASE_SPAWN_INTERVAL 40→60`, `MAX_ENEMIES_PER_WAVE
  45→30` (reine Werte, Playtest).
- **D21** — **Elite-Gegner**: 10% je Nicht-Boss-Spawn = `ELITE_HP_MULT=10`-fache HP +
  roter Ring → **ADR 011**. `elite`-Klassenattribut auf `Warrior`; Bosse ausgenommen;
  Mehr-Reward bewusst noch offen.
- **D22** — Anti-Snowball: XP-Kurve versteilt `XP_BASE 5→8`, `XP_PER_LEVEL 3→7` (gegen
  „Durchlaufen ab Lvl 10"; reine Werte, Playtest).
- **D23** — Elite-Reward skaliert: `ELITE_REWARD_MULT=5` über `enemy.coin_value` (×5
  Münzen UND XP, da `coin_value` beides speist). ×5 statt ×10 (HP-linear), um die
  Anti-Snowball-XP-Kurve nicht auszuhebeln. Löst die offene Reward-Frage aus ADR 011.
- **D24** — **Gegner-HP super-linear** → **ADR 012**:
  `enemy_hp_for_wave` von linear `30+Welle·10` auf `ENEMY_HP_BASE + Welle·ENEMY_HP_PER_WAVE
  + Welle²·ENEMY_HP_PER_WAVE_SQ` (30/12/0.9). Grund: Spielerkraft skaliert multiplikativ,
  linear kann nie mithalten → Welle 100 war trivial (Level-17-Build via F4 schlug
  SuperBoss). Faktor W17→100 jetzt ~20× (war 5×); SuperBoss 25,7k→255k HP. Zahlen = erster
  Wurf, Playtest (Regler `ENEMY_HP_PER_WAVE_SQ`). **F4 ist Debug-Sprung — kein gültiger
  Endgame-Balance-Test, da Level/Stats eingefroren.**
- **D25** — **Stats-Overlay auf Taste C** (Spieler-Feature, kein Dev-Key): `draw_stats_panel`
  zeigt Schaden/Angriffstempo/Kugel-Stats/Multishot/Durchschlag/Lifesteal/HP, liest direkt
  aus `gs["stats"]`+`balance` (keine gespiegelten Werte). `show_stats`-Toggle; Dev-Hint
  um „C Stats" ergänzt.
- **D26** — **Boss-HP-Multiplikatoren ×8/×25 → ×2/×3** → **ADR 013**. Datengestützt per
  neuem read-only Modell `tools/balance_model.py` (kein Spiel-Code): Spieler endet ~Level 33
  (Kill-XP nicht wellenskaliert), Boss = DPS-Rennen gegen Anlaufzeit → alte Multiplikatoren
  = unfaire Wand ab ~W40. Neue Konstanten `BOSS_HP_MULT`/`SUPERBOSS_HP_MULT` in `balance.py`
  (vorher Magic Numbers in `enemy.py`). Bewusst nur dieser eine Hebel; zweiter Hebel
  (`ENEMY_HP_PER_WAVE_SQ`/XP-Kurve) für W60+ offen. Revidiert die „×8/×25 bleiben"-Festlegung
  aus ADR 012.
- **D33** — **Boss-Wand als Meta-Gate für ~5 Läufe bis Welle 100** → **ADR 018** (revidiert
  ADR 013/014). `BOSS_HP_MULT 2→6`, `SUPERBOSS_HP_MULT 3→10`, `PERMANENT_DAMAGE_PER_LEVEL
  15→25`, `COST_MULT 1.65→1.4`; kalibriert per neuem `tools/balance_model_runs.py`. Boss-Mult
  allein = brüchige Klippe → vier Hebel zusammen. Vorbehalt: Modell ignoriert HP-Tod durch
  die ×10-Normalgegner.
- **D32** — **Spiel-weiter Feel-Umbau (reine Werte, Nutzerwunsch):** Gegner ~30 % langsamer
  (`enemy_speed_for_wave = min(1.5+wave·0.13, 3.2)`); `CAMERA_ZOOM 1.2→1.4` (statt SPRITE_SCALE,
  da Post-Render-Zoom = alles inkl. Boss/Spieler, Hitboxen unberührt); neue Gegner-HP **×10**
  (Goblin ×2.5/Ork ×25/Nekro ×6 der Basis-HP — bewusst sehr zäh, Ork > SuperBoss); `save.json`
  zurückgesetzt. Optik der animierten Sprites via `tools/animate_walk.py` (kein ADR — Werte/Tooling).
- **D31** — **Drei neue Gegnerklassen** (Goblin/OrcBerserker/Necromancer) → **ADR 017**.
  Schwarm/Brecher/Beschwörer füllen die Druck-/Build-Tiefe-Lücke; alle subklassen `Warrior`
  mit Fallback-Sprites (Golden Rule 5), HP/Speed-Faktoren inline (wie Lancer/Monk),
  Verhalten (`SUMMON_*`, `DAMAGE_MULT`) als benannte Konstanten. Spawn welleabhängig
  gewichtet (W5/W8/W12). Necromancer-Summons via `pop_summons()` nach der Update-Schleife
  angehängt (kein Mutieren während Iteration), umgehen aber `MAX_CONCURRENT_ENEMIES`
  (per `SUMMON_MAX` gedeckelt). Sprites + Balance noch offen.
- **D30** — **SuperBoss fliegt: animierter Drache** → **ADR 016** (ersetzt D29/ADR 015).
  Sauberes 5×5-Spritesheet (25 Frames, Alpha, kein Wasserzeichen) → 25-Frame-Strip
  `drache_superboss_fly.png`; `load_drache_superboss(target_w)` slict + `smoothscale`t
  (Seitenverhältnis erhalten); Animation gratis über `Warrior.update`; „Fliegen" = visueller
  `FLY_LIFT`+Sinus-Bob in `draw` (`self.pos` bleibt am Boden → Kollision unverändert).
  `SPRITE_PX` 170→240. Walk-GIF als Quelle verworfen (Wasserzeichen/weißer BG).
- **D29** — **SuperBoss = Pixel-Art-Drache** → **ADR 015** (abgelöst von D30/ADR 016). Drachen-
  Artwork zu 96×96-Pixel-Art heruntergerechnet (`assets/custom/drache_superboss.png`),
  `load_drache_superboss()` NEAREST-skaliert, `SuperBoss` nutzt es statt Lancer (`RADIUS` 60,
  `SPRITE_PX` 170, Spawn nur Ost/West). Tradeoff Stil-Bruch (Pixel vs. Tiny-Swords) bewusst
  akzeptiert.
- **D28** — **Animierter Drachenlord-Sprite verworfen.** SuperBoss aus KI-Video (Frame-Pipeline)
  gebaut, vom Nutzer optisch abgelehnt, vollständig zurückgerollt (nie committet). Ersetzt durch
  D29 (Pixel-Art-Standbild).
- **D27** — **XP pro Kill skaliert mit der Welle** → **ADR 014** (zweiter Endgame-Hebel).
  `gs["xp"] += enemy.coin_value * xp_wave_mult(wave)`, `xp_wave_mult = 1+wave//XP_WAVE_DIV`,
  `XP_WAVE_DIV=8` (neu in `balance.py`). Modell-gesweept: Lever A (SQ senken) allein reicht
  nicht, voller Münzfaktor überschießt (Level 164) → gedämpftes `//8` = Endlevel ~98, 0/10
  Bosse über Budget. Bewusst „Root-Fix pur" (nur XP, HP unverändert) statt HP-lastiger Combo;
  Risiko Level-Inflation akzeptiert. Löst die offene Progressions-Frage aus ADR 013.

## Phase → ADR map

- **Phase 0** (Doc-System) → ADR 001, 002, 003, 004 (alle hier festgehalten).
- **Gameplay-Politur** (Belagerung) → ADR 005.
- **Phase 1** (`game/balance.py`) → ADR 002 (Tuning zentral, JSON später).
- **Phase 2** (Welle 100 + Sieg) → ADR 004 (Run-Modell), ADR 006 (Wellen-Cap).
- **Phase 3** (Inhalt) → ADR 002 (neue Werte nach `game/balance.py`), ADR 003 (Struktur),
  ADR 010 (Passiv-Combat/Autoaim), ADR 011 (Elite-Gegner), ADR 012 (HP-Scaling super-linear),
  ADR 013 (Boss-Multiplikatoren ×2/×3), ADR 014 (XP-Wellenskalierung),
  ADR 015 (SuperBoss-Pixel-Art-Drache, abgelöst), ADR 016 (SuperBoss-Drache animiert → Walk),
  ADR 017 (drei neue Gegnerklassen: Goblin/OrcBerserker/Necromancer),
  ADR 018 (Boss-Wand als Meta-Gate, ~5 Läufe; revidiert ADR 013/014),
  ADR 019 (Speicherstand-Slots), ADR 020 (FPS-Regler + Zeitraffer-Multiplikator),
  ADR 022 (gestufter Doppelschuss-Shop + begrenzte Angriffsreichweite + Aufgeben behält Gold).
- **Tooling/Workflow** → ADR 021 (SessionStart-Status-Hook).
- **Phase 4** (Verpacken) → ADR 001 (Python/Pygame → PyInstaller).
- **Part 2** (Rebirth/Waffen) → ADR 004.

## Phase status

- **Phase 0 — Doc-System:** ✅ Gate erfüllt (2026-06-20). Nachweis: alle Doc-Dateien
  + ADR 001–004 existieren, Ist-Stand mit Code abgeglichen.
- **Phase 1 — `balance.py`:** ✅ Gate erfüllt (2026-06-20). Nachweis: `game/balance.py`
  existiert mit allen Tuning-Zahlen; Spiel startet fehlerfrei; Test bestätigt
  byte-identische UI-Strings/Preise + Werte-Gleichheit (reiner Umzug, Balance
  unverändert).
- **Phase 2 — Welle 100 + Sieg:** ✅ Code-Gate erfüllt (2026-06-20). Nachweis: der
  neue Headless-Treiber (`.claude/skills/run-roguelite-clicker/driver.py`) fuhr im
  echten Spiel Menü → Lauf starten → F4/W99 → Upgrade wählen → Welle 100/SuperBoss →
  **Sieg-Screen** und screenshottete alle Stufen (`shots/01..05`). Offen bleibt nur
  das **Balance-Feintuning** eines durchgespielten 1→100-Laufs (HP/Speed vs. DPS).
- **Phase 3 — Inhaltszuwachs:** angefangen (2026-06-20). Erste Inhalte: Passiv-Combat +
  Autoaim (ADR 010), Elite-Gegner + Reward (ADR 011), super-lineares HP-Scaling (ADR 012),
  Stats-Overlay (C), Boss-Multiplikatoren entschärft (ADR 013) + Balance-Modell-Tool, XP-
  Wellenskalierung (ADR 014), SuperBoss animierter Flug-Drache (ADR 016), drei neue
  Gegnerklassen Goblin/OrcBerserker/Necromancer (ADR 017, Sprites noch ausstehend). Noch
  offen: weitere Karten/Upgrades (Crit, Explosiv/Kette, DoT, Regen, Dornen, Reroll …) + ein
  echter 1→100-Balance-Lauf (inkl. Level-Inflations- + Neue-Gegner-Check); alles per Playtest.
- **Phase 4 — Politur & `.exe`:** offen
- **Part 2 — Rebirth/Waffen:** offen (Backlog)

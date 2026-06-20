# architecture.md — Die Design-Wahrheit

Diese Datei beschreibt, **wie das Spiel technisch aufgebaut ist und warum**. Bei
Design-Unklarheit gewinnt diese Datei. Wer eine Design-Entscheidung ändert,
aktualisiert `architecture.md` im selben Change.

Lesereihenfolge: nur bei Design-Aufgaben laden (nicht jede Session). Der Plan
steht in `roadmap.md`, der aktuelle Stand in `progress.md`, einzelne Entscheidungen
mit Abwägung in `docs/decisions/`.

---

## 1. Overview & Design-Prinzipien

2D-Roguelite × Tower-Defense × Clicker (Python + Pygame). Der Spieler ist ein
**stationärer Turm** in der Bildschirmmitte; der Turm **feuert voll-automatisch** im
Angriffstempo und **zielt selbst auf den nächsten Gegner** (Autoaim, ADR 010) — keine
Maus-/Klick-Eingabe im Kampf. Treffer heilen den Spieler (Lifesteal, ADR 009). Gegner
spawnen wellenweise vom Rand und laufen auf den Turm zu; ein Teil von ihnen sind zähe
**Elites** (ADR 011). Kills geben XP; bei jedem **Level-up** wählt man eine von drei
Karten (ADR 008); verdiente Münzen kaufen dauerhafte Verbesserungen.

**Rückgrat ist die Roguelite-Run-Struktur** (Welle → Upgrade wählen → stärker
werden → sterben/neu). Tower-Defense liefert die Gegnerwellen; das Kämpfen läuft
seit ADR 010 **passiv** (Auto-Feuer + Autoaim) — der „Clicker"-Anteil ist nur noch
historisch im Namen, nicht mehr in der Eingabe. Der Spielspaß soll aus
**Build-Vielfalt pro Run** (Upgrade-Kombos) und **dauerhafter Meta-Progression**
entstehen.

Leitprinzipien:

- **Einfachheit vor Eleganz.** Lernprojekt mit Veröffentlichungs-Absicht, solo.
  Wir bauen das Spiel, nicht die perfekte Architektur. Refactor nur, wenn eine
  Stelle wirklich wehtut.
- **Robustheit über Asset-Fallbacks.** Fehlt ein Sprite/Sound, fällt das Spiel
  auf gezeichnete Primitive zurück statt zu crashen.
- **Tuning getrennt vom Verhalten.** Stellschrauben (Zahlen) leben zentral in
  `balance.py`; Logik/Verhalten lebt im Code. Siehe ADR 002.
- **Verifikation durch Starten.** Es gibt kein Test-Setup; jede Änderung wird
  durch `python main.py` geprüft.

Sprach-Konvention: **Bezeichner Englisch, Kommentare und alle UI-Texte Deutsch.**
Diese Doku ist auf Deutsch.

---

## 2. Tech-Stack & Topologie

- **Sprache/Engine:** Python + Pygame. Einzige Pflicht-Abhängigkeit:
  `pip install pygame`. `numpy` optional (Cannonball-Hintergrund-Cropping).
  Begründung und verworfene Alternativen: ADR 001.
- **Zielplattform:** Windows-Desktop als `.exe` (z. B. itch.io). Verpacken
  später via PyInstaller (Phase 4). Browser-Version (pygbag) ist Backlog.
- **Fenster:** fest **1280×720**, mit `pygame.SCALED`. **75 FPS** Ziel (= 1.25x
  Spielgeschwindigkeit, alles frame-basiert; ADR 007/008).
- **Kein Build-Schritt, keine Tests, kein Linter, keine `requirements.txt`.**
- **Kein Git** im Repo initialisiert (Stand Phase 0). Committen nur auf
  ausdrückliche Aufforderung.

Startbefehl:

```bash
python main.py
```

Dev-Tasten (nur im `PLAYING`-State):

- **F1** — alle Gegner sofort töten (löst Wave-Clear aus)
- **F2** — auf Welle 9 springen (nächster Clear → Boss in Welle 10)
- **F3** — auf Welle 49 springen (nächster Clear → SuperBoss in Welle 50)
- **F11** — Fullscreen toggeln · **ESC** — Pause / zurück

---

## 3. Komponenten / Module

Das Spiel ist eine **einzige `while running`-Schleife** in `main.py` (Root), plus
ein `game/`-Package mit Entitäts- und UI-Modulen. Diese Struktur bleibt bewusst so
(ADR 003). `main.py` importiert aus dem Package via `from game.<modul> import ...`.

| Modul | Zweck |
|---|---|
| `main.py` (Root) | State-Machine + Game-Loop (Event/Update/Draw), Wellen-Logik, Trefferprüfung, alle Helfer. Das Herz. Einstiegspunkt. |
| `game/constants.py` | Fenster-/FPS-/Farb-Konstanten. |
| `game/player.py` | `Player` (Turm): HP, Schaden nehmen, Turm-Sprite + HP-Bar zeichnen. |
| `game/enemy.py` | Alle Gegnerklassen mit Lazy-Sprite-Pattern (siehe §4). |
| `game/projectile.py` | `Projectile` (Spieler-Geschoss): Bewegung, Kanonenkugel-Sprite/Fallback. |
| `game/upgrade_menu.py` | In-Run-Karten (`UPGRADES`) + Auswahl-Overlay bei Level-up. |
| `game/main_menu.py` | `MainMenu`, `OptionsMenu`, `ImprovementsMenu`, `DIFFICULTIES`, `IMPROVEMENTS`, wiederverwendbare `Button`-Klasse. |
| `game/save_data.py` | Laden/Speichern von `save.json` (Merge mit `_DEFAULT`). |
| `game/sounds.py` | Prozedural erzeugte SFX + Musik-Wiedergabe. |
| `game/sprite_loader.py` | Lädt Unit-Spritesheets (Tiny Swords), schneidet Frame-Strips, spiegelt Links-Frames. |
| `game/ui_loader.py` | Baut Tiny-Swords-UI (HP-Bars, Buttons, Labels) per 3-Slice mit Tight-Crop-Grenzen. |
| `game/terrain.py` | Backt Gras-Hintergrund + verteilt zufällige Deko. |
| `game/fx.py` | `DamageNumber` (aufsteigende Schadens-/Münz-Zahlen). |
| `game/balance.py` | Zentrales Tuning-Datenmodul (Wellen-Formeln, Spawn-/Nahkampf-Werte, Upgrade-Werte, Preise). |
| `tools/generate_assets.py` | Hilfsskript zur Asset-Erzeugung (kein Laufzeit-Modul). |

**`game/balance.py`** (seit Phase 1): Wellen-Formeln (`enemies/​hp/​speed/​coin_for_wave`),
Spawn-/Nahkampf-Konstanten, In-Run-Upgrade-Werte und Münz-Shop-Preise. **Nur
Zahlen + reine Formeln** — Verhalten bleibt in den jeweiligen Modulen. UI-Texte
(z. B. „+10 Schaden") werden aus denselben Konstanten generiert (eine Quelle der
Wahrheit). JSON-Auslagerung weiter Backlog (ADR 002).

> **Hinweis (Stand 2026-06-20):** Das Repo wurde gerade in ein `game/`-Package
> umstrukturiert (vorher lagen alle Module flach im Root). Die Audio-/Asset-Pfade
> sind dabei mitten im Umzug — `game/sounds.py` zeigt auf `assets/audio/Music/`,
> während parallel noch ein altes `Gamesounds/` existiert. Vor Audio-Arbeit den
> realen Pfad per grep prüfen.

### 3.1 State-Machine

`main.py` hält einen State-String und verzweigt in **Event-, Update- und
Draw-Phase** darauf. **Beim Hinzufügen von Verhalten muss man typischerweise an
allen drei Stellen denselben State behandeln.**

States: `MAIN_MENU`, `OPTIONS`, `IMPROVEMENTS`, `PLAYING`, `WAVE_CLEAR`,
`UPGRADE`, `PAUSED`, `GAME_OVER`, `VICTORY`.

`VICTORY` (seit Phase 2): erreicht, sobald Welle `WIN_WAVE` (100) geräumt ist
(SuperBoss besiegt). Eigener Sieg-Screen; R = neuer Lauf, M = Menü — Event/Draw
teilen sich die Logik mit `GAME_OVER`, die Update-Phase ist (wie `GAME_OVER`) ein
No-Op.

### 3.2 Laufzustand `gs`

Der laufende Spielzustand lebt im Dict **`gs`** (erzeugt von
`fresh_game_state()`): `wave`, `enemies`, `projectiles`, `enemy_projectiles`,
`pending_shots`, `stats`, `coins`, `obtained`, `spawn_remaining`, `spawn_timer`,
`wave_clear_timer`, `banner`, `fire_timer` (Auto-Feuer, ADR 009), sowie XP/Level
(`xp`, `level`, `xp_to_next`, `pending_levelups`; ADR 008) u. a. `gs is None` bedeutet
„kein aktiver Lauf"
(`run_active` im Hauptmenü). Beide Wege ins Menü — Pause→Menü **und**
Beide Run-Enden ins Menü (GAME_OVER **und** VICTORY) — setzen `gs = None`, damit
der **Verbesserungen-Shop** dort erreichbar ist; permanente Käufe ergeben nur
außerhalb eines Laufs Sinn.

`gs["stats"]` hält die In-Run-Werte: `damage`, `bullet_speed`, `bullet_size`,
`pierce`, `multishot`, `attack_speed` (Schüsse/Sek., ADR 009).

---

## 4. Gegner: Lazy-Sprite-Pattern

Alle Gegner erben von der Basisklasse `Warrior` (die zugleich der Standard-
Nahkämpfer ist). Sprites werden **klassenweise** und **faul**
geladen: jede Klasse hat `_frames_r = None` / `_frames_l = None` als Klassen-Cache,
und `_load_sprites()` (classmethod) lädt einmalig per `try/except`. Schlägt das
Laden fehl, wird auf gezeichnete Primitive (Kreise) zurückgefallen —
`_blit_sprite()` gibt `False` zurück und `draw()` zeichnet den Fallback.

**Jede neue Gegnerklasse muss eigene `_frames_r/_frames_l`-Klassenvariablen
deklarieren**, sonst greift sie über die MRO auf die der Basisklasse zu.

Gegnertypen:

- `Warrior` (Nahkampf, Standard) — zugleich die Basisklasse aller Gegner
- `Archer` (Fernkampf, erzeugt `EnemyProjectile`) — Spawn-Key „rusher"
- `Lancer` (Tank, 5 Richtungs-Angriffsanimationen) — Spawn-Key „tanker"
- `Monk` (Heiler, heilt Nachbarn + Heal-FX)
- `Boss` (alle 10 Wellen), `SuperBoss` (alle 50) — beide nutzen die Lancer-Sprites
  und töten den Spieler mit einem Treffer.

Wave-Skalierung über die `*_for_wave()`-Funktionen oben in `main.py`. Einhängen
neuer Gegner in `spawn_enemy_for_wave()`.

---

## 5. Daten-/Simulationsfluss pro Tick

Pro Frame im `PLAYING`-State (vereinfacht):

1. **Spawnen:** Timer zählt; bei Ablauf spawnt `spawn_enemy_for_wave()` einen
   Gegner, bis `spawn_remaining` aufgebraucht ist. Spawn-Intervall hängt vom
   Schwierigkeitsgrad ab (`diff_mod["spawn_bonus"]`). Jeder Nicht-Boss-Spawn wird mit
   `ELITE_SPAWN_CHANCE` zum **Elite** (`ELITE_HP_MULT`-fache HP, roter Ring; ADR 011).
2. **Update:** alle Geschosse, Gegner-Geschosse, Gegner und FX bewegen sich.
   **Voll-Auto-Feuer + Autoaim (ADR 010):** sobald `fire_timer <= 0` und ein Gegner
   existiert, feuert der Turm auf den nächsten Gegner (`nearest_enemy_pos()`) im Takt
   `FPS / attack_speed`; ohne Ziel bleibt der Timer ≤0 (sofortiger Schuss beim ersten
   Gegner). Keine Maus-/Klick-Eingabe. Doppelschuss-Nachzügler laufen über `pending_shots`.
3. **Kollisionen:** `check_projectile_hits()` (Spieler-Geschoss → Gegner, mit
   Pierce-/Multishot-Logik; je Treffer **Lifesteal** `LIFESTEAL_PER_HIT` HP),
   `check_enemy_contact()` (Gegner → Turm). Nahkämpfer **stoppen vor dem Turm und
   greifen auf Cooldown an** (`melee_attack()`, `ATTACK_DAMAGE`/`ATTACK_COOLDOWN`);
   Kontakt **tötet den Gegner nicht** — nur Projektile töten ihn. Boss/SuperBoss
   bleiben bei Berührung sofort tödlich.
4. **Münzen/FX:** Kills geben Münzen (`coin_value_for_wave()`, optional ×1.5 bei
   `gold_boost`), erzeugen `DamageNumber`-FX.
5. **XP/Level (ADR 008):** Jeder Kill gibt XP (`enemy.coin_value`); erreicht `xp` die
   wellenabhängige Schwelle `xp_to_next(level, wave)`, gibt es einen Levelup
   (`pending_levelups`). Bei offenem Levelup geht `PLAYING` → `UPGRADE` (1-aus-3-Karte,
   **keine** Wellen-Erhöhung) und danach zurück. Karten kommen **nur** aus Level-ups.
6. **Wellen-Ende:** keine Gegner mehr + `spawn_remaining == 0` → `WAVE_CLEAR` → nach
   kurzem Delay **direkt zur nächsten Welle** (`WAVE_CLEAR` rückt `wave` vor, setzt
   Boss-Banner/-Musik). War es Welle `WIN_WAVE` (100), stattdessen → `VICTORY` (Sieg).
   Tod des Turms → `GAME_OVER`. **Spawn-Gate:** pro Welle max. `MAX_ENEMIES_PER_WAVE`
   Gegner gesamt, und es wird nur nachgespawnt, solange weniger als
   `MAX_CONCURRENT_ENEMIES` leben (deckelt Performance + Belagerungs-DPS).

**Wichtig: Simulation und Rendering sind nicht getrennt** — jede Entität hat
`update()` und `draw()` und läuft im Immediate-Mode-Stil von Pygame. Das ist für
dieses Spiel bewusst akzeptiert (kein Determinismus-/Netcode-Bedarf). Kein
Golden-Rule-Zwang zur Trennung.

**Kamera-Zoom & Sprite-Größe (ADR 007):** Die **Welt** (Terrain + Entitäten +
Schaden-FX) wird in ein `world_surf` gezeichnet; `blit_world_zoomed()` skaliert deren
zentralen `1/CAMERA_ZOOM`-Ausschnitt formatfüllend auf den Screen. **HUD, Banner,
Menüs und Cursor** werden danach **unskaliert** direkt auf den Screen gezeichnet.
Skaliert wird um die Bildmitte (= Turm), daher bleiben Schussrichtungen korrekt.
Zusätzlich vergrößert `SPRITE_SCALE` alle Einheiten-/Geschoss-Sprites beim Laden
(`sprite_loader._px()`); Hitboxen (`RADIUS`) bleiben unverändert. **Spieltempo** =
`constants.FPS` (75 = 1.25x), da alles frame-basiert ist.

---

## 6. Content-Pipeline (Tuning vs. Verhalten)

**Aktueller Zustand (seit Phase 1):** Tuning-Zahlen liegen zentral in
`game/balance.py` — Wellen-Formeln (`enemies_for_wave`, `enemy_hp_for_wave`,
`enemy_speed_for_wave`, `coin_value_for_wave`), Spawn-/Nahkampf-Konstanten,
In-Run-Upgrade-Werte und Münz-Shop-Preise. Gegner sind weiter Klassen, der
Gegner-Mix eine gewichtete Zufallswahl je Wellenbereich in
`spawn_enemy_for_wave()`; die Upgrade-/Shop-**Listen** bleiben in
`upgrade_menu.py` / `main_menu.py`, ziehen ihre Zahlen aber aus `balance.py`.

**Designprinzip:** Tuning-Zahlen zentral in `game/balance.py`
(Python-Datenmodul mit Tabellen/Dicts) — **kein JSON** zunächst. Vorteil:
Balancing-Stellschrauben an einem Ort, mit Syntax-Check und Kommentaren, ohne
neue Technik. Verhalten (Gegner-KI, Schussmuster) bleibt im Code.

**JSON** ist explizit später (Backlog), falls externe Balancing-Tools oder
Modding nötig werden. Begründung + Alternativen: ADR 002.

---

## 7. Save / State-Modell

`save.json` wird via `save_data.load()` mit `_DEFAULT` gemerged (fehlende Keys
aufgefüllt). „Harter" Zustand (überlebt Programm-Neustart):

- `total_coins`, `best_wave`, `best_coins`
- `bought` — einmalige Käufe (`"doppelschuss"`, `"gold_boost"`)
- `upgrades` — Stufenzähler permanenter Verbesserungen (`start_damage`, `start_hp`)
- `settings` — **als Integer-Indizes**, nicht als Rohwerte: `sfx`/`music` 0–10
  (→ Lautstärke `idx/10`), `difficulty` = Index in `DIFFICULTIES`, `fps` 0/1.

Zwei getrennte Upgrade-Systeme:

1. **In-Run-Karten** (`upgrade_menu.py`): temporär, nur aktueller Lauf; Auswahl **bei
   Level-up** (XP-getrieben, ADR 008). Wirken über `apply_upgrade()` auf `gs["stats"]`
   bzw. den `Player`.
2. **Permanente Verbesserungen** (`main_menu.py`, `ImprovementsMenu`): mit Münzen
   gekauft, persistiert. `_ONE_TIME` (einmalig) und `_INFINITE` (stufenweise,
   Preis ×`_COST_MULT`). Angewendet via `apply_permanent_bonuses()` zu Laufbeginn
   bzw. inline (`"gold_boost" in save["bought"]`).

**Geplante Erweiterung (Part 2, Rebirth):** Das Save-Format bekommt
freigeschaltete **Waffen** und deren Meta-Upgrades. Diese überleben als Einzige
einen Rebirth — siehe §8 und ADR 004.

---

## 8. Run-Modell & Rebirth (Sieg-Bedingung)

**MVP-Sieg (seit Phase 2):** **Welle `WIN_WAVE` (100) räumen = den SuperBoss
besiegen = gewonnen.** Der `VICTORY`-State zeigt einen Sieg-Screen; `best_wave`/
`best_coins`/`total_coins` werden gebucht, der Lauf endet sauber (R = neuer Lauf,
M = Menü). Damit Welle 100 überhaupt erreichbar bleibt, deckelt Phase 2 die
Gegnerzahl (`MAX_ENEMIES_PER_WAVE` gesamt + `MAX_CONCURRENT_ENEMIES` gleichzeitig);
Schwierigkeit kommt spät v. a. über HP/Speed-Skalierung statt Masse. Begründung:
ADR 006. (Vorher war das Spiel endlos.)

**Rebirth (Part 2, nicht im MVP):** Nach dem Sieg wird das Spiel **komplett
zurückgesetzt** (Run, Münzen, permanente Verbesserungen). Als Belohnung wählt man
per Karte **1 von 3 Waffen**, behält diese **dauerhaft** und kann sie im
Verbesserungsmenü **upgraden**. Nur Waffen + Waffen-Upgrades überleben einen
Rebirth.

Offene Design-Punkte (siehe `progress.md`):

- **Waffe = anderes Schussverhalten** (Arbeitsannahme, z. B. Schrot/Laser/Bumerang;
  vor dem Run gewählt). Noch nicht final.
- **Wie genau** Waffen-Upgrades im Verbesserungsmenü funktionieren: offen.

Begründung + Alternativen (endlos-Highscore vs. Sieg vs. beides): ADR 004.

---

## 9. Sound

SFX werden **prozedural zur Laufzeit erzeugt** (`_sine`/`_sweep`/`_concat`-Buffer
→ `pygame.mixer.Sound`), keine SFX-Dateien. Musik dagegen sind `.ogg`-Dateien
(Pfad gerade im Umzug — `game/sounds.py` zeigt auf `assets/audio/Music/`, altes
`Gamesounds/` existiert noch parallel). `init_mixer()` muss **vor** `pygame.init()` laufen —
deshalb steht `import sounds; sounds.init_mixer()` ganz oben in `main.py`.
Lautstärke getrennt für SFX und Musik; Boss-Musik hat einen eigenen
Dämpfungsfaktor.

---

## 10. Asset-Loader & UI-Konventionen

- **`sprite_loader.py`** — lädt Unit-Spritesheets aus
  `assets/Tiny Swords (Free Pack)/Units/`. `_load_strip()` schneidet horizontale
  Frame-Strips; `_both_dirs()` erzeugt gespiegelte Links-Frames. Frame-Größen pro
  Sheet bekannt (z. B. 192, 320). **Sheet-Breite / Frame-Größe = Frame-Anzahl
  vor dem Laden prüfen.**
- **`ui_loader.py`** — baut Tiny-Swords-UI per **3-Slice** zusammen. Quell-Sprites
  haben transparente Ränder, deshalb arbeiten die `_BAR_SRC`/`_SWD_SRC`/`_RIB_SRC`-
  Specs mit **Tight-Crop-Pixelgrenzen**. Gecacht in `_surf_cache`. **Bei
  UI-Ausrichtungsproblemen sind diese Crop-Werte der erste Verdächtige.**
- **Cursor** ist ein eigenes Sprite (`pygame.mouse.set_visible(False)` + manuelles
  Blit zuletzt vor `display.flip()`).
- **Fonts faul laden:** Menü-Klassen setzen ein `_fonts_ready`-Flag und
  initialisieren Fonts/Icons erst im ersten `draw()`, nicht im `__init__` (Pygame
  evtl. noch nicht voll initialisiert).

---

## 11. Risiken & ehrliche Knackpunkte

- **Wellen-Skalierung bricht bei Welle 100.** `enemies_for_wave` =
  `5 + (Welle-1)·3` ergibt nahe Welle 99 fast 300 Gegner gleichzeitig —
  Performance- und Balancing-Problem. „Welle 100 erreichbar machen" heißt:
  Skalierung überarbeiten (Phase 2). Eventuell Caps, Spawn-Wellen statt
  Dauerstrom, oder gestaffelte Spawns.
- **Performance bei vielen Entitäten.** Kollisionsprüfung ist O(Geschosse ×
  Gegner) ohne räumliche Optimierung. Bei großen Wellen beobachten.
- **Python-Verpackung.** PyInstaller-`.exe` mit Pygame + vielen Assets kann
  zickig sein (Pfade, Asset-Bundling). Phase 4 einplanen, nicht unterschätzen.
- **Wachsende `main.py`.** Bewusst akzeptiert (ADR 003), aber im Auge behalten:
  wenn eine Stelle unübersichtlich wird, gezielt Helfer auslagern.
- **`gs`-Dict ohne festes Schema.** Flexibel, aber tippfehleranfällig. Neue Keys
  konsequent in `fresh_game_state()` dokumentieren.

---

## 12. Projektstruktur

```
roguelite-clicker/
├── CLAUDE.md            # Session-Ritual + Golden Rules (Einstieg jeder Session)
├── architecture.md      # Diese Datei — die Design-Wahrheit
├── roadmap.md           # Phasenplan MVP → Vollversion mit Gates
├── progress.md          # Aktueller Stand, nächster Schritt, offene Fragen
├── .gitignore           # __pycache__, Build-Artefakte
├── docs/
│   └── decisions/       # ADRs (eine Datei je Entscheidung mit Abwägung)
├── main.py              # State-Machine + Game-Loop (Einstiegspunkt, Root)
├── save.json            # Persistenz
├── game/                # Laufzeit-Package (alle Spiel-Module)
│   ├── __init__.py
│   ├── constants.py     # Fenster-/FPS-/Farb-Konstanten
│   ├── player.py        # Turm
│   ├── enemy.py         # Gegnerklassen (Lazy-Sprite-Pattern)
│   ├── projectile.py    # Spieler-Geschoss
│   ├── upgrade_menu.py  # In-Run-Upgrades
│   ├── main_menu.py     # Menüs, Verbesserungen, Button
│   ├── save_data.py     # save.json laden/speichern
│   ├── sounds.py        # prozedurale SFX + Musik
│   ├── sprite_loader.py # Unit-Spritesheets
│   ├── ui_loader.py     # Tiny-Swords-UI (3-Slice)
│   ├── terrain.py       # Hintergrund + Deko
│   └── fx.py            # Schadens-/Münz-Zahlen
├── tools/
│   └── generate_assets.py  # Asset-Hilfsskript (kein Laufzeit-Modul)
├── assets/              # Sprites (+ Audio im Umzug nach assets/audio/)
├── media/
│   └── clips/           # Aufnahmen/Videos
└── Gamesounds/          # Alt-Musikordner (Umzug nach assets/audio/ im Gange)
```

`game/balance.py` (seit Phase 1): zentrales Tuning-Datenmodul.

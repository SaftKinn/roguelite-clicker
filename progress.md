# progress.md

Wo wir stehen, was als Nächstes kommt. Diese Datei ist die laufende Wahrheit über
den Projektzustand — am Ende jeder Session aktualisieren.

---

## Current focus

Phase 0 abgeschlossen (Doc-System, ADR 001–004). Erste Gameplay-Politur am Code
(ADR 005): Gegner-Klassen nach ihren Sprites benannt, Tower-Defense-Kontaktverhalten
umgestellt (Gegner belagern statt zu sterben), Archer-Schuss an den Release-Frame
gekoppelt, einen durch den `game/`-Umzug entstandenen Sprite/Cannonball-Bug behoben
und den Verbesserungen-Shop nach dem Tod wieder zugänglich gemacht. Spiel läuft und
ist spielbar.

## Last session

2026-06-20 — Code-Politur:
- **Gegner-Rename** nach Sprite: `Enemy`→`Warrior` (Basisklasse), `Rusher`→`Archer`,
  `Tanker`→`Lancer`; `Monk`/`Boss`/`SuperBoss` unverändert. Referenzen in `main.py`
  mitgezogen. Spawn-Key-Strings (`"rusher"`/`"tanker"`) bewusst NICHT umbenannt.
- **Belagerungs-Verhalten** (ADR 005): Nahkämpfer stoppen vor dem Turm und greifen
  auf Cooldown an (`melee_attack()`); Kontakt tötet den Gegner nicht mehr — nur
  Projektile. Welle endet erst, wenn der Spieler alle Gegner erschießt.
- **Archer-Schuss** verlässt den Bogen erst am Release-Frame (`SHOOT_RELEASE_FRAME`)
  statt beim Animationsstart.
- **Bugfix:** Faule `import sprite_loader` in `game/enemy.py` (7×) und
  `game/projectile.py` (1×) auf `from . import sprite_loader` umgestellt — nach dem
  `game/`-Umzug schluckte der try/except den ImportError, daher fehlten
  Gegner-Sprites und der Cannonball.
- **Bugfix Shop nach Tod:** GAME_OVER→Menü setzt jetzt `gs/terrain = None` (wie
  Pause→Menü). Vorher blieb der tote Lauf „aktiv", wodurch der Verbesserungen-Button
  per `run_active` ausgegraut war. Münzen waren nie verloren (Zeile 506 schreibt sie
  in `total_coins`) — reines UI-Gating.
- **Doku-Sync:** `architecture.md` §3.2 (gs/Shop-Zugang), §4 (neue Klassennamen),
  §5 (Belagerungs-Kontakt); `roadmap.md` Phase 2 (Belagerung beeinflusst Skalierung);
  ADR 005 angelegt + im `docs/decisions/README.md`-Index ergänzt.

## Next concrete step

**Phase 1 starten:** `game/balance.py` anlegen und die Tuning-Werte dorthin
verschieben — zuerst die `*_for_wave()`-Funktionen + Konstanten aus `main.py`
(`enemies_for_wave`, `enemy_hp_for_wave`, `enemy_speed_for_wave`,
`coin_value_for_wave`, `BASE_SPAWN_INTERVAL`, `MELEE_REACH` sowie die neuen
Nahkampf-Konstanten `ATTACK_DAMAGE`/`ATTACK_COOLDOWN` aus `game/enemy.py`).
Spielbalance dabei NICHT ändern, nur verschieben. Danach In-Run-Upgrade-Werte
(`game/upgrade_menu.py`) und permanente Preise (`game/main_menu.py`).

## Open questions

- **Waffen-Mechanik (Part 2):** Arbeitsannahme „Waffe = anderes Schussverhalten"
  (z. B. Schrot/Laser/Bumerang). Noch nicht final bestätigt.
- **Waffen-Upgrades (Part 2):** Wie genau Waffen im Verbesserungsmenü upgradebar
  sind — offen.
- **Wellen-Skalierung (Phase 2):** Welches genaue Schema macht Welle 100
  erreichbar ohne ~300 Gegner gleichzeitig? (Caps? Spawn-Schübe? gestaffelt?)

## Decision log

Trivia-Entscheidungen (echte Abwägungen → ADR in `docs/decisions/`):

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

## Phase → ADR map

- **Phase 0** (Doc-System) → ADR 001, 002, 003, 004 (alle hier festgehalten).
- **Gameplay-Politur** (Belagerung) → ADR 005.
- **Phase 1** (`game/balance.py`) → ADR 002 (Tuning zentral, JSON später).
- **Phase 2** (Welle 100 + Sieg) → ADR 004 (Run-Modell).
- **Phase 3** (Inhalt) → ADR 002 (neue Werte nach `game/balance.py`), ADR 003 (Struktur).
- **Phase 4** (Verpacken) → ADR 001 (Python/Pygame → PyInstaller).
- **Part 2** (Rebirth/Waffen) → ADR 004.

## Phase status

- **Phase 0 — Doc-System:** ✅ Gate erfüllt (2026-06-20). Nachweis: alle Doc-Dateien
  + ADR 001–004 existieren, Ist-Stand mit Code abgeglichen.
- **Phase 1 — `balance.py`:** offen
- **Phase 2 — Welle 100 + Sieg:** offen
- **Phase 3 — Inhaltszuwachs:** offen
- **Phase 4 — Politur & `.exe`:** offen
- **Part 2 — Rebirth/Waffen:** offen (Backlog)

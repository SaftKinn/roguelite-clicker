# CLAUDE.md

Einstieg jeder Session. Hier stehen das Ritual und die Regeln — **nicht** das
ganze Design (das lebt in `architecture.md`).

Der Zustand des Projekts lebt **auf der Platte, nicht im Context**: Die
Markdown-Docs sind die Wahrheit. Jede neue Session liest sich an ihnen ein.

---

## Session-Ritual (Anfang)

Zu Beginn JEDER Session, **bevor du irgendetwas anfasst**, in dieser Reihenfolge
lesen:

1. `CLAUDE.md` (diese Datei — Konventionen + Ritual)
2. `progress.md` (wo wir stehen / nächster konkreter Schritt)
3. Das **höchstnummerierte File** in `docs/decisions/` (jüngste Entscheidung)

Dann in **2–3 Sätzen** festhalten: *wo stehen wir, was machen wir gleich.* Erst
nach diesem Handshake — und nach meinem OK — Dateien ändern.

## Auf Abruf lesen (nicht jede Session)

Eager alles zu laden füllt den Context, bevor echte Arbeit beginnt. Selektiv sein:

| Datei | Wann lesen |
|---|---|
| `architecture.md` | Nur bei Design-/Architektur-Aufgaben. |
| `roadmap.md` | Beim Phasenwechsel oder Planen der nächsten Phase. |
| ältere ADRs in `docs/decisions/` | Wenn du in ihrem Bereich arbeitest. |

Beim Arbeiten: **grep/lies das betroffene Modul, bevor du es änderst** (grep-first,
Context schlank halten — nicht alle Docs eager laden).

## Session-Ritual (Ende)

Am Ende JEDER Session (oder auf „wrap up") — **ohne dass ich es extra sagen muss**:

1. `progress.md` aktualisieren: Current focus, Last session, Next concrete step,
   Open questions, ggf. Verifikations-Nachweis der Phase.
2. Bei einer Entscheidung **mit echter Abwägung** das nächste ADR anlegen
   (`docs/decisions/NNN-kurz-titel.md`). Trivia-Entscheidungen nur als Einzeiler
   ins Decision-Log von `progress.md`.

Schweigen hier ist der Fehlermodus, der Kontinuität bricht. Lieber updaten.

**Committe nicht ins Git, außer ich sage es ausdrücklich.**

---

## Was das Projekt ist

Ein 2D-Roguelite × Tower-Defense × Clicker (Python + Pygame). Der Spieler ist ein
stationärer Turm in der Bildschirmmitte; der Turm feuert voll-automatisch und zielt
selbst auf den nächsten Gegner (Autoaim, ADR 010), Treffer heilen (Lifesteal). Gegner
spawnen wellenweise und laufen auf den Turm zu (ein Teil als zähe Elites, ADR 011).
Gegner-Kills geben XP; bei jedem Level-up wählt man eine von drei Karten; Münzen kaufen
dauerhafte Verbesserungen.
**Sieg = Welle 100 schaffen.** Danach (geplant) ein Rebirth, der neue Waffen freischaltet.

Vollständiges Design in `architecture.md`, Plan in `roadmap.md`. **Bei
Design-Unklarheit gewinnt `architecture.md` — und wer eine Entscheidung ändert,
aktualisiert `architecture.md` im selben Change.**

## Befehle

```bash
python main.py        # Spiel starten (kein Build, kein Test-Setup)
pip install pygame    # einzige Pflicht-Abhängigkeit; numpy optional
```

Verifikation erfolgt durch **Starten des Spiels** — es gibt keine Tests/Linter.

Spieler-Taste: **C** blendet im `PLAYING`-State die eigenen Stats ein/aus (Overlay).

Dev-Tasten (nur im `PLAYING`-State): **F1** alle Gegner töten · **F2** zu Welle 9
· **F3** zu Welle 49 · **F4** zu Welle 99 (→ SuperBoss/​Sieg testen; friert Level/Stats
ein → **kein** Endgame-Balance-Test) · **F5** Levelup erzwingen (Karten testen) ·
**F11** Fullscreen · **ESC** Pause/zurück.

---

## Golden Rules

1. **Verifikation = Spiel starten.** `python main.py`; eine Änderung gilt erst als
   fertig, wenn das Spiel ohne Fehler läuft.
2. **Keine Magic Numbers.** Tuning-Werte gehören in `game/balance.py` bzw. als
   Modulkonstante an den Dateianfang — nie verstreut. Verhalten/Logik bleibt Code.
3. **Bezeichner Englisch, Kommentare + alle UI-Texte Deutsch.** Diese Doku auch
   Deutsch.
4. **Jeder State wird in allen drei Phasen behandelt** — Event, Update, Draw in
   `main.py`. Beim Ergänzen eines States an alle drei denken.
5. **Neue Gegner robust.** Eigene `_frames_r/_frames_l`-Klassenvariablen +
   `_load_sprites()` mit `try/except`-Fallback auf gezeichnete Primitive. Das
   Spiel crasht nie, wenn ein Asset fehlt — überall Asset-Fallbacks.
6. **`main.py`-Schleife bleibt das Herz.** Ausgelagert wird nur, wenn eine Stelle
   wirklich unübersichtlich wird — kein voreiliger Refactor.
7. **`architecture.md` ist die Design-Wahrheit.** Bei Unklarheit gewinnt sie; eine
   Designänderung aktualisiert `architecture.md` im selben Change.
8. **Session-Ritual einhalten** (Anfang lesen, Ende `progress.md` + ggf. ADR) —
   auch ohne Aufforderung.
9. **Kein Git-Commit ohne ausdrückliche Aufforderung.**

---

## Repo-Layout

```
roguelite-clicker/
├── CLAUDE.md            # Diese Datei — Ritual + Golden Rules
├── architecture.md      # Design-Wahrheit (technischer Aufbau + Warum)
├── roadmap.md           # Phasenplan mit Verifikations-Gates
├── progress.md          # Stand, nächster Schritt, offene Fragen, Decision-Log
├── docs/decisions/      # ADRs (eine Datei je Entscheidung mit Abwägung)
├── main.py              # State-Machine + Game-Loop (das Herz, Einstiegspunkt)
├── save.json            # Persistenz
├── game/                # Laufzeit-Package (importiert via `from game.x import …`)
│   ├── constants.py · player.py · enemy.py · projectile.py
│   ├── upgrade_menu.py · main_menu.py · save_data.py
│   ├── sounds.py · sprite_loader.py · ui_loader.py · terrain.py · fx.py
│   └── __init__.py
├── tools/generate_assets.py   # Asset-Hilfsskript (kein Laufzeit-Modul)
├── assets/              # Sprites (+ Audio im Umzug nach assets/audio/)
├── media/clips/         # Aufnahmen
└── Gamesounds/          # Alt-Musikordner (Umzug im Gange)
```

(Geplant ab Phase 1: `game/balance.py` — zentrales Tuning-Datenmodul. Vollständige
Modul-Tabelle in `architecture.md` §3.)

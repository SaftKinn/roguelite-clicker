# progress.md

Wo wir stehen, was als Nächstes kommt. Diese Datei ist die laufende Wahrheit über
den Projektzustand — am Ende jeder Session aktualisieren.

---

## Current focus

Phase 1 abgeschlossen: `game/balance.py` angelegt, alle Tuning-Zahlen (Wellen-Formeln,
Spawn-/Nahkampf-Konstanten, In-Run-Upgrade-Werte, Münz-Shop-Preise) zentralisiert.
**Reiner Umzug — Balance unverändert**, durch byte-identische UI-Strings/Preise
verifiziert. Davor: Phase 0 (Doc-System, ADR 001–004) + Gameplay-Politur (ADR 005,
Belagerung). Spiel läuft und ist spielbar.

## Last session

2026-06-20 — Phase 1 (`game/balance.py`):
- **Neu `game/balance.py`** — zentrales Tuning-Datenmodul (ADR 002). Enthält:
  Wellen-Formeln (`enemies/​hp/​speed/​coin_for_wave`), `BASE_SPAWN_INTERVAL`,
  `MELEE_REACH`, `ATTACK_DAMAGE`/`ATTACK_COOLDOWN`, In-Run-Upgrade-Werte
  (`UPGRADE_DAMAGE`/`…_BULLET_SPEED`/`…_BULLET_SIZE`/`…_MAX_HP`, `MULTISHOT_ANGLES`),
  permanente Effekte (`PERMANENT_DAMAGE/HP_PER_LEVEL`, `GOLD_BOOST_MULT`,
  `DOPPELSCHUSS_DELAY`) und Preise (`COST_MULT`, `COST_START_DAMAGE/HP`,
  `COST_DOPPELSCHUSS/GOLD_BOOST`).
- **`main.py`**: Definitionen entfernt, aus `balance` importiert; `apply_upgrade`,
  `apply_permanent_bonuses`, `spawn_projectiles` (Multishot-Winkel), `gold_mult`
  und Doppelschuss-Delay ziehen jetzt aus den Konstanten. Aufrufstellen wortgleich.
- **`game/enemy.py`**: `from . import balance`; `ATTACK_DAMAGE`/`ATTACK_COOLDOWN`
  bleiben Klassen-Variablen (Vererbung/Override intakt), Werte aus `balance`.
- **`game/upgrade_menu.py` + `game/main_menu.py`**: `balance` importiert; UI-Texte
  (`"+10 Schaden"`, `"+50%…"`) + Preise werden aus den Konstanten **generiert**
  (eine Quelle der Wahrheit; UI-Layout-Konstanten wie `CARD_W` bleiben lokal).
- **Verifikation:** Spiel startet fehlerfrei; Test bestätigt byte-identische
  UI-Strings/Preise + Werte-Gleichheit (`Warrior.ATTACK_DAMAGE==10`,
  `enemies_for_wave(5)==17`, `upgrade_cost(50,2)` identisch).
- **Doku-Sync:** `architecture.md` §3 (Modul-Tabelle + balance.py-Beschreibung),
  §6 (Ist-Zustand statt „geplant"), §Repo-Layout.

## Next concrete step

**Phase 2 starten:** Welle 100 erreichbar + Sieg-Zustand. Zuerst die offene
Wellen-Skalierungs-Frage klären (siehe unten) — welches Schema macht Welle 100
ohne ~300 gleichzeitige Belagerer spielbar (Caps? gestaffelte Spawn-Schübe?). Die
Stellschrauben liegen jetzt zentral in `game/balance.py` bereit. ADR 004 (Run-Modell)
beim Sieg-Zustand mitlesen.

(Optionaler Nachzügler aus Phase 1, falls gewünscht: Basis-Stats in
`fresh_game_state()` — Start-`damage`/`bullet_speed`/`bullet_size` — und
`EnemyProjectile`-Werte sind noch nicht in `balance.py`. Bewusst außerhalb des
Phase-1-Scopes gelassen.)

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
- **D9** — Phase-1-Umzug: UI-Texte/Preise werden aus `balance.py`-Konstanten
  generiert (f-Strings) statt als Literale doppelt gepflegt — Single Source of
  Truth, keine Verhaltensänderung (keine Abwägung, fällt unter ADR 002).

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
- **Phase 1 — `balance.py`:** ✅ Gate erfüllt (2026-06-20). Nachweis: `game/balance.py`
  existiert mit allen Tuning-Zahlen; Spiel startet fehlerfrei; Test bestätigt
  byte-identische UI-Strings/Preise + Werte-Gleichheit (reiner Umzug, Balance
  unverändert).
- **Phase 2 — Welle 100 + Sieg:** offen
- **Phase 3 — Inhaltszuwachs:** offen
- **Phase 4 — Politur & `.exe`:** offen
- **Part 2 — Rebirth/Waffen:** offen (Backlog)

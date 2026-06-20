# roadmap.md

Phasenplan vom MVP zur Vollversion. **Layer für Layer, mit Gate:** Jede Phase hat
ein konkret nachprüfbares Verifikations-Gate, das erfüllt sein muss, bevor die
nächste Phase beginnt. Verifikation = Spiel starten (`python main.py`).

Aktueller Stand steht in `progress.md` (Phase status).

---

## Part 1 — MVP

Ziel des MVP: Die jetzige Schleife **rund und verkaufbar** machen, **Welle 100
als Sieg** erreichbar, plus **moderater Inhaltszuwachs**. Rebirth/Waffen sind
bewusst NICHT im MVP (siehe Part 2). Bezug: ADR 004.

### Phase 0 — Doc-System aufsetzen
Dokumentengetriebenes Arbeitssystem etablieren (diese Dateien + ADRs).

**Gate:** `CLAUDE.md`, `architecture.md`, `roadmap.md`, `progress.md` und
`docs/decisions/` (README + ADR 001–004) existieren; der Ist-Stand stimmt mit dem
Code überein.

### Phase 1 — Tuning zentralisieren (`game/balance.py`)
Tuning-Zahlen aus dem verstreuten Code in ein zentrales Python-Datenmodul
`game/balance.py` ziehen: Gegner-HP/Speed pro Welle, Wellen-Anzahl/-Mix,
Münz-Werte, In-Run-Upgrade-Werte, permanente Preise/Multiplikatoren. **Verhalten
bleibt im Code.** Keine Spielbalance ändern — nur verschieben. Bezug: ADR 002.

**Gate:** Das Spiel läuft **identisch** wie vorher (gleiche Werte), aber alle
genannten Stellschrauben liegen an einem Ort in `game/balance.py`. Gegengeprüft:
ein paar Werte in `game/balance.py` ändern → Wirkung im Spiel sichtbar.

### Phase 2 — Welle 100 + Sieg-Bildschirm
Wellen-Skalierung so überarbeiten, dass Welle 100 **erreichbar und nicht absurd**
ist (Performance: keine ~300 Gegner gleichzeitig). Sieg-Zustand/-Screen beim
Besiegen des SuperBosses in Welle 100; Lauf endet sauber, `best_wave` korrekt.

Beachten: Seit ADR 005 **belagern** Gegner den Turm und verschwinden nicht mehr
durch Kontakt — sie stauen sich, bis der Spieler sie erschießt. Das verschärft
sowohl die Performance- (gleichzeitige Gegner) als auch die Balance-Frage
(`ATTACK_DAMAGE`/`ATTACK_COOLDOWN` vs. Spieler-DPS) und gehört hier mitgedacht.

**Gate:** Mit Dev-Tasten (F3 → Welle 49, weiterspielen) lässt sich Welle 100
erreichen, der SuperBoss besiegen, der Sieg-Screen erscheint, und der Lauf endet
sauber (zurück ins Menü / Neustart möglich). Keine Performance-Einbrüche oder
Crashes auf dem Weg.

### Phase 3 — Moderater Inhaltszuwachs
Phasenweise, je separat testbar (nicht koppeln):

- **3a:** Mehr In-Run-Upgrades (stärkt Build-Vielfalt / das Run-Rückgrat zuerst).
- **3b:** 1–2 neue Gegnertypen mit eigenem Verhalten.
- **3c:** Mehr permanente Verbesserungen (Meta-Progression zwischen Runs).
- **3d:** Zusätzliche Boss-Variante oder zweiter Map-/Terrain-Look.

**Gate (je Teilphase):** Der neue Inhalt ist im Spiel erlebbar, Balancing wirkt
okay, kein Crash. Neue Werte liegen in `game/balance.py`, neue Gegner folgen dem
Lazy-Sprite-Fallback-Pattern.

### Phase 4 — Politur & Verpacken
Game-Feel-Schliff (Feedback, Sound, Lesbarkeit, kleine Bugs), dann
Windows-`.exe` via PyInstaller.

**Gate:** Eine lauffähige `.exe` existiert, die **jemand anders** auf einem
Windows-Rechner ohne Python-Installation starten und spielen kann.

---

## Part 2 — Jenseits des MVP (Backlog)

Die großen Brocken nach dem MVP, grob nach Wert geordnet:

- **Rebirth-System.** Sieg bei Welle 100 → komplettes Reset → Karte mit 3 Waffen
  → 1 dauerhaft behalten. Bezug: ADR 004.
- **Waffen-System.** Verschiedene Waffen = verschiedene Schussmuster (Arbeitsannahme).
  Waffenwahl vor dem Run.
- **Waffen-Meta-Upgrades** im Verbesserungsmenü (genaue Mechanik offen).
- **Save-Format erweitern** um freigeschaltete Waffen + deren Upgrades (überleben
  als Einzige einen Rebirth).
- **JSON-Migration** der Balance-Daten (wenn externes Balancing/Modding nötig).
  Bezug: ADR 002.
- **Browser-Version** via pygbag (Reichweite), falls gewünscht.
- Weiterer Inhalt: mehr Maps, mehr Bosse, mehr Waffen, Achievements.

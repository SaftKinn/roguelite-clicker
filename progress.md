# progress.md

Wo wir stehen, was als Nächstes kommt. Diese Datei ist die laufende Wahrheit über
den Projektzustand — am Ende jeder Session aktualisieren.

---

## Current focus

**Endgame-Wand auf beiden Hebeln datengestützt entschärft — bereit für echten Playtest.**
Das read-only Modell (`tools/balance_model.py`) hat zwei Fixes getrieben: (1) Boss-HP-
Multiplikatoren ×8/×25 → **×2/×3** (ADR 013, SuperBoss W100 255k→31k); (2) **Kill-XP skaliert
jetzt mit der Welle** (`xp_wave_mult = 1+wave//8`, `XP_WAVE_DIV=8`, ADR 014) — vorher flach,
Spieler hing auf W100 bei ~Level 33 mit zu wenig DPS. Mit dem XP-Fix: Modell-Endlevel ~98,
**0/10 Bosse über dem Walk-Budget** (vorher 9/10). Bewusst gewählt: „Root-Fix pur" (nur XP,
HP unverändert) statt HP-lastiger Combo. **Bekanntes Risiko: Level-Inflation** (~98 → fast
alle Karten erreichbar, Build-Tiefe verwässert). Alles uncommitted (ADR 013 ist committet
`ba7c997`; ADR 014 neu, uncommitted). **Offen: der echte 1→100-Playtest** — bestätigt er
~Level 98 als gutes Gefühl und die Boss-TTKs?

## Last session

2026-06-21 (Teil 3) — SuperBoss-Sprite aus KI-Video (Drachenlord) **verworfen**:
- Versuch, den SuperBoss als animierten Drachen aus einem Kling-MP4 zu setzen (Frame-Extraktion
  + Keying-Pipeline). **Vom Nutzer verworfen — Sprite gefiel optisch nicht**, alles rückgängig
  gemacht (enemy.py/sprite_loader.py via git checkout; Banner/Sieg-Text/Doku manuell zurück;
  Assets + Tool + ADR 015 gelöscht). **Offen: ein neuer SuperBoss-Sprite** (Nutzer liefert).
  Die Balance-Arbeit (ADR 013/014) blieb davon unberührt.

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

**Ein echter 1→100-Lauf (kein F4!)** mit beiden Hebeln drin (ADR 013 ×2/×3 + ADR 014 XP-
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
  aktive Spannung? (Build-Tiefe, Gegnerdruck, evtl. aktivierbare Fähigkeit?) Offen.

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
- **D28** — **Drachenlord-Sprite verworfen.** Animierter SuperBoss aus KI-Video (Pipeline +
  ADR 015) wurde gebaut, vom Nutzer aber optisch abgelehnt und vollständig zurückgerollt
  (kein ADR-Eintrag mehr). Offen: neuer SuperBoss-Sprite vom Nutzer.
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
  ADR 013 (Boss-Multiplikatoren ×2/×3), ADR 014 (XP-Wellenskalierung).
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
  Wellenskalierung (ADR 014). Noch offen: neuer SuperBoss-Sprite (Drachen-Versuch verworfen),
  weitere Karten/Upgrades (Crit, Explosiv/Kette, DoT, Regen, Dornen, Reroll …) + ein echter
  1→100-Balance-Lauf (inkl. Level-Inflations-Check); alles per Playtest.
- **Phase 4 — Politur & `.exe`:** offen
- **Part 2 — Rebirth/Waffen:** offen (Backlog)

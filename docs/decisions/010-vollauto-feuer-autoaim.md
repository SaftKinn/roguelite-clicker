# ADR 010 — Voll-Auto-Feuer + Autoaim (Wende zum Idle-Tower-Defense)
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** architecture.md §1, §5; löst das Feuer-Modell aus ADR 009 ab; progress.md D17–D20

## Context
ADR 009 hatte „Halten der LMB feuert automatisch Richtung **Maus**" eingeführt — der
Spieler musste die Taste halten **und** zielen. Im Playtest war das ermüdend und
unpräzise (Zielen mit der Maus bei vielen Gegnern), und schnelles Klicken umging die
`attack_speed`-Bremse (jeder `MOUSEBUTTONDOWN` setzte `fire_timer = 0` → Sofortschuss).
Gewünscht: der Turm soll **selbst feuern und selbst zielen** — der Spieler trifft nur
noch Build-Entscheidungen (Karten/Upgrades).

## Decision
- **Voll-Auto-Feuer:** Kein `mouse_held` mehr. Im `PLAYING`-Update feuert der Turm,
  sobald `fire_timer <= 0` **und** ein Gegner existiert; danach `fire_timer =
  FPS / attack_speed`. Ohne Ziel bleibt der Timer ≤0 → erster Schuss fällt sofort beim
  ersten Gegner (kein Leerlauf-Ballern). Die Maus ist im Spiel funktionslos (nur Menüs).
- **Autoaim:** `nearest_enemy_pos(pc, enemies)` liefert die Weltposition des nächsten
  lebenden Gegners als Ziel. Da der Turm im Welt-Zentrum sitzt und der Kamera-Zoom um
  die Mitte arbeitet, ist die Richtung Turm→Gegner in Welt- und Bildschirmkoordinaten
  identisch — `spawn_projectiles` normalisiert ohnehin nur die Richtung, also dient die
  Gegner-Weltposition direkt als Ziel (keine Zoom-Rückrechnung nötig).
- **Spam tot (Bestandteil der Wende):** Der `fire_timer`-Reset beim Klick entfällt;
  allein der jeden Frame runterzählende `fire_timer` taktet das Feuer.
- **Angriffstempo-Karte additiv:** `attack_speed += UPGRADE_ATTACK_SPEED` (+0.2/s je
  Karte) statt multiplikativ ×1.10 (ADR 009). Basis `BASE_ATTACK_SPEED = 1.5`/s.

## Alternatives
- **Halten beibehalten, nur Autoaim:** Zwischenschritt; im Playtest gewünscht war das
  *vollständig* passive Feuern. Verworfen.
- **Auf Maus/Cursor zielbar lassen (manuelles Aim als Option):** mehr Code, kein
  spürbarer Nutzen, sobald Autoaim „nächster Gegner" trifft. Verworfen.
- **Angriffstempo multiplikativ lassen (ADR 009):** spätere Karten würden überproportional
  stark (Snowball). Additiv macht jede Karte gleich viel wert und planbarer.

## Consequences
- **Positiv:** Kernschleife ist jetzt komplett passiv — der Spieler steuert nur den
  Build. Deterministische DPS, kein Klick-Spam-Exploit, kein Maus-Zielstress. Das passt
  zum Idle-/Auto-Battler-Gefühl und macht spätere Auto-Builds (mehr Karten) sinnvoll.
- **Negativ / Bindung:** Das **„Clicker" im Genre-Namen stimmt nicht mehr** — die
  Schuss-Eingabe als „Würze" (architecture.md §1) ist entfallen. Ohne aktives Zielen
  fehlt eine Skill-Achse; Spannung muss künftig stärker aus Build-Entscheidungen,
  Gegnerdruck und Elites (ADR 011) kommen. Autoaim „nächster Gegner" ist simpel —
  Priorisierung (z. B. gefährlichste/zäheste zuerst) ist bewusst **nicht** umgesetzt.
- **Verifikation:** Treiber (`/run-roguelite-clicker`) — der **nie die Maus hält** —
  startet fehlerfrei und zeigt im Spiel-Screenshot ein automatisch abgefeuertes
  Projektil; Feuer-/HP-Mathe headless geprüft. Spielgefühl per Playtest.

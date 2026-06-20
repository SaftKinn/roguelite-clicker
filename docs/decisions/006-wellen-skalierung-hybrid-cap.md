# ADR 006 — Wellen-Skalierung: Hybrid-Cap (Gesamt + Concurrent) für Welle 100
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** roadmap.md Phase 2; architecture.md §3.1, §5, §8; ADR 004 (Sieg-Bedingung), ADR 005 (Belagerung)

## Context
ADR 004 macht **Welle 100 = Sieg**. Die bisherige Skalierung
`enemies_for_wave = 5 + (Welle-1)·3` ergibt bei Welle 99 **≈300 Gegner** — und seit
ADR 005 *belagern* Gegner den Turm (sie verschwinden nicht mehr durch Kontakt,
sondern stapeln sich und greifen auf Cooldown an). Damit ist die *gleichzeitige*
Gegnerzahl der eigentliche Engpass: sie bestimmt Performance **und** den eingehenden
Belagerungs-DPS (`ATTACK_DAMAGE`/`ATTACK_COOLDOWN`). Welle 100 wäre so weder lauffähig
noch fair erreichbar.

## Decision
**Hybrid-Cap aus zwei Stellschrauben** (`game/balance.py`):
- `MAX_ENEMIES_PER_WAVE = 40` — Obergrenze der **Gesamtzahl** je Normalwelle:
  `enemies_for_wave = min(5 + (Welle-1)·3, 40)`. Boss-Wellen (`Welle % 10 == 0`)
  bleiben bei **1**. Der Cap greift ab Welle 13.
- `MAX_CONCURRENT_ENEMIES = 25` — es wird nur nachgespawnt, solange **weniger als 25
  Gegner leben**. Bremst das Nachrücken, deckelt On-Screen-Zahl und Belagerungs-DPS.

Schwierigkeit jenseits von Welle 13 kommt damit über **HP/Speed-Skalierung** (bereits
vorhanden) statt über Masse → späte Wellen = lange, zähe Abnutzung. Beide Werte liegen
zentral in `balance.py` (Phase 1) und sind ohne Codeänderung tunebar.

## Alternatives
- **Nur Gesamtzahl hart deckeln (~25), kein Concurrent-Cap** („wenige, aber zäh"):
  einfachster Eingriff (eine Formel), aber ohne Concurrent-Gate spawnen bei kleinem
  Cap fast alle sofort → weniger Kontrolle über das Belagerungs-Staus-Tempo.
- **Hohe Gesamtzahl + nur Concurrent-Cap** („Schwarm + Trickle"): erhält das
  Massen-Gefühl, führt aber zu sehr langen Wellen (80+ Gegner sickern in 25er-Schüben
  nach) — zäher als gewünscht und schwerer zu balancieren.
- **Gar kein Cap, nur HP/Speed steiler:** löst die Performance nicht — 300 belagernde
  Gegner bleiben 300 Entitäten und 300× Cooldown-DPS.

## Consequences
- **Positiv:** Welle 100 ist erreichbar und performant (nie >25 gleichzeitig); der
  Concurrent-Cap deckelt Perf und eingehenden Schaden in einem. Tuning bleibt zentral
  und billig.
- **Negativ / Bindung:** Die Gegner*zahl* plateaut früh (ab Welle 13 konstant 40
  gesamt) — die Spannungskurve danach hängt **ganz** an HP/Speed und am
  Belagerungs-DPS. Diese Werte (`enemy_hp_for_wave`, `enemy_speed_for_wave`,
  `ATTACK_DAMAGE`/`ATTACK_COOLDOWN` vs. Spieler-DPS) brauchen beim Durchspielen ein
  Feintuning, sobald ein echter Welle-1-bis-100-Lauf getestet wurde.
- **Verifikation:** Dev-Taste **F4 → Welle 99** (nächste Clear → SuperBoss Welle 100);
  mit F1 räumen → Sieg-Screen.

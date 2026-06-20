# ADR 001 — Engine & Sprache: Python + Pygame
- **Status:** Accepted
- **Date:** 2026-06-20
- **Refs:** Decision-Log D2, D3 in progress.md; architecture.md §2

## Context
Das Projekt ist ein Lernprojekt mit echter Veröffentlichungs-Absicht (Windows-`.exe`,
z. B. itch.io), bearbeitet von einem Programmier-Anfänger, solo. Es existiert
bereits ein lauffähiges Spiel in Python + Pygame. Die Frage ist, ob man auf dieser
Basis weiterbaut oder die Engine wechselt. Constraints: Lernkurve niedrig halten,
schnell sichtbare Ergebnisse, später als Desktop-Spiel verteilbar.

## Decision
Wir bleiben bei **Python + Pygame** als Engine und Sprache.

## Alternatives
- **Godot (GDScript/C#):** Mächtige, kostenlose 2D-Engine mit Editor und einfachem
  Export. Verworfen: Engine- und Editor-Wechsel würde den vorhandenen Code
  wegwerfen und eine neue Sprache/Umgebung erzwingen — zu viel Reibung mitten im
  Lernen.
- **Unity:** Industriestandard, aber schwer für Anfänger, überdimensioniert für
  ein kleines 2D-Spiel, C# + komplexe Editor-Konzepte.
- **Web (JavaScript/HTML5-Canvas):** Einfachstes Verteilen (Browser), aber
  Sprachwechsel und Wegwerfen des vorhandenen Codes.

## Consequences
- **Positiv:** Der vorhandene Code bleibt, Python ist anfängerfreundlich, Pygame ist
  simpel und gut dokumentiert. Schnelle Iteration via `python main.py`.
- **Negativ / Bindung:** Verteilen ist die bekannte Pygame-Schwäche — eine
  `.exe` braucht PyInstaller und sorgfältiges Asset-Bundling (Phase 4 einplanen,
  nicht unterschätzen). Performance hat Grenzen (reines Python, keine GPU-Beschleunigung
  der Spiellogik) — relevant bei großen Wellen (siehe architecture.md §11).
- Ein späterer Browser-Port ist via **pygbag** möglich (Backlog), aber nicht
  garantiert reibungslos.

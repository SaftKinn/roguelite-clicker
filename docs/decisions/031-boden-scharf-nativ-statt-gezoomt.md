# ADR 031 — Boden scharf in nativer Auflösung statt durch den Kamera-Zoom hochskaliert

- **Status:** Accepted
- **Date:** 2026-06-22
- **Refs:** `main.py` (`blit_world_zoomed`, Render-Block, `world_surf`), `game/sprite_loader.py`;
  betrifft Tier-Boden ADR 029, Kamera-Zoom ADR 007 (`CAMERA_ZOOM = 1.4`)

## Context
Die Tier-Boden-Texturen (ADR 029) wirkten leicht unscharf. Ursache: Die gesamte Welt wird in
`world_surf` (1280×720) gezeichnet, dann skaliert `blit_world_zoomed` den zentralen `1/1.4`-
Ausschnitt **formatfüllend hoch** (`CAMERA_ZOOM`). Der Boden wird so um 1,4× vergrößert — bei einer
detailreichen Steintextur sichtbar weicher als bei den glatten Gegner-Sprites.

## Decision
1. **Boden post-zoom, nativ.** Der Boden wird **direkt auf den `screen`** (1280×720, ungezoomt)
   gezeichnet; nur die **Gameplay-Ebene** (Gegner/Geschosse/Spieler/Schadenszahlen) liegt in
   `world_surf` und wird gezoomt darübergelegt. Da der Boden eine gleichförmige Textur ist, ist die
   fehlende Zoom-Vergrößerung optisch unerheblich — er bleibt aber pixelscharf.
2. **`world_surf` → SRCALPHA.** Die Gameplay-Ebene ist transparent (`fill((0,0,0,0))` je Frame);
   `blit_world_zoomed` **blittet** das skalierte Ergebnis alpha-erhaltend über den Boden, statt es
   wie bisher per `smoothscale(..., dest=screen)` direkt in den Screen zu schreiben (das hätte den
   Boden überschrieben).
3. **Textur exakt 1280×720, kein Runtime-Resample.** Re-Import der drei Boden-PNGs in einem
   einzigen Cover-Crop aus der Voll-Auflösung (1680²) direkt auf 1280×720. `load_tier_background`
   gibt die Textur 1:1 zurück, wenn sie bereits Zielgröße hat (kein zweiter Smoothscale).

## Alternatives
- **`world_surf` supersamplen (z. B. 2×):** würde Gameplay-Koordinaten (alle in 1280×720) brechen
  oder überall teure Skalierung erzwingen.
- **Schärfen/Unsharp-Mask auf die Textur:** kaschiert nur, behebt die Upscale-Ursache nicht.
- **Boden ebenfalls zoomen, nur höher aufgelöst:** unmöglich, solange er durch das 1280×720-
  `world_surf` läuft — die Auflösung ist dort gedeckelt.

## Consequences
- **Positiv:** Boden in nativer Bildschirmauflösung, sichtbar schärfer; Gegner/Geschosse behalten
  exakt ihren 1,4×-Zoom (Gameplay unverändert); HUD/Overlays unberührt (kommen ohnehin danach).
- **Negativ / offen:** Boden „zoomt" nicht mit der Welt — bei der gleichförmigen Textur unkritisch;
  bei den Tiny-Swords-Deko-Objekten (Gras-Fallback) wären sie jetzt ungezoomt (nur im Fallback
  sichtbar). `world_surf` ist jetzt SRCALPHA (minimal mehr Füll-/Blit-Kosten pro Frame, vernachlässigbar).
- **Verifikation:** In-Game `02_playing.png` zeigt klar schärfere Pflastersteine; voller Treiber-
  Flow (→ Sieg) crashfrei; Gameplay-Ebene komponiert korrekt über dem Boden (kein Überschreiben).

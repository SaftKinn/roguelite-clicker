# 033 — UI-Redesign: zentrales Theme-Modul, „Glass"-Hybrid-Look

Datum: 2026-06-22
Status: angenommen

## Kontext

Das gesamte Front-End (Hauptmenü, Shop, Level-up-Karten, Slot-Auswahl, Optionen,
Lexikon, HUD-Overlays) war **flach code-gezeichnet**: dunkle Panels `(26,28,40)`,
einfarbige Akzent-Rahmen, `border_radius`, simple Hover-Glows, SysFont-Arial. Dieselbe
Panel-Logik (`pygame.draw.rect`-Body + Rahmen + Kopfband) war in **sechs** Screens per
Copy-Paste dupliziert, jeweils mit hartkodierten Farben. Der Nutzer wollte einen
**moderneren, hochwertigeren** Look.

Gewählte Richtung (mit dem Nutzer geklärt): **Hybrid** — sleek-dark „Glassmorphism"-Basis
komplett im Code, plus gezielte freigestellte Leonardo-PNGs (Logo, Gruppen-Icons).
Reihenfolge Hauptmenü → Shop → Karten → Rest. Karten-Icons: **eines je Farbgruppe** (4).

## Entscheidung

**Neues Modul `game/theme.py` als einzige Quelle des UI-Looks.** Es kapselt eine neutrale
Palette und gecachte „Glass"-Primitive, die jeder Screen statt roher Draw-Aufrufe nutzt:

- `backdrop(screen)` / `backdrop_region(...)` — Vollbild-Verlauf + weiche Vignette (ersetzt
  `screen.fill(BG_COLOR)`); Region-Variante als nahtlose Scroll-Maske (Lexikon).
- `panel(...)` — Glass-Panel: Verlaufs-Füllung + eingebackenes Oberkante-Highlight +
  optional Akzent-Rahmen. Kapselt das frühere Body/Rahmen/Kopfband-Muster.
- `drop_shadow(...)` / `accent_glow(...)` — weiche Schatten/Glows via Down-/Upscale-Blur
  (`smoothscale`), pro Form gecacht (Pygame hat keinen nativen Blur).
- `text(...)` / `text_center(...)` — Text mit 1px-Schatten.
- `pill(...)`, `header_band(...)`, `font(size, bold, display)` — Mini-Panels, Kopfbänder,
  globaler Font-Cache mit optionaler **Display-TTF** aus `assets/fonts/` (Fallback Arial).

Die geteilte `Button`-Klasse (`main_menu.py`) wurde auf diese Primitive umgestellt — damit
heben sich **alle** Menü-Buttons (Hauptmenü, Optionen, Lexikon, Shop, Pause) an einer
Stelle. Karten/Shop/End-Overlays bekamen Glass-Bodies, Schatten/Glows, Gruppen-Verlauf-
Kopfbänder. Karten nutzen jetzt **ein Icon je Farbgruppe** (`assets/custom/icon_<group>.png`)
mit Fallback auf die bisherigen Tiny-Swords-Icons. Hauptmenü lädt optional ein
`assets/custom/menu_logo.png` (Fallback: gezeichneter Gold-Titel).

Gruppen-Farben bleiben in `balance.py` (`GROUP_COLORS`) — `theme.py` enthält nur die
neutrale UI-Palette.

## Abwägung / Alternativen

- **Pures Code-Glass vs. Tiny-Swords-Fantasy-Frames (PNG-Rahmen):** Hybrid gewählt — die
  Code-Basis ist auflösungsscharf, wartbar und braucht keine 9-Slice-Frames; PNGs nur als
  gezielte Akzente (Logo, Icons), wo sie Charakter bringen, ohne den ganzen Look an Assets
  zu binden.
- **Theme-Modul vs. weiter inline pro Screen:** Modul gewählt (DRY) — der Look ist jetzt an
  einer Stelle steuerbar; Konsistenz statt Drift.
- **`pygame.draw.rect` für Hover-Aufhellung:** verworfen — `draw.*` **überschreibt** auf
  SRCALPHA-Surfaces das Ziel-Alpha (blendet nicht), was den Karteninhalt auswischte. Hover
  signalisieren jetzt `accent_glow` (Halo) + dickerer Rahmen.
- **Performance:** Verläufe/Schatten/Glows/Panel-Füllungen werden pro Form gecacht und nur
  geblittet; keine Per-Frame-Neuberechnung.

## Konsequenzen

- Alle Menü-Screens + In-Game-Overlays (Pause/Game-Over/Sieg/„Welle geschafft") teilen einen
  kohärenten, modernen Look. Verifiziert per Headless-Renders **und** vollem Treiber-Flow
  (Slot→Menü→Shop→PLAYING→F7-Karten→Sieg) crashfrei.
- **Offen (extern, Nutzer):** 5 Leonardo-PNGs sind noch zu generieren — `menu_logo.png` +
  `icon_red/blue/gold/white.png` (Prompts/Settings im Plan-File). Bis dahin greifen die
  Fallbacks (Gold-Titel bzw. Tiny-Swords-Icons) — nichts crasht ohne sie (Golden Rule 5).
- **Optional:** eine Display-TTF nach `assets/fonts/` legen aktiviert Titel-Font überall;
  ohne sie bleibt Arial.
- `★`-Glyphe aus Rekord-/Sieg-Texten entfernt (der aufgelöste Arial-Font rendert sie als
  Kästchen); das Gold-Pill ist Emphase genug.

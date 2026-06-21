# ADR 020 — FPS-Regler + Geschwindigkeits-/Zeitraffer-Multiplikator

- **Status:** Accepted
- **Date:** 2026-06-21
- **Refs:** architecture.md §3.1 (Loop/States), §Render-Feel; progress.md; berührt ADR 007
  (Speed/Zoom), ADR 009/010 (Feuer-Takt)

## Context
Das Spiel ist **frame-basiert** (Bewegung = px/Frame, Timer in Ticks). Der Nutzer wollte
(a) die Bildrate einstellen können und (b) einen **Zeitraffer**, der das Spiel beschleunigt,
„ohne dass sich am Balancing etwas ändert — nur schneller".

## Decision
- **FPS-Standard 75 → 140** (`constants.FPS`). **FPS-Regler** im `OptionsMenu` als Schiebebalken
  (wie die Lautstärke; Werte 30–240). Die gewählte Bildrate treibt **sowohl** `clock.tick`
  **als auch** die Feuerrate (`fire_timer = fps / attack_speed`) über `options_menu.fps_value`
  — so bleibt „Schüsse **pro Sekunde**" (`attack_speed`) bei jeder Bildrate ehrlich.
- **Zeitraffer-Button** (HUD oben rechts, `PLAYING`): **ausklappbares Dropdown** mit den Stufen
  **x1 / x2 / x3 / x5 / x10 / x20** (Klick öffnet die Liste, Option wählt direkt). Umsetzung als
  **Update-Loop-Multiplikator**: der gesamte Gameplay-Update-Block läuft `time_scale`-mal pro
  gerendertem Frame (`for _ in range(time_scale): …`). Jeder Step ist **identisch** zum
  Normalspiel → die Balance bleibt exakt gleich, es passieren nur mehr Steps je Bild.
- **Taste `B`** setzt die Geschwindigkeit sofort auf x1 zurück (Zeitraffer aus).
- **Steuerungs-Übersicht:** ein `CONTROLS`-Screen (aus dem Pause-Menü) listet alle Tasten/Bedienelemente.

## Alternatives
- **Delta-time-Refactor** (alles in Sekunden, framerate-unabhängig): sauberste Lösung, aber
  großer Umbau jeder Bewegung/jedes Timers. Out of scope.
- **Zeitraffer über Werte-Skalierung** (z. B. Speeds ×N, Timer /N): ändert Sub-Step-Verhalten
  (Kollision/Tunneling) → Balance driftet. Verworfen zugunsten „echte N Steps".
- **Spawn-Rate-Button** (erste Version): beschleunigte nur die Spawns, nicht „alles". Durch den
  echten Zeitraffer ersetzt (Nutzerwunsch „alles gleich, nur schneller").

## Consequences
- **Positiv:** Einstellbare Bildrate; echter Fast-Forward, der Balance exakt erhält (ein Step =
  ein Step); minimal-invasiv (Loop-Wrap + ein Multiplikator).
- **Negativ / Bindung:** **FPS 140 ist frame-basiert** → real läuft alles ~1,87× schneller als
  bei 75 (Bewegung px/Frame); Gegner-Speed/Spawn-Feel ändern sich mit der Bildrate (bewusst).
  Bei x20 werden Sounds/FX bis zu 20×/Frame ausgelöst (Kakofonie, akzeptiert). State-Wechsel
  mitten im Loop sind unkritisch (folgende Iterationen treffen die passenden `if/elif`-Zweige).
- **Verifikation:** FPS-Regler headless (Default 140, Drag 30–240, Persistenz); Zeitraffer x20
  headless crashfrei + sichtbar schnellerer Levelup; `fire_timer` an `fps_value` gekoppelt.

#!/usr/bin/env python3
"""Session-Start-Status (für den SessionStart-Hook, ADR 021).

Gibt knapp aus, wo das Projekt steht — damit jede neue Session sofort das
CLAUDE.md-Ritual erfüllt hat, ohne dass Dateien manuell gelesen werden müssen:
  * `## Current focus` aus progress.md
  * `## Next concrete step` aus progress.md
  * das höchstnummerierte ADR in docs/decisions/

Read-only, keine Abhängigkeiten. stdout wird vom Hook als Kontext eingespeist.
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _section(text: str, header: str) -> str:
    """Inhalt eines '## header'-Abschnitts bis zur nächsten '## '-Überschrift."""
    m = re.search(rf"^##\s+{re.escape(header)}\s*$(.*?)(?=^##\s|\Z)",
                  text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def main() -> None:
    print("=== Projekt-Status (SessionStart-Hook) ===")
    prog = os.path.join(_ROOT, "progress.md")
    if os.path.exists(prog):
        with open(prog, encoding="utf-8") as f:
            text = f.read()
        focus = _section(text, "Current focus")
        nxt   = _section(text, "Next concrete step")
        if focus:
            print("\n[Current focus]\n" + focus)
        if nxt:
            print("\n[Next concrete step]\n" + nxt)
    else:
        print("(progress.md nicht gefunden)")

    dec = os.path.join(_ROOT, "docs", "decisions")
    if os.path.isdir(dec):
        adrs = sorted(f for f in os.listdir(dec)
                      if re.match(r"\d{3}-.*\.md$", f))
        if adrs:
            print(f"\n[Neuestes ADR] {adrs[-1]}")

    print("\n(Ritual erfüllt — jetzt in 2-3 Sätzen 'wo stehen wir / was als Nächstes' bestätigen.)")


if __name__ == "__main__":
    main()

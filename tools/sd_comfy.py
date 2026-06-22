#!/usr/bin/env python3
"""Dünner Client für eine lokal laufende ComfyUI-Instanz (ADR 037).

ComfyUI läuft als **eigener Prozess** (eigenes venv, bringt torch/CUDA mit) und stellt
eine HTTP-API auf `127.0.0.1:8188` bereit. Dieses Modul spricht nur diese API an — es
importiert NIE torch. Damit bleibt das Spiel frei von schweren ML-Abhängigkeiten
(`python main.py` braucht weiter nur pygame).

Aufgabe hier bewusst klein:
  * `is_up()`            — läuft ComfyUI? (saubere Meldung statt Crash)
  * `load_workflow()`    — Workflow-Graph (ComfyUI „API format" JSON) laden
  * `set_inputs()`       — Platzhalter-Tokens (%PROMPT% …) im Graph ersetzen
  * `upload_image()`     — Stil-Referenzbild hochladen (für IP-Adapter)
  * `run()`              — Graph ausführen, fertige Bilder als PIL.Image zurückgeben

Der Workflow referenziert nichts über fragile Node-IDs, sondern über **Platzhalter-Tokens**
in den Input-Werten (z. B. der Positive-Prompt-String ist `"%PROMPT%"`). `set_inputs()`
ersetzt sie rekursiv — so überlebt der Client kleine Umbauten des Graphen.

Deps: `requests` (Pflicht für echten Lauf), `websocket-client` (optional; fehlt es, wird
auf History-Polling zurückgefallen), `Pillow` (schon vorhanden). Alles separat von der
Spiel-Pflicht-Dep — siehe `tools/requirements-sd.txt`.
"""
import io
import json
import os
import time
import urllib.parse

COMFY_HOST = os.environ.get("COMFY_HOST", "127.0.0.1:8188")
POLL_INTERVAL = 1.0        # s zwischen History-Abfragen (Fallback ohne websocket)
TIMEOUT = 300              # s Gesamt-Wartelimit je Lauf
WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "workflows")

# Platzhalter-Tokens, die im Workflow-JSON als Input-Werte stehen und hier gefüllt werden.
TOKENS = ("%PROMPT%", "%NEGATIVE%", "%SEED%", "%STEPS%", "%CFG%",
          "%WIDTH%", "%HEIGHT%", "%CKPT%", "%REF_IMAGE%", "%BATCH%", "%IPWEIGHT%")


def _requests():
    """`requests` lazy importieren → --dry-run in sd_gen braucht es nie."""
    try:
        import requests
        return requests
    except ImportError:
        raise SystemExit(
            "Modul `requests` fehlt (nur für echte SD-Läufe nötig):\n"
            "    pip install -r tools/requirements-sd.txt")


def _base() -> str:
    return f"http://{COMFY_HOST}"


# --- Erreichbarkeit ------------------------------------------------------------------

def is_up() -> tuple[bool, str]:
    """(erreichbar?, Klartext-Meldung). Crasht nie — wirft nur, wenn requests fehlt."""
    requests = _requests()
    try:
        r = requests.get(f"{_base()}/system_stats", timeout=3)
        if r.ok:
            return True, f"ComfyUI läuft auf {COMFY_HOST}."
        return False, f"ComfyUI antwortet, aber HTTP {r.status_code}."
    except Exception as e:
        return False, (f"ComfyUI auf {COMFY_HOST} nicht erreichbar ({e.__class__.__name__}).\n"
                       "Starte ComfyUI zuerst (siehe tools/README-sd.md) oder setze COMFY_HOST.")


# --- Workflow laden + füllen ---------------------------------------------------------

def load_workflow(name: str) -> dict:
    """Workflow-JSON laden. `name` ohne Pfad → aus tools/workflows/, sonst direkter Pfad."""
    path = name if os.path.isabs(name) or os.path.sep in name \
        else os.path.join(WORKFLOW_DIR, name)
    if not path.endswith(".json"):
        path += ".json"
    if not os.path.exists(path):
        raise SystemExit(f"Workflow nicht gefunden: {path}")
    with open(path, "r", encoding="utf-8") as f:
        wf = json.load(f)
    # `_`-Schlüssel sind menschliche Kommentare, keine Nodes → vor dem Senden entfernen
    # (ComfyUI erwartet je Top-Level-Eintrag einen Node mit class_type).
    return {k: v for k, v in wf.items() if not k.startswith("_")}


def set_inputs(wf: dict, **values) -> dict:
    """Platzhalter-Tokens rekursiv ersetzen. Keys ohne '%' werden zu '%KEY%' (Großschreibung).
    Beispiel: set_inputs(wf, prompt=p, seed=42) ersetzt %PROMPT% und %SEED%."""
    mapping = {}
    for k, v in values.items():
        if v is None:
            continue
        token = k if k.startswith("%") else f"%{k.upper()}%"
        mapping[token] = v

    def walk(node):
        if isinstance(node, dict):
            return {kk: walk(vv) for kk, vv in node.items()}
        if isinstance(node, list):
            return [walk(x) for x in node]
        if isinstance(node, str) and node in mapping:
            return mapping[node]
        return node

    return walk(wf)


# --- Referenzbild hochladen (IP-Adapter Stil-Referenz) -------------------------------

def upload_image(path: str) -> str:
    """Bild in ComfyUIs input-Ordner hochladen, gibt den dortigen Dateinamen zurück."""
    requests = _requests()
    fname = os.path.basename(path)
    with open(path, "rb") as f:
        r = requests.post(f"{_base()}/upload/image",
                          files={"image": (fname, f, "image/png")},
                          data={"overwrite": "true"}, timeout=30)
    r.raise_for_status()
    return r.json().get("name", fname)


# --- Ausführen -----------------------------------------------------------------------

def _queue(requests, wf: dict, client_id: str) -> str:
    r = requests.post(f"{_base()}/prompt",
                      json={"prompt": wf, "client_id": client_id}, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"ComfyUI lehnte den Workflow ab (HTTP {r.status_code}):\n{r.text[:800]}")
    return r.json()["prompt_id"]


def _wait_history(requests, prompt_id: str) -> dict:
    """Fallback ohne websocket: /history pollen, bis der Auftrag auftaucht."""
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        r = requests.get(f"{_base()}/history/{prompt_id}", timeout=10)
        if r.ok and (hist := r.json()).get(prompt_id):
            return hist[prompt_id]
        time.sleep(POLL_INTERVAL)
    raise SystemExit(f"Zeitüberschreitung ({TIMEOUT}s) beim Warten auf ComfyUI.")


def _wait_ws(prompt_id: str, client_id: str) -> None:
    """Mit websocket-client blockieren, bis das Prompt fertig ist (schneller als Polling)."""
    import websocket  # websocket-client
    ws = websocket.WebSocket()
    ws.connect(f"ws://{COMFY_HOST}/ws?clientId={urllib.parse.quote(client_id)}",
               timeout=TIMEOUT)
    try:
        deadline = time.monotonic() + TIMEOUT
        while time.monotonic() < deadline:
            msg = ws.recv()
            if not isinstance(msg, str):
                continue
            data = json.loads(msg)
            # 'executing' mit node=None und passender prompt_id = fertig.
            if data.get("type") == "executing":
                d = data.get("data", {})
                if d.get("node") is None and d.get("prompt_id") == prompt_id:
                    return
        raise SystemExit(f"Zeitüberschreitung ({TIMEOUT}s) beim Warten auf ComfyUI.")
    finally:
        ws.close()


def _collect_images(requests, history: dict) -> list:
    """Alle Output-Bilder des Auftrags über /view holen → PIL.Image-Liste."""
    from PIL import Image
    images = []
    for node_out in history.get("outputs", {}).values():
        for img in node_out.get("images", []):
            params = urllib.parse.urlencode({
                "filename": img["filename"],
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output"),
            })
            r = requests.get(f"{_base()}/view?{params}", timeout=30)
            r.raise_for_status()
            images.append(Image.open(io.BytesIO(r.content)).convert("RGBA"))
    return images


def run(wf: dict, client_id: str = "sd_gen") -> list:
    """Workflow ausführen und die erzeugten Bilder als PIL.Image-Liste zurückgeben."""
    requests = _requests()
    prompt_id = _queue(requests, wf, client_id)
    try:
        _wait_ws(prompt_id, client_id)
    except ImportError:
        _wait_history(requests, prompt_id)   # websocket-client nicht installiert
    r = requests.get(f"{_base()}/history/{prompt_id}", timeout=10)
    r.raise_for_status()
    history = r.json().get(prompt_id, {})
    images = _collect_images(requests, history)
    if not images:
        raise SystemExit("ComfyUI lieferte keine Bilder — Workflow-Output-Node prüfen.")
    return images


if __name__ == "__main__":
    ok, msg = is_up()
    print(("OK   " if ok else "FEHLT ") + msg)
    raise SystemExit(0 if ok else 1)

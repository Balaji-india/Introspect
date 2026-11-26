"""One-command demo start: check deps, pick a port, start the API, warm caches, open the dashboard.

    python scripts/start_demo.py              # or just double-click demo.bat
    python scripts/start_demo.py --no-browser --port 8000
"""
from __future__ import annotations

import argparse
import importlib
import json
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["numpy", "pandas", "scipy", "sklearn", "lightgbm", "fastapi", "uvicorn", "pydantic"]


def check_imports() -> bool:
    missing = []
    for mod in REQUIRED:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(f"[demo] Missing Python packages: {', '.join(missing)}")
        print("[demo] Fix: python -m venv .venv  then  .venv\\Scripts\\activate  then  pip install -r requirements.txt")
        return False
    return True


def _get(url: str, timeout: float = 2.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:   # noqa: S310 - localhost only
        return json.loads(r.read().decode())


def is_introspect(port: int) -> bool:
    try:
        return _get(f"http://127.0.0.1:{port}/api/health", 1.0).get("status") == "ok"
    except Exception:  # noqa: BLE001
        return False


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


EDGE_PATHS = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
              Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]


def open_browser(url: str) -> None:
    """On Windows prefer Microsoft Edge (the browser the demo, incl. the offline voice, was tested in)."""
    edge = next((p for p in EDGE_PATHS if p.exists()), None) if sys.platform == "win32" else None
    if edge is not None:
        subprocess.Popen([str(edge), "--new-window", url])
    else:
        webbrowser.open(url)


def warm(base: str) -> None:
    """Hit the heavy endpoints once so the first dashboard load is instant."""
    for path in ("/api/brief", "/api/timeline", "/api/forecast"):
        try:
            _get(base + path, 30)
        except Exception as e:  # noqa: BLE001
            print(f"[demo] warm-up of {path} failed: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    if not check_imports():
        return 1

    port = a.port
    if is_introspect(port):
        url = f"http://127.0.0.1:{port}"
        print(f"[demo] Introspect is already running at {url}")
        if not a.no_browser:
            open_browser(url)
        return 0
    while not port_free(port):
        print(f"[demo] Port {port} is busy, trying {port + 1}")
        port += 1
        if port > a.port + 20:
            print("[demo] No free port found near", a.port)
            return 1

    url = f"http://127.0.0.1:{port}"
    t0 = time.time()
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1",
                             "--port", str(port), "--log-level", "warning"], cwd=ROOT)
    try:
        while not is_introspect(port):
            if proc.poll() is not None:
                print("[demo] The server exited during startup (see the error above).")
                return 1
            if time.time() - t0 > 60:
                print("[demo] The server did not become healthy within 60 s.")
                proc.terminate()
                return 1
            time.sleep(0.2)
        warm(url)
        print(f"[demo] Ready in {time.time() - t0:.1f} s at {url}   (Ctrl+C to stop)")
        if not a.no_browser:
            open_browser(url)
        return proc.wait()
    except KeyboardInterrupt:
        print("\n[demo] Stopping.")
        proc.terminate()
        return 0


if __name__ == "__main__":
    sys.exit(main())

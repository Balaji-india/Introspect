#!/usr/bin/env sh
# One-command Introspect demo (macOS/Linux). Uses .venv if present.
cd "$(dirname "$0")" || exit 1
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi
exec "$PY" scripts/start_demo.py "$@"

#!/bin/sh
set -eu
cd "$(dirname "$0")"
if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Installera Python 3.12 och starta igen. Appen ar inte testad med Python 3.15."
  exit 1
fi
if [ ! -f .venv312/bin/python ]; then
  python3.12 -m venv .venv312
fi
.venv312/bin/python -c 'import sys; sys.exit(sys.version_info[:2] != (3, 12))'
.venv312/bin/python -m pip install --only-binary=:all: -r requirements.txt
if [ "${PLAGG_START:-}" = mobile ]; then
  exec .venv312/bin/python mobile_start.py
fi
exec .venv312/bin/python app.py

#!/bin/sh
set -eu
cd /workspace/Reselling-automatation
python3 -m venv /workspace/.venvs/resell
/workspace/.venvs/resell/bin/python -m pip install -r requirements-dev.txt

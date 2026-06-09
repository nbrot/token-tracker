#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PYTHON=/opt/homebrew/bin/python3.12

# Create venv if absent
if [ ! -d .venv ]; then
    "$PYTHON" -m venv .venv
fi

# Install deps if needed
.venv/bin/pip show rumps &>/dev/null || .venv/bin/pip install -r requirements.txt -q

.venv/bin/python main.py

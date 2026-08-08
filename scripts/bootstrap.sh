#!/usr/bin/env bash
set -euo pipefail
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r services/backend/requirements.txt
cp -n .env.example .env || true

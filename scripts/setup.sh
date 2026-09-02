#!/usr/bin/env bash
# One-time setup: virtualenv, dependencies, Chromium for PDF rendering and
# auto-fill, and the local (gitignored) config/profile files.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
if [ ! -d .venv ]; then
  echo "==> creating .venv with $PYTHON"
  "$PYTHON" -m venv .venv
fi
echo "==> installing dependencies"
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "==> installing Chromium for Playwright (PDF rendering + application auto-fill)"
.venv/bin/playwright install chromium

[ -f .env ] || cp .env.example .env
[ -f config.json ] || cp config.example.json config.json
[ -f data/profile.json ] || cp data/profile.example.json data/profile.json
mkdir -p materials/personal data/documents

cat <<'MSG'

Setup complete. Next:
  1. Put your Anthropic API key in .env (optional but recommended; without it
     the app runs in deterministic "basic" mode).
  2. Build your materials from your resume:
       .venv/bin/python scripts/onboard.py --resume path/to/resume.pdf [--cover-letter path/to/letter.docx]
  3. Run the app:
       .venv/bin/python run.py     ->  http://127.0.0.1:5151
  4. In Settings: search keywords, locations, company watchlist, dream companies.
MSG

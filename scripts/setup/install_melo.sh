#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MELO_ENV="$REPO_ROOT/.venv-melo"
MELO_REF="${MELO_REF:-209145371cff8fc3bd60d7be902ea69cbdb7965a}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to create the Melo environment." >&2
  exit 1
fi

cd "$REPO_ROOT"

if [ ! -d "$MELO_ENV" ]; then
  uv venv --python 3.11 "$MELO_ENV"
fi
"$MELO_ENV/bin/python" -m pip install --upgrade pip "setuptools<81"
"$MELO_ENV/bin/python" -m pip install "git+https://github.com/myshell-ai/MeloTTS.git@${MELO_REF}"
"$MELO_ENV/bin/python" "$REPO_ROOT/scripts/experiments/melo_smoke.py" \
  --language EN \
  --speaker EN-US \
  --text "Preparation check for MeloTTS." \
  --output "$REPO_ROOT/runtime/outputs/.melo-prepare.wav" \
  --check-only

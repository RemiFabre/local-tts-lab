#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

PYTORCH_ENABLE_MPS_FALLBACK=1 "$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/scripts/experiments/kokoro_voice_sweep.py" \
  --lang fr \
  --text "Bonjour depuis le balayage des voix Kokoro. Ceci est une courte phrase de comparaison."

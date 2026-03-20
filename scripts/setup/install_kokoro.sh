#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$repo_root"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found on PATH." >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required to install espeak-ng on macOS." >&2
  exit 1
fi

if ! command -v espeak-ng >/dev/null 2>&1; then
  echo "Installing espeak-ng with Homebrew..."
  brew install espeak-ng
fi

if [ ! -d .venv ]; then
  uv venv --python 3.12 .venv
fi

uv pip install --python .venv/bin/python pip
uv pip install --python .venv/bin/python "kokoro>=0.9.4" soundfile

echo "Kokoro environment is ready at $repo_root/.venv"
echo "Try:"
echo "  PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python scripts/experiments/kokoro_smoke.py --lang-code a --voice af_heart --text 'Hello from Kokoro.' --output runtime/outputs/kokoro-en.wav"

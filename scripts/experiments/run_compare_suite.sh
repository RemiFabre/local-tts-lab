#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

PYTORCH_ENABLE_MPS_FALLBACK=1 "$REPO_ROOT/.venv/bin/local-tts" compare-suite \
  --langs en fr \
  --backends macos-say kokoro melo piper

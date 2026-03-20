# local-tts-lab

Local-first text-to-speech research and benchmarking for Apple Silicon macOS.

This repository is focused on a simple question: what should we run locally on a Mac when we want high-quality, scriptable speech for coding agents and robotics experiments?

## Current status

This first pass includes:

- a research document covering the strongest Apple Silicon local TTS contenders
- an initial recommendation and ranked shortlist
- a realistic benchmark plan for local evaluation
- a multi-backend CLI for `say`, Kokoro, MeloTTS, and Piper
- bring-up notes plus helper scripts for local smoke tests and compare runs

## Quick start

```bash
cd /Users/remi/local-tts-lab
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -m local_tts_lab.cli doctor
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -m local_tts_lab.cli backends
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -m local_tts_lab.cli compare-suite
```

If you want the installed script:

```bash
cd /Users/remi/local-tts-lab
python3 -m pip install -e .
PYTORCH_ENABLE_MPS_FALLBACK=1 local-tts compare-suite
local-tts play-compare --lang en
```

## Setup helpers

```bash
cd /Users/remi/local-tts-lab
scripts/setup/install_kokoro.sh
.venv/bin/local-tts install piper-voices
scripts/setup/install_melo.sh
```

The Melo helper creates a dedicated Python 3.11 environment in `.venv-melo` because its dependency set is less happy on Python 3.12.

## Layout

- `docs/research/`
  - source-backed research notes and recommendations
- `docs/benchmarks/`
  - benchmark design and evaluation rubric
- `docs/runbooks/`
  - next-step implementation plans and operational notes
- `benchmarks/`
  - future runners, manifests, and result summaries
- `scripts/`
  - setup helpers and one-off workflow scripts
- `src/local_tts_lab/`
  - local Python package and CLI entry point
- `runtime/`
  - downloaded models, caches, and generated audio artifacts

## First documents

- `docs/research/2026-03-20-apple-silicon-local-tts-first-pass.md`
- `docs/benchmarks/benchmark-plan.md`
- `docs/benchmarks/2026-03-20-first-compare-suite.md`
- `docs/runbooks/next-steps.md`
- `docs/runbooks/kokoro-bringup-2026-03-20.md`
- `docs/runbooks/melo-bringup-2026-03-20.md`

## Near-term intent

The planned first benchmark wave is:

1. macOS `say` as the built-in control
2. Kokoro-82M as the first quality-first benchmark
3. MeloTTS as the practical English/French comparison
4. Piper as the reliability and latency baseline

## Notes

- The core system is intended to stay local-first.
- Cloud APIs may appear only as external comparison points, not dependencies.
- Runtime artifacts live under `runtime/` and are ignored by git by default.
- The latest compare suite currently writes EN/FR outputs and a `summary.tsv` under `runtime/outputs/compare/`.

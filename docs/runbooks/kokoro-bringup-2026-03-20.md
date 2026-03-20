# Kokoro Bring-Up

Date: 2026-03-20

## Goal

Verify that Kokoro can run locally on this Apple Silicon Mac with usable English and French output.

## What worked

- `espeak-ng` installed successfully via Homebrew
- a repo-local Python 3.12 virtualenv worked
- `kokoro==0.9.4` installed cleanly with `uv pip`
- MPS is available in PyTorch on this machine
- English smoke test succeeded with `af_heart`
- French smoke test succeeded with `ff_siwis`

## Setup notes

### Environment

- Python: `3.12.12` in `.venv`
- PyTorch: `2.10.0`
- `PYTORCH_ENABLE_MPS_FALLBACK=1` was set for the smoke tests

### First-run wrinkle

The `uv` virtualenv did not initially expose `python -m pip`, and Kokoro appears to rely on that during first-run setup. Installing `pip` into the virtualenv fixed that issue:

```bash
uv pip install --python .venv/bin/python pip
```

### English first-run behavior

On the first English run, Kokoro automatically installed the spaCy model `en_core_web_sm`. That completed successfully.

## Smoke test commands

### English

```bash
cd /Users/remi/local-tts-lab
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python scripts/experiments/kokoro_smoke.py \
  --lang-code a \
  --voice af_heart \
  --text "Hello from the local TTS lab. This is a first Kokoro smoke test on Apple Silicon." \
  --output runtime/outputs/kokoro-en-smoke.wav
```

### French

```bash
cd /Users/remi/local-tts-lab
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python scripts/experiments/kokoro_smoke.py \
  --lang-code f \
  --voice ff_siwis \
  --text "Bonjour. Ceci est un test Kokoro en francais sur Apple Silicon. Je veux verifier que la voix francaise est bien exploitable." \
  --output runtime/outputs/kokoro-fr-smoke.wav
```

## Output artifacts

Generated locally under:

- `runtime/outputs/kokoro-en-smoke.wav`
- `runtime/outputs/kokoro-fr-smoke.wav`

These runtime files are intentionally ignored by git.

## Current assessment

- Kokoro is viable on this machine.
- English is immediately promising.
- French is available and functioning, but the bigger question is still subjective quality, because Kokoro has a much thinner French voice inventory than English.

## Next step

Compare Kokoro directly against MeloTTS on the same short English and French prompts before wiring either one into a more permanent backend.

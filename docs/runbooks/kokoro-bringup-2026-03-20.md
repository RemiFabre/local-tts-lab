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

## Latency snapshot

From the first shared compare suite:

- English `af_heart`: `2.96s` elapsed for `7.53s` of audio
- French `ff_siwis`: `2.69s` elapsed for `8.85s` of audio

From a warm-process benchmark in a single Python process:

- English pipeline init: `2.45s`
- English first synthesis after init: `1.64s` for `6.88s` of audio
- English second synthesis in the same process: `1.48s` for `6.88s` of audio
- French pipeline init: `1.87s`
- French first synthesis after init: `1.35s` for `7.12s` of audio
- French second synthesis in the same process: `1.52s` for `7.12s` of audio

Interpretation:

- the current CLI measures a cold per-invocation path because it creates a new pipeline each time
- keeping a process alive and reusing the pipeline saves roughly `1.5s` to `2.5s` of startup on this machine

## Cache size and RAM notes

Local Hugging Face cache on this machine:

- total `hexgrad/Kokoro-82M` cache: about `313 MB`
- main model weights `kokoro-v1_0.pth`: about `312 MB`
- each tested voice tensor (`af_heart`, `ff_siwis`): about `511 KB`

Observed peak process RSS during warm-process benchmarking:

- English run: about `1.84 GB` after first synthesis and `1.93 GB` after the second
- French run: about `1.66 GB` after first synthesis and `1.80 GB` after the second

These are process-level numbers on this Mac, not a formal end-to-end memory profile.

## Hugging Face warning

You may see:

```text
Warning: You are sending unauthenticated requests to the HF Hub.
```

That does not mean Kokoro is fully redownloading on every run. The relevant files are already cached locally under `~/.cache/huggingface/hub/models--hexgrad--Kokoro-82M`. The warning means the library is talking to the public Hugging Face Hub without a token, so requests are anonymous and subject to lower rate limits.

For local public-model use:

- no token is required
- a token is still nice to have because it avoids anonymous-rate-limit issues and is useful for future model work

## Preload direction

The upstream `kokoro` package is designed so one `KModel` can be reused across multiple `KPipeline` instances. For agent usage, the next optimization is straightforward:

- keep one long-lived Python worker alive
- preload one `KModel`
- keep one English pipeline and one French pipeline resident
- send text requests to that worker instead of launching a fresh CLI process each time

## Next step

Build a small always-on Kokoro worker so agent speech requests hit the warm path instead of paying cold-start cost each time.

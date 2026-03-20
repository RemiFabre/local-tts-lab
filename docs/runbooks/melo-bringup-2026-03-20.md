# Melo Bring-Up

Date: 2026-03-20

## Goal

Verify that MeloTTS can run locally on this Apple Silicon Mac with usable English and French output.

## What worked

- a dedicated Python 3.11 environment in `.venv-melo`
- local English synthesis with `EN-US`
- local French synthesis with `FR`
- repeated synthesis through the shared `local-tts` CLI
- a repo-local cache for NLTK data and UniDic fixes

## Setup notes

### Environment

- Python: `3.11` in `.venv-melo`
- package: `melotts==0.1.2`
- install source: `myshell-ai/MeloTTS` at commit `209145371cff8fc3bd60d7be902ea69cbdb7965a`
- `PYTORCH_ENABLE_MPS_FALLBACK=1` is the safe default on Apple Silicon

### Apple Silicon wrinkles

- Melo did not install cleanly in the main Python 3.12 environment because of older dependency pins.
- A dedicated Python 3.11 environment avoided the `tokenizers` build problem.
- `librosa` still expects `pkg_resources`, so `setuptools<81` is pinned in `.venv-melo`.
- Melo imports Japanese text tooling eagerly, so UniDic has to be present even for English and French.
- `mecab-python3` expected a valid `unidic/dicdir` plus `mecabrc`; the helper script now normalizes that layout automatically.
- English also needed repo-local NLTK resources, especially `averaged_perceptron_tagger_eng` and `cmudict`.

## Install command

```bash
cd /Users/remi/local-tts-lab
scripts/setup/install_melo.sh
```

That helper creates `.venv-melo`, installs Melo from the pinned Git commit, prepares UniDic, and downloads the required NLTK data into `runtime/cache/nltk_data`.

## Smoke test commands

### English

```bash
cd /Users/remi/local-tts-lab
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -m local_tts_lab.cli speak \
  --backend melo \
  --lang en \
  --output runtime/outputs/melo-en-check.wav \
  "Hello from Melo on Apple Silicon. This is a local English smoke test."
```

Observed result:

- `elapsed=18.16s`
- `audio=5.11s`

### French

```bash
cd /Users/remi/local-tts-lab
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -m local_tts_lab.cli speak \
  --backend melo \
  --lang fr \
  --output runtime/outputs/melo-fr-check.wav \
  "Bonjour depuis Melo sur Apple Silicon. Ceci est un test local en francais."
```

Observed result:

- `elapsed=33.82s`
- `audio=5.14s`

## Current assessment

- Melo is now viable on this machine for English and French.
- It is slower than Piper and Kokoro on cold runs, but it is straightforward to call from the shared CLI.
- The multilingual story is attractive enough to keep it in the main benchmark set.

## Next step

Keep Melo in the compare suite and judge it mostly on voice quality and French performance rather than raw latency.

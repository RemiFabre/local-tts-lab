# Kokoro Voice Sweeps

Date: 2026-03-21

## Goal

Make it easy to generate one comparison sample per available Kokoro English or French voice.

## Voice listing

List the currently available English voices:

```bash
kokoro-say --lang en --list-voices
```

List the currently available French voices:

```bash
kokoro-say --lang fr --list-voices
```

Current observed inventory from the official `hexgrad/Kokoro-82M` model repo:

- English voices: `28`
- French voices: `1`

## Sweep commands

Run the English sweep:

```bash
cd /Users/remi/local-tts-lab
scripts/experiments/run_kokoro_english_voices.sh
```

Run the French sweep:

```bash
cd /Users/remi/local-tts-lab
scripts/experiments/run_kokoro_french_voices.sh
```

Advanced usage with a custom sentence:

```bash
cd /Users/remi/local-tts-lab
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python scripts/experiments/kokoro_voice_sweep.py \
  --lang en \
  --text "Hello from a custom Kokoro voice sweep sentence."
```

## Output layout

The sweep runner writes to:

- `runtime/outputs/kokoro-voice-sweeps/<timestamp>/en/`
- `runtime/outputs/kokoro-voice-sweeps/<timestamp>/fr/`

Each directory contains:

- one wav per voice
- a `summary.tsv` with voice name, elapsed time, audio duration, and output path

## First generated runs

English sweep:

- directory: `runtime/outputs/kokoro-voice-sweeps/20260321-103423/en/`
- summary: `runtime/outputs/kokoro-voice-sweeps/20260321-103423/en/summary.tsv`

French sweep:

- directory: `runtime/outputs/kokoro-voice-sweeps/20260321-103412/fr/`
- summary: `runtime/outputs/kokoro-voice-sweeps/20260321-103412/fr/summary.tsv`

## Notes

- The sweeps use the warm Kokoro daemon, so they benefit from the model already being resident in RAM.
- The English inventory is much richer than the French one right now.
- `ff_siwis` is still the only French voice surfaced by the current official voice list.

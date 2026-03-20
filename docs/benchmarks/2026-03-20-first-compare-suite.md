# First Compare Suite

Date: 2026-03-20

## Goal

Capture a first local EN/FR compare run that can be regenerated with one command.

## Command

```bash
cd /Users/remi/local-tts-lab
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -m local_tts_lab.cli compare-suite \
  --langs en fr \
  --backends macos-say kokoro melo piper
```

Equivalent helper:

```bash
cd /Users/remi/local-tts-lab
scripts/experiments/run_compare_suite.sh
```

## Output directory

- `runtime/outputs/compare/20260320-170443/`
- `runtime/outputs/compare/20260320-170443/summary.tsv`

## First timings

| Lang | Backend | Voice | Elapsed | Audio |
| --- | --- | --- | --- | --- |
| en | macOS `say` | `Samantha` | `1.40s` | `6.43s` |
| en | Kokoro | `af_heart` | `2.96s` | `7.53s` |
| en | MeloTTS | `EN-US` | `9.24s` | `7.40s` |
| en | Piper | `en_US-lessac-medium` | `0.72s` | `6.39s` |
| fr | macOS `say` | `Thomas` | `0.46s` | `7.72s` |
| fr | Kokoro | `ff_siwis` | `2.69s` | `8.85s` |
| fr | MeloTTS | `FR` | `10.72s` | `7.94s` |
| fr | Piper | `fr_FR-siwis-medium` | `0.70s` | `7.95s` |

## Quick take

- Piper is the clear startup and latency baseline.
- Kokoro is fast enough locally that it remains the most attractive quality-first default.
- Melo is slower, but it is now stable enough to keep in the first listening round because English and French both worked.
- macOS `say` remains a useful built-in control and an instant fallback.

## Playback

To listen to the latest run in English:

```bash
cd /Users/remi/local-tts-lab
.venv/bin/local-tts play-compare --lang en
```

To listen to the latest run in French:

```bash
cd /Users/remi/local-tts-lab
.venv/bin/local-tts play-compare --lang fr
```

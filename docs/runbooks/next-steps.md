# Next Steps

Date: 2026-03-20

## Immediate plan

### Phase 1: make the repo runnable

1. Add a unified backend interface under `src/local_tts_lab/backends/`.
2. Keep the existing macOS `say` adapter as the first backend.
3. Add Piper backend support next.
4. Add Kokoro backend support after Piper.

Suggested commit slices:

- `Add backend protocol and macOS say adapter`
- `Add Piper backend and voice download helper`
- `Add Kokoro backend and basic voice selection`

### Phase 2: benchmark harness

1. Add benchmark manifests and a fixed EN/FR corpus.
2. Add a runner that records:
  - cold-start time
  - warm-path time
  - peak RSS
  - output duration
3. Write markdown summaries automatically after each run.

Suggested commit slices:

- `Add bilingual benchmark corpus and manifests`
- `Add benchmark runner with timing and memory capture`
- `Write markdown benchmark summaries from run artifacts`

### Phase 3: cloning / frontier branch

1. Decide whether cloning is required immediately.
2. If yes, add XTTS-v2 first.
3. Add OuteTTS after XTTS-v2, or earlier if Apple Silicon-native experimentation is more valuable than cloning.

Suggested commit slices:

- `Add XTTS v2 backend for cloning benchmark`
- `Add OuteTTS backend for Metal path experiment`

## Proposed repo structure

Keep the root uncluttered and push detail down one level:

```text
local-tts-lab/
  README.md
  pyproject.toml
  docs/
    research/
    benchmarks/
    runbooks/
  benchmarks/
    corpora/
    manifests/
    reports/
  scripts/
    setup/
    maintenance/
  src/
    local_tts_lab/
      backends/
      benchmarking/
      cli.py
  runtime/
    cache/
    models/
    outputs/
```

## Recommended implementation order

### Order for the first usable system

1. `say`
2. Piper
3. Kokoro

Reason:

- this gives an immediate fallback, a practical open baseline, and a likely best-quality option

### Order for the first deeper benchmark wave

1. XTTS-v2
2. OuteTTS 1.0-0.6B
3. Chatterbox Multilingual

Reason:

- XTTS-v2 answers the cloning question quickly
- OuteTTS tests the explicit Apple Silicon frontier path
- Chatterbox can follow once the base harness is stable

## CLI direction

Keep one simple agent-facing entry point:

```bash
local-tts speak "Hello world"
local-tts speak --backend piper --voice en_US-lessac-medium "Hello world"
local-tts benchmark run phase1
```

The outer CLI should stay stable even if backend internals change.

## Operational notes

- Prefer long-lived workers or servers for backends that reload weights slowly.
- Keep runtime artifacts under `runtime/` only.
- Store benchmark results as files, not just terminal output.
- Make small commits after each backend or benchmark milestone.
- Pushing frequently only becomes possible once a remote is configured for this repo.

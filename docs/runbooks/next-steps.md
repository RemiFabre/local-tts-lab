# Next Steps

Date: 2026-03-20

## Immediate plan

### Phase 1: make the repo runnable

1. Add a unified backend interface under `src/local_tts_lab/backends/`.
2. Keep the existing macOS `say` adapter as the first backend.
3. Add Kokoro backend support next.
4. Add MeloTTS backend support after Kokoro.

Suggested commit slices:

- `Add backend protocol and macOS say adapter`
- `Add Kokoro backend and basic voice selection`
- `Add MeloTTS backend and fixed voice presets`

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
2. If not, add Qwen3-TTS next as the quality-focused larger model experiment.
3. Add XTTS-v2 or OuteTTS later only if priorities swing back toward cloning or speaker-reference workflows.

Suggested commit slices:

- `Add Qwen3-TTS backend for quality benchmark`
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
2. Kokoro
3. MeloTTS

Reason:

- this gives an immediate fallback plus two of the strongest non-cloning EN/FR candidates

### Order for the first deeper benchmark wave

1. Qwen3-TTS
2. Piper
3. Chatterbox Multilingual

Reason:

- Qwen3-TTS is now the first larger-quality experiment worth the effort
- Piper becomes a pragmatic reliability comparison instead of the main target
- Chatterbox can follow once the base harness is stable

## CLI direction

Keep one simple agent-facing entry point:

```bash
local-tts speak "Hello world"
local-tts speak --backend kokoro --voice af_heart "Hello world"
local-tts benchmark run phase1
```

The outer CLI should stay stable even if backend internals change.

## Operational notes

- Prefer long-lived workers or servers for backends that reload weights slowly.
- Keep runtime artifacts under `runtime/` only.
- Store benchmark results as files, not just terminal output.
- Make small commits after each backend or benchmark milestone.
- Pushing frequently only becomes possible once a remote is configured for this repo.

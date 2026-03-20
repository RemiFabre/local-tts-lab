# Benchmark Plan

Date: 2026-03-20

## Goal

Run mostly autonomous local benchmarks on Apple Silicon macOS that compare:

- subjective naturalness
- intelligibility
- speed
- startup cost
- RAM usage
- ease of invocation from shell and Python

## Guiding principles

- Keep the benchmark reproducible.
- Keep the corpus small enough to run often.
- Separate cold-start and warm-path measurements.
- Treat subjective evaluation as primary for audio quality.
- Use objective proxies only where they are honest and helpful.

## Benchmark matrix

### Phase 1 runners

- macOS `say`
- Kokoro-82M
- MeloTTS

### Phase 2 runners

- Qwen3-TTS
- Piper

### Phase 3 runners

- XTTS-v2
- OuteTTS 1.0-0.6B
- Chatterbox Multilingual
- F5-TTS

## Test corpus

Use a fixed corpus with both English and French.

### English sets

- `agent_short`
  - 10 short assistant-style messages
  - 5 to 20 words each
- `agent_medium`
  - 10 medium summaries
  - 30 to 90 words each
- `robotics_commands`
  - 10 action-oriented utterances
  - status, warnings, confirmations, and narrated plans

### French sets

- `agent_short_fr`
  - 10 short assistant-style messages
- `agent_medium_fr`
  - 10 medium summaries
- `robotics_commands_fr`
  - 10 action-oriented utterances

### Cloning references

For cloning-capable models only:

- one clean English reference clip, around 8 to 12 seconds
- one clean French reference clip, around 8 to 12 seconds
- one optional noisier clip to test robustness

## Metrics

### 1. Subjective naturalness

Primary metric.

Method:

- Generate all samples and review them in randomized batches.
- Score each utterance on a 1 to 5 rubric:
  - 5: natural, fluent, no distracting artifacts
  - 4: clearly usable, minor synthetic feel
  - 3: understandable but noticeably robotic or uneven
  - 2: poor pacing, artifacts, or prosody problems
  - 1: not realistically usable

Also capture pairwise preference:

- Kokoro vs MeloTTS
- Kokoro vs Qwen3-TTS
- fixed-voice baseline vs larger frontier model

### 2. Intelligibility

Important for agent and robotics use.

Primary proxy:

- Run local ASR on generated audio and compute WER / CER against the prompt text.

Suggested local ASR:

- `mlx-whisper`
- or another local Whisper runner already known to work well on the machine

Caveats:

- WER is only a proxy for intelligibility.
- It is biased by ASR weaknesses, punctuation, numerals, and accent mismatch.
- Lower WER does not automatically mean more natural speech.

### 3. Speed

Measure:

- wall-clock synthesis time
- audio duration
- real-time factor:
  - `synthesis_time / output_audio_duration`
- reciprocal real-time factor:
  - `output_audio_duration / synthesis_time`

Report both:

- cold run
- warm run after model load

### 4. Startup cost

Measure separately from ongoing synthesis:

- install/setup effort
- first model download time
- first import / initialization time
- first utterance completion time

For server-capable engines, also measure:

- time to start daemon/server
- time for first request after server is up

### 5. RAM usage

Measure:

- peak RSS during cold initialization
- peak RSS during one medium utterance
- peak RSS during repeated batch generation

Practical macOS methods:

- `/usr/bin/time -l ...` for peak resident set size
- `ps -o rss= -p <pid>` sampling for long-lived workers

### 6. Ease of invocation

Use a simple rubric from 1 to 5:

- 5: one obvious command, good defaults, stable output, clean errors
- 4: simple wrapper needed, otherwise smooth
- 3: works but setup or invocation is somewhat fiddly
- 2: several sharp edges, poor defaults, or awkward environment handling
- 1: too fragile for routine agent usage

Evaluate:

- shell invocation
- Python invocation
- stdin / file input support
- output file control
- repeat-call ergonomics
- whether a long-lived worker is practical

## What is meaningful and what is not

### Meaningful

- Subjective naturalness
- Pairwise preference
- WER / CER as a rough intelligibility proxy
- Cold-start and warm-path timing
- Peak RSS
- Installation and invocation friction

### Weak or misleading if overused

- Single-number "quality" scores without listening
- Speaker similarity metrics when the model does not target cloning
- MOS-style scoring from only one listener
- Tiny sample sets that overfit to one speaking style

## Benchmark harness design

The harness should be mostly autonomous once adapters exist.

### Inputs

- benchmark manifest describing:
  - backend
  - language
  - prompt set
  - voice or speaker reference
  - output directory

### Outputs

- generated audio files
- machine-readable metrics JSON
- markdown summary per run
- a combined comparison table across runs

### Suggested artifact layout

- `runtime/outputs/<date>/<backend>/<case>.wav`
- `runtime/outputs/<date>/<backend>/metrics.json`
- `runtime/outputs/<date>/<backend>/summary.md`

## Suggested implementation details

### Unified backend interface

Each backend adapter should expose:

- `prepare()`
- `synthesize(text, language, voice, output_path, options)`
- `metadata()`
- `supports_cloning()`

### Measurement wrapper

For every synthesis call, capture:

- start timestamp
- end timestamp
- output audio duration
- peak RSS if available
- return code
- stderr snapshot

### Repetition policy

For timing:

- 1 cold run
- 3 warm runs
- report median warm result

For subjective review:

- at least 10 English and 10 French samples before drawing conclusions

## Recommended first autonomous sequence

1. Implement adapters for `say`, Piper, and Kokoro.
1. Implement adapters for `say`, Kokoro, and MeloTTS.
2. Create a small EN/FR benchmark corpus.
3. Run cold and warm synthesis tests for all three.
4. Generate a listening pack for manual review.
5. Add Qwen3-TTS next if the fixed-voice baselines are promising.
6. Add XTTS-v2 or OuteTTS only if later priorities change.

## Success criteria for phase 1

We should be able to answer:

- Is Kokoro clearly better than MeloTTS for the English/French quality target?
- Is the quality gap large enough to justify extra setup?
- Is `say` still valuable as a fallback backend?
- Is Qwen3-TTS worth its extra complexity on this Mac once we hear Kokoro and MeloTTS?

# Kokoro Daemon

Date: 2026-03-20

## Goal

Make Kokoro feel closer to `say` by keeping the model warm between invocations.

## What exists now

- a long-lived local Kokoro daemon
- one shared `KModel` kept resident in RAM
- one English pipeline and one French pipeline preloaded
- an auto-starting `kokoro-say` CLI
- daemon management through `local-tts kokoro-daemon ...`

## Main commands

Start the daemon explicitly:

```bash
cd /Users/remi/local-tts-lab
.venv/bin/local-tts kokoro-daemon start
```

Check whether it is running:

```bash
cd /Users/remi/local-tts-lab
.venv/bin/local-tts kokoro-daemon status
```

Speak English:

```bash
kokoro-say "Hello from warm Kokoro."
```

Speak French:

```bash
kokoro-say --lang fr "Bonjour depuis Kokoro."
```

Pipe text from another command:

```bash
echo "This came from stdin." | kokoro-say
```

Generate a wav without playing it:

```bash
kokoro-say --lang fr --no-play --print-path "Bonjour." 
```

Stop the daemon:

```bash
cd /Users/remi/local-tts-lab
.venv/bin/local-tts kokoro-daemon stop
```

## Runtime files

- socket: `runtime/cache/kokoro-service/kokoro.sock`
- pid file: `runtime/cache/kokoro-service/kokoro.pid`
- daemon log: `runtime/cache/kokoro-service/kokoro.log`
- generated warm-path audio: `runtime/outputs/kokoro-live/`

## Behavior

- `kokoro-say` auto-starts the daemon if it is not already running.
- The first request after daemon start is still slower because PyTorch/MPS has to warm up.
- After that, repeated calls reuse the already-loaded model and pipelines.

## First measured warm-path results

Daemon start status:

- `pid=24453`
- `device=mps`
- `rss_mb=1254.6` immediately after preload

Repeated shell invocations:

- first English invocation after restart: `5.85s` elapsed for `5.50s` of audio
- second English invocation: `0.87s` elapsed for `5.58s` of audio
- first French invocation after English warm-up: `0.97s` elapsed for `5.62s` of audio

Interpretation:

- the model preload is working
- the first real synthesis still pays a one-time warm-up penalty
- after that, the user-facing command is much closer to the responsiveness we want for agent speech

## Design note

The current command still writes a wav file before playback and then plays it with `afplay`. That is deliberate for now because it keeps the implementation simple, scriptable, and debuggable.

## Next step

If we keep leaning into Kokoro, the next good improvement is a tiny stable API layer around the daemon so local agents can call it with JSON payloads instead of shell arguments.

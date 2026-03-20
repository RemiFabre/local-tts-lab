# Apple Silicon Local TTS First Pass

Date: 2026-03-20

## Goal

Identify the strongest local text-to-speech contenders for Apple Silicon macOS, with special attention to:

- robust local usage
- shell and Python integration
- English and French support
- coding-agent narration
- robotics experiments

## Scope and assumptions

- This is a local-first pass. Cloud APIs are out of scope for the core system.
- The machine is Apple Silicon macOS.
- Streaming is not required yet, but cold-start and repeated-call latency still matter.
- "Runs on Apple Silicon" is marked carefully:
  - `documented` means the official source explicitly mentions macOS, Apple Silicon, MPS, Metal, or a Mac install path.
  - `inferred` means the official package is local and Python-based, but Apple Silicon is not called out as a first-class path in the docs I reviewed.

## Bottom line

If we only benchmark a small first wave, the highest-value set is:

1. `say` as the built-in control
2. Kokoro-82M as the most likely high-quality, low-drama fit
3. Qwen3-TTS as the ambitious high-quality multilingual bet
4. MeloTTS as the practical fixed-voice EN/FR backup
5. Piper as the boring-but-reliable baseline if we still want one

My recommendation for the first three open-model benchmarks is:

1. Kokoro-82M
2. MeloTTS
3. Qwen3-TTS

If you want to push quality upward after that, add a larger Qwen3-TTS variant next.

Qwen3-TTS should also be on the board, but not as a first default for this repo:

- it is clearly a serious frontier contender
- it supports French, instruction control, and nice built-in voices
- but the official local path is much more CUDA / FlashAttention / vLLM flavored than Apple Silicon flavored

## Ranked shortlist

| Rank | Contender | Why test early | Main caution |
| --- | --- | --- | --- |
| Control | macOS `say` | Instant local baseline, best cold-start control, trivial CLI use | Not the open-model target architecture |
| 1 | Kokoro-82M | Best blend of quality, Mac fit, and built-in English/French voices | French voice inventory is thin |
| 2 | Qwen3-TTS | High-end multilingual quality path with instruction control and better voice options | Official local docs are CUDA/FlashAttention-first, not Mac-first |
| 3 | MeloTTS | Practical fixed-voice EN/FR option with simple CLI and MPS path | Less exciting than Kokoro or Qwen3-TTS |
| 4 | Piper | Reliability baseline for shell and robotics usage | Quality is not the main reason to choose it |
| 5 | Chatterbox Multilingual | Interesting quality/expressiveness candidate with French support | Apple Silicon support is inferred, not first-class in docs |
| 6 | OuteTTS 1.0-0.6B | Interesting Apple Silicon-native frontier path via llama.cpp Metal | Better aligned with speaker-reference workflows than fixed-voice quality testing |
| 7 | XTTS-v2 | Strong multilingual reference if cloning becomes important later | Heavier stack, non-standard model license, and cloning is no longer a priority |
| 8 | F5-TTS | Hype-worthy quality/cloning research target | Official story is strongest for EN/ZH, weights are non-commercial |
| Watchlist | Parler-TTS Mini | Fully open, documented Apple Silicon MPS path, stylish prompting | English-only, so not a first-wave fit for this project |

## Recommendations

### Best first benchmark: Kokoro-82M

Why:

- strongest match to the new priority stack
- very likely to sound good immediately
- explicit Apple Silicon note in the official repo
- enough built-in English voices plus one usable French voice to answer the "few nice voices" requirement

Tradeoff:

- French coverage is thinner than English
- if you decide you want richer voice design later, a larger model family may still beat it

### Best bigger quality bet: Qwen3-TTS

Why:

- it moves up a lot under the new priorities
- multilingual, including English and French
- built-in custom voices and voice-design variants are more relevant than cloning now
- you have enough RAM that the larger footprints are no longer disqualifying

Tradeoff:

- the official fast path is still much more NVIDIA-oriented than Apple-Silicon-oriented
- I would treat this as a quality experiment, not as the first thing to operationalize

### Best safe multilingual backup: MeloTTS

Why:

- fixed English and French voices
- simple CLI and Python API
- official docs explicitly mention `mps`
- good candidate if Kokoro is great in English but disappoints in French

Tradeoff:

- it is more of a practical backup than a frontier quality swing
- it may not be the winner, but it is a smart comparison point

Models I would now deprioritize for phase 1:

- XTTS-v2, because cloning is no longer central
- OuteTTS, because its default path is more speaker-reference-centric
- Piper, except as a pragmatic baseline

## Recent / hyped / new contenders to call out explicitly

- Chatterbox family: repo created on 2025-04-23; current family includes Turbo (350M), Multilingual (500M), and the original English model. Very worth watching for agent-like speech generation.
- OuteTTS 1.0: model card created on 2025-05-18. Interesting because it pairs modern LLM tooling with local TTS and explicitly supports Apple Silicon / Metal installs.
- Qwen3-TTS: released by Qwen on 2026-01-22 in 0.6B and 1.7B variants. Very important to watch because it combines multilingual support, 3-second cloning, streaming support, and instruction control under Apache-2.0.
- F5-TTS v1 base: announced in the official repo on 2025-03-12. Still one of the most talked-about open voice-cloning style TTS lines, but it is not the cleanest fit for an English/French-first Mac benchmark.
- Kokoro v1.0: published on 2025-01-27. It moved very quickly from "small interesting model" to "serious practical contender."

## Detailed contender notes

### 1. macOS `say` (control, not the main open-model target)

- Model / runtime:
  - Built-in macOS speech synthesis via `/usr/bin/say`
- License:
  - Bundled Apple system component; no separate OSS model license
- Runs locally on macOS / Apple Silicon:
  - Yes, documented locally by `man say`
- Runtime / backend:
  - Speech Synthesis Manager, `say` CLI
- Approximate model size / RAM:
  - Bundled with the OS; no extra model download
- Quality strengths:
  - robust, instant, easy to invoke
- Quality weaknesses:
  - less natural and less expressive than modern neural open models
- Speed / latency:
  - excellent cold-start behavior
- Multilingual support:
  - depends on installed voices; English and French voices are available on many macOS setups
- Voice cloning / speaker conditioning:
  - none
- Ease of local scripting / CLI integration:
  - excellent
- Agent fit:
  - excellent control baseline
- Robotics fit:
  - good for reliability, limited for nuanced voice design
- Sources:
  - local observation from `man say`
  - local observation from `say -v ?`

### 2. Piper

- Model / runtime:
  - Piper engine with voice-specific ONNX VITS models
- License:
  - engine repo is GPL-3.0
  - voice licenses vary by voice and must be checked per voice `MODEL_CARD`
- Runs locally on macOS / Apple Silicon:
  - Yes, inferred from official local Python package and ONNX-based design
- Runtime / backend:
  - `piper-tts` Python package
  - ONNX Runtime
  - embedded `espeak-ng` phonemization
- Approximate model size / RAM:
  - example English and French medium ONNX voices are both about 63.2 MB
  - runtime memory is expected to be modest compared with larger transformer stacks
- Quality strengths:
  - reliable, practical, broad language coverage, strong deployment story
- Quality weaknesses:
  - less expressive and less "wow" than newer frontier models
- Speed / latency:
  - designed for local use; CLI is explicitly called out as slower because it reloads the model each run
  - persistent server mode should be preferred for repeated calls
- Multilingual support:
  - very broad language coverage, including English and French
- Voice cloning / speaker conditioning:
  - no zero-shot cloning in the standard voice-pack flow
- Ease of local scripting / CLI integration:
  - excellent; clear CLI, Python API, and server mode
- Agent fit:
  - excellent
- Robotics fit:
  - excellent
- Notes:
  - this is the cleanest "boring in a good way" baseline
- Official links:
  - Repo: [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)
  - CLI docs: [docs/CLI.md](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md)
  - Python API docs: [docs/API_PYTHON.md](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md)
  - Voices: [docs/VOICES.md](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md)
  - Voice downloads: [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/main)
  - Samples: [piper samples](https://rhasspy.github.io/piper-samples)

### 3. Kokoro-82M

- Model / runtime:
  - Kokoro-82M via the official `kokoro` inference library
- License:
  - Apache-2.0
- Runs locally on macOS / Apple Silicon:
  - Yes, documented; the official repo includes an Apple Silicon MPS note
- Runtime / backend:
  - Python package `kokoro`
  - `misaki` G2P
  - `espeak-ng` fallback
  - PyTorch, with documented MPS fallback on Mac
- Approximate model size / RAM:
  - core model file `kokoro-v1_0.pth` is about 327.2 MB
  - total model repo storage is about 1.23 GB including many voice tensors and sample assets
- Quality strengths:
  - excellent quality-per-size
  - practical voice inventory
  - strong reputation for sounding better than its size suggests
- Quality weaknesses:
  - non-English support quality varies by language and data coverage
  - French has only one official voice in the current voice list
- Speed / latency:
  - lightweight and described by the official sources as significantly faster than larger models
  - should be a strong warm-path candidate on Apple Silicon
- Multilingual support:
  - English, French, Spanish, Hindi, Italian, Japanese, Brazilian Portuguese, Mandarin Chinese
- Voice cloning / speaker conditioning:
  - no official zero-shot voice cloning path in the core library; uses predefined voice tensors
- Ease of local scripting / CLI integration:
  - strong Python fit
  - CLI story is less first-class than Piper, but wrapping it is straightforward
- Agent fit:
  - excellent
- Robotics fit:
  - very good
- Notes:
  - likely the best single model to test if we want "modern sounding, local, not huge"
- Official links:
  - Model card: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
  - Repo: [hexgrad/kokoro](https://github.com/hexgrad/kokoro)
  - Voices: [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
  - Samples: [SAMPLES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/SAMPLES.md)
  - Eval notes: [EVAL.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/EVAL.md)

### 4. MeloTTS

- Model / runtime:
  - MeloTTS multilingual fixed-speaker stack
- License:
  - MIT
- Runs locally on macOS / Apple Silicon:
  - Yes, documented for Linux and macOS
  - official Python examples mention `mps`
- Runtime / backend:
  - editable Python install
  - `melo` / `melotts` CLI
  - Python API
- Approximate model size / RAM:
  - exact model footprint is not clearly documented in the official install docs I reviewed
  - official docs state CPU is sufficient for real-time inference
- Quality strengths:
  - practical, multilingual, simple API
  - fixed speakers and accents are useful for repeatable tests
- Quality weaknesses:
  - less frontier and less exciting than Kokoro, Chatterbox, or OuteTTS
  - voice identity is less flexible than cloning models
- Speed / latency:
  - official docs explicitly state CPU is sufficient for real-time inference
- Multilingual support:
  - English, Spanish, French, Chinese, Japanese, Korean
- Voice cloning / speaker conditioning:
  - no official zero-shot cloning path in the base docs
- Ease of local scripting / CLI integration:
  - very good; clear CLI and Python examples
- Agent fit:
  - good
- Robotics fit:
  - good
- Notes:
  - good backup baseline if Piper or Kokoro prove awkward for a specific language case
- Official links:
  - Repo: [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS)
  - Install / CLI docs: [docs/install.md](https://github.com/myshell-ai/MeloTTS/blob/main/docs/install.md)
  - Hugging Face org: [myshell-ai](https://huggingface.co/myshell-ai)

### 5. XTTS-v2

- Model / runtime:
  - Coqui XTTS-v2 multilingual voice-cloning model
- License:
  - Coqui Public Model License (not Apache/MIT)
- Runs locally on macOS / Apple Silicon:
  - Yes locally via the Coqui TTS stack
  - Apple Silicon acceleration is inferred rather than explicitly documented in the model card
- Runtime / backend:
  - `TTS` Python package
  - Python API and `tts` CLI
- Approximate model size / RAM:
  - `model.pth` is about 1.87 GB, plus support files
  - expect a meaningfully heavier runtime than Piper or Kokoro
- Quality strengths:
  - still one of the clearest multilingual cloning baselines
  - cross-language voice cloning from a short reference clip
- Quality weaknesses:
  - older stack than the newest frontier models
  - extra operational complexity
- Speed / latency:
  - official Coqui repo news claims XTTS can stream with under 200 ms latency
  - this claim is not an Apple Silicon-specific local result
- Multilingual support:
  - 17 languages including English and French
- Voice cloning / speaker conditioning:
  - yes; official card says a 6-second reference clip is enough
- Ease of local scripting / CLI integration:
  - very good; strong Python and CLI path
- Agent fit:
  - medium to high if voice identity matters
- Robotics fit:
  - medium; capable, but heavier and more operationally involved
- Notes:
  - important benchmark reference if cloning is part of the roadmap
- Official links:
  - Model card: [coqui/XTTS-v2](https://huggingface.co/coqui/XTTS-v2)
  - Repo: [coqui-ai/TTS](https://github.com/coqui-ai/TTS)
  - Docs: [XTTS docs](https://tts.readthedocs.io/en/latest/models/xtts.html)
  - Demo: [coqui/xtts Space](https://huggingface.co/spaces/coqui/xtts)

### 6. Chatterbox family (Turbo / Multilingual / original)

- Model / runtime:
  - Resemble AI Chatterbox family
  - current family includes Turbo (350M), Multilingual (500M), and original English model
- License:
  - MIT
- Runs locally on macOS / Apple Silicon:
  - Probably yes, but Apple Silicon support is inferred rather than explicitly documented
  - official examples use CUDA devices
- Runtime / backend:
  - `chatterbox-tts` Python package
  - Python-first API
- Approximate model size / RAM:
  - Turbo repo footprint is large despite the 350M headline parameter count
  - observed Turbo weight files are roughly:
    - `t3_turbo_v1.safetensors`: about 1.92 GB
    - `s3gen.safetensors`: about 1.06 GB
    - `s3gen_meanflow.safetensors`: about 1.06 GB
  - practical download footprint is therefore multiple gigabytes
- Quality strengths:
  - very recent
  - explicit voice-agent positioning
  - zero-shot cloning
  - paralinguistic tags like `[laugh]` and `[cough]`
  - multilingual variant includes French
- Quality weaknesses:
  - less mature Mac-specific operational story
  - heavier environment than Piper/Kokoro
- Speed / latency:
  - Turbo is explicitly positioned as lower-compute / lower-VRAM than earlier family members
  - official open-source docs do not provide Apple Silicon local numbers
- Multilingual support:
  - Turbo is English
  - Multilingual supports 23+ languages including French
- Voice cloning / speaker conditioning:
  - yes
- Ease of local scripting / CLI integration:
  - medium; Python package is straightforward, but there is no first-class simple CLI in the official docs
- Agent fit:
  - high
- Robotics fit:
  - medium to high if expressiveness matters, but I would want real local soak testing first
- Notes:
  - this is one of the most interesting "new hotness" families in the set
- Official links:
  - Repo: [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)
  - Turbo model card: [ResembleAI/chatterbox-turbo](https://huggingface.co/ResembleAI/chatterbox-turbo)
  - Turbo demo: [HF Space](https://huggingface.co/spaces/ResembleAI/chatterbox-turbo-demo)
  - Turbo sample page: [demo page](https://resemble-ai.github.io/chatterbox_turbo_demopage/)
  - Multilingual demo: [HF Space](https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS)

### 7. OuteTTS 1.0

- Model / runtime:
  - OuteTTS 1.0, especially the 0.6B checkpoint for first Mac tests
- License:
  - Apache-2.0
- Runs locally on macOS / Apple Silicon:
  - Yes, documented
- Runtime / backend:
  - official `outetts` package
  - llama.cpp Python bindings
  - llama.cpp server
  - Transformers
  - explicit Apple Silicon / Metal install path
  - external MLX-Audio support is also listed
- Approximate model size / RAM:
  - `OuteTTS-1.0-0.6B` model file is about 1.20 GB
  - `Llama-OuteTTS-1.0-1B` is larger and should be a second-step experiment
- Quality strengths:
  - modern, interesting architecture
  - multilingual support including French
  - strong local-backend flexibility
  - speaker profiles / cloning path
- Quality weaknesses:
  - strongly dependent on speaker reference quality
  - official docs warn that sampling configuration matters a lot
  - current default testing voice story is still sparse
- Speed / latency:
  - official published benchmarks are on NVIDIA L40S, not Mac
  - expect slower and more tuning-sensitive behavior than Piper/Kokoro
- Multilingual support:
  - 14 trained languages for the 0.6B model including English and French
  - 1B model claims 23+ languages
- Voice cloning / speaker conditioning:
  - yes
- Ease of local scripting / CLI integration:
  - good Python path, plus strong server/backend flexibility
- Agent fit:
  - medium to high as an experimental path
- Robotics fit:
  - medium; interesting, but not yet the safest foundation
- Notes:
  - the explicit Metal path makes this a particularly good Apple Silicon frontier candidate
- Official links:
  - Repo: [edwko/OuteTTS](https://github.com/edwko/OuteTTS)
  - Model card: [OuteAI/OuteTTS-1.0-0.6B](https://huggingface.co/OuteAI/OuteTTS-1.0-0.6B)
  - Oute model org: [OuteAI on Hugging Face](https://huggingface.co/OuteAI)
  - Docs: [interface usage guide](https://github.com/edwko/OuteTTS/blob/main/docs/interface_usage.md)

### 8. Qwen3-TTS

- Model / runtime:
  - Qwen3-TTS family
  - for the new priorities, `Qwen3-TTS-12Hz-0.6B-CustomVoice` is the most attractive first Qwen variant
  - `Qwen3-TTS-12Hz-1.7B-VoiceDesign` is the most interesting bigger follow-up if the smaller test looks promising
- License:
  - Apache-2.0
- Runs locally on macOS / Apple Silicon:
  - Local use is clearly supported
  - Apple Silicon support is inferred rather than explicitly documented
  - official examples and optimization guidance are CUDA / FlashAttention 2 first
- Runtime / backend:
  - `qwen-tts` Python package
  - Transformers-based Python API
  - official local web UI demo
  - vLLM-Omni support is also called out
- Approximate model size / RAM:
  - `Qwen3-TTS-12Hz-0.6B-Base` model file is about 1.83 GB
  - `Qwen3-TTS-12Hz-1.7B-Base` model file is about 3.86 GB
  - actual repo storage is larger because the speech tokenizer assets are separate
- Quality strengths:
  - very strong paper-level feature set
  - multilingual, including English and French
  - 3-second rapid voice cloning
  - instruction-driven voice control on the higher-end variants
  - explicit streaming capability in the model family
- Quality weaknesses:
  - operational story is more GPU-centric than Mac-centric
  - likely heavier and more finicky on Apple Silicon than Piper, Kokoro, or even OuteTTS
  - if we do not need cloning or instruction control, it is probably overkill for phase 1
- Speed / latency:
  - official README emphasizes extreme low-latency streaming and cites latency as low as 97 ms
  - this is a family capability claim, not an Apple Silicon local benchmark
- Multilingual support:
  - 10 major languages including English and French
- Voice cloning / speaker conditioning:
  - yes; base models support 3-second rapid voice clone
  - custom-voice and voice-design variants add stronger control features
- Ease of local scripting / CLI integration:
  - medium to good
  - Python API is real, but the simplest happy path is less lightweight than Piper or Kokoro
- Agent fit:
  - high if we care about cloning, instruction control, or future streaming
- Robotics fit:
  - medium to high for research
  - medium for first deployment because the local Mac path is not as boring-and-reliable yet
- Notes:
  - if we specifically want the most modern open multilingual cloning family, this is one of the top contenders
  - for this repo, I would now test a CustomVoice model before the Base cloning model
  - if quality matters more than convenience and the Mac can tolerate it, the 1.7B VoiceDesign variant is worth serious consideration
  - the third-party project [andimarafioti/faster-qwen3-tts](https://github.com/andimarafioti/faster-qwen3-tts) is worth knowing about, but it is explicitly a CUDA-graph acceleration layer that requires an NVIDIA GPU with CUDA, so it is not a practical Apple Silicon path for this repo
- Official links:
  - Repo: [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
  - Hugging Face collection: [Qwen3-TTS collection](https://huggingface.co/collections/Qwen/qwen3-tts-688a697f81f2d8010430c328)
  - 0.6B base model: [Qwen/Qwen3-TTS-12Hz-0.6B-Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base)
  - 1.7B base model: [Qwen/Qwen3-TTS-12Hz-1.7B-Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base)
  - Technical report: [arXiv 2601.15621](https://arxiv.org/abs/2601.15621)
  - Blog: [Qwen3-TTS blog](https://qwen.ai/blog?id=qwen3tts-0115)

### 9. F5-TTS

- Model / runtime:
  - F5-TTS v1 base
- License:
  - code is MIT
  - pretrained weights are CC-BY-NC
- Runs locally on macOS / Apple Silicon:
  - Yes, documented in the install section
- Runtime / backend:
  - `f5-tts` Python package
  - official CLI and Gradio app
- Approximate model size / RAM:
  - `F5TTS_v1_Base/model_1250000.safetensors` is about 1.35 GB
  - expect a fairly heavy runtime compared with Kokoro/Piper
- Quality strengths:
  - important frontier reference
  - strong excitement around cloning and fidelity
  - official CLI is a plus
- Quality weaknesses:
  - weights are non-commercial
  - English/French is not its cleanest official story
  - more research-like than deployment-boring
- Speed / latency:
  - official benchmark table is on an L20 GPU
  - no Apple Silicon numbers in the official docs I reviewed
- Multilingual support:
  - official top-level story is strongest for English and Chinese
  - I would not make it a first-wave French benchmark
- Voice cloning / speaker conditioning:
  - yes
- Ease of local scripting / CLI integration:
  - good; official CLI exists
- Agent fit:
  - medium
- Robotics fit:
  - medium for research, lower for maintainable baseline deployment
- Notes:
  - worth testing later if we decide that cloning quality beats operational simplicity
- Official links:
  - Repo: [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)
  - Model card: [SWivid/F5-TTS](https://huggingface.co/SWivid/F5-TTS)
  - Paper: [arXiv 2410.06885](https://arxiv.org/abs/2410.06885)
  - Demo page: [F5-TTS demo](https://swivid.github.io/F5-TTS/)

### Watchlist: Parler-TTS Mini

- Why it is interesting:
  - fully open Apache stack
  - official inference docs explicitly mention `mps` for Mac
  - Apple Silicon users are called out in the repo install section
- Why it is not in the first wave:
  - English-only
  - 880M parameters and about 3.51 GB weights for the mini checkpoint
  - speaker style prompting is interesting, but it does not solve the French requirement
- Official links:
  - Repo: [huggingface/parler-tts](https://github.com/huggingface/parler-tts)
  - Model card: [parler-tts-mini-v1](https://huggingface.co/parler-tts/parler-tts-mini-v1)
  - Inference guide: [INFERENCE.md](https://github.com/huggingface/parler-tts/blob/main/INFERENCE.md)
  - Paper: [arXiv 2402.01912](https://arxiv.org/abs/2402.01912)

## Which models I would benchmark first

### First-wave benchmark order

1. macOS `say`
2. Kokoro-82M
3. MeloTTS
4. Qwen3-TTS
5. Piper

### Why this order

- `say` gives us the built-in control for cold-start behavior and CLI ergonomics.
- Kokoro is now the best immediate quality fit.
- MeloTTS gives us a straightforward EN/FR comparison with fixed voices.
- Qwen3-TTS is the first larger-quality experiment worth trying once the basic path is stable.
- Piper is no longer the star, but it is still useful as a reliability reference.

### Second-wave candidates

- Chatterbox Multilingual
- Qwen3-TTS 1.7B VoiceDesign
- OuteTTS 1.0
- XTTS-v2
- F5-TTS
- Parler-TTS Mini

## Recommendation summary

If the goal is to ship a usable local system quickly:

- start with Kokoro
- keep MeloTTS as the first practical EN/FR comparison
- keep macOS `say` as the fallback backend

If the goal is to probe the frontier:

- add Qwen3-TTS next
- only go to the larger Qwen variant if the smaller one is promising on this Mac

If the goal shifts toward expressive voice-agent behavior:

- move Chatterbox Multilingual up into the first wave

## Sources used

### Apple local sources

- `man say` on this machine
- `say -v ?` on this machine

### Official repos and model cards

- [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)
- [Piper CLI docs](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md)
- [Piper Python API docs](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md)
- [Piper voices](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md)
- [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/main)
- [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- [hexgrad/kokoro](https://github.com/hexgrad/kokoro)
- [Kokoro VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
- [coqui/XTTS-v2](https://huggingface.co/coqui/XTTS-v2)
- [coqui-ai/TTS](https://github.com/coqui-ai/TTS)
- [XTTS docs](https://tts.readthedocs.io/en/latest/models/xtts.html)
- [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)
- [ResembleAI/chatterbox-turbo](https://huggingface.co/ResembleAI/chatterbox-turbo)
- [edwko/OuteTTS](https://github.com/edwko/OuteTTS)
- [OuteAI/OuteTTS-1.0-0.6B](https://huggingface.co/OuteAI/OuteTTS-1.0-0.6B)
- [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS)
- [MeloTTS install docs](https://github.com/myshell-ai/MeloTTS/blob/main/docs/install.md)
- [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)
- [SWivid/F5-TTS model card](https://huggingface.co/SWivid/F5-TTS)
- [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
- [Qwen3-TTS collection](https://huggingface.co/collections/Qwen/qwen3-tts-688a697f81f2d8010430c328)
- [Qwen/Qwen3-TTS-12Hz-0.6B-Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base)
- [Qwen/Qwen3-TTS-12Hz-1.7B-Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base)
- [huggingface/parler-tts](https://github.com/huggingface/parler-tts)
- [parler-tts/parler-tts-mini-v1](https://huggingface.co/parler-tts/parler-tts-mini-v1)

### Papers

- [Natural language guidance of high-fidelity text-to-speech with synthetic annotations](https://arxiv.org/abs/2402.01912)
- [F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching](https://arxiv.org/abs/2410.06885)
- [Qwen3-TTS Technical Report](https://arxiv.org/abs/2601.15621)
- [StyleTTS 2](https://arxiv.org/abs/2306.07691)

## Confidence notes

- High confidence:
  - Piper, Kokoro, XTTS-v2, MeloTTS, Parler-TTS source-backed facts
- Medium confidence:
  - Apple Silicon practical behavior for XTTS-v2 and Chatterbox
  - Apple Silicon practical behavior for Qwen3-TTS
  - exact warm-path latency expectations for OuteTTS and Chatterbox on a Mac
- Low confidence until we benchmark locally:
  - whether Chatterbox Multilingual beats OuteTTS for this exact machine and workflow
  - whether XTTS-v2 is worth its runtime overhead if we do not actually need cloning

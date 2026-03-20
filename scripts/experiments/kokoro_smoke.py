from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local Kokoro synthesis smoke test.")
    parser.add_argument("--lang-code", required=True, help="Kokoro language code, e.g. a for US English, f for French.")
    parser.add_argument("--voice", required=True, help="Kokoro voice id, e.g. af_heart or ff_siwis.")
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument("--output", required=True, type=Path, help="WAV output path.")
    parser.add_argument("--speed", type=float, default=1.0, help="Kokoro speech speed.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    print(f"torch={torch.__version__}")
    print(f"mps_available={torch.backends.mps.is_available()}")
    print(f"mps_built={torch.backends.mps.is_built()}")
    print(f"pytorch_enable_mps_fallback={os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK', 'unset')}")

    start = time.perf_counter()
    pipeline = KPipeline(lang_code=args.lang_code)
    chunks: list[np.ndarray] = []

    for _, _, audio in pipeline(args.text, voice=args.voice, speed=args.speed):
        chunks.append(np.asarray(audio))

    if not chunks:
        raise RuntimeError("Kokoro returned no audio chunks.")

    audio = np.concatenate(chunks)
    sf.write(args.output, audio, 24000)

    elapsed = time.perf_counter() - start
    print(f"output={args.output}")
    print(f"samples={audio.shape[0]}")
    print(f"seconds={audio.shape[0] / 24000:.2f}")
    print(f"elapsed_seconds={elapsed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

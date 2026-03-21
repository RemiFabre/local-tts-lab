from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from local_tts_lab.kokoro_service import ensure_service_running, list_available_voices, send_request
from local_tts_lab.paths import OUTPUTS_DIR, ensure_runtime_dirs
from local_tts_lab.presets import SAMPLE_TEXTS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate one Kokoro sample per available voice.")
    parser.add_argument("--lang", required=True, choices=["en", "fr"])
    parser.add_argument("--text", help="Optional override sentence.")
    parser.add_argument("--output-dir", type=Path, help="Optional destination directory.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ensure_runtime_dirs()
    ensure_service_running()

    text = args.text or SAMPLE_TEXTS[args.lang]
    voices = list_available_voices(args.lang)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    root = args.output_dir or OUTPUTS_DIR / "kokoro-voice-sweeps" / timestamp / args.lang
    root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for voice in voices:
        output_path = root / f"{voice}.wav"
        result = send_request(
            {
                "action": "synthesize",
                "lang": args.lang,
                "voice": voice,
                "speed": 1.0,
                "text": text,
                "output": str(output_path),
            }
        )
        rows.append(
            {
                "lang": args.lang,
                "voice": voice,
                "elapsed_seconds": str(result["elapsed_seconds"]),
                "audio_seconds": str(result["audio_seconds"]),
                "output": str(output_path),
            }
        )
        print(f"{voice} elapsed={result['elapsed_seconds']}s output={output_path}")

    summary_path = root / "summary.tsv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["lang", "voice", "elapsed_seconds", "audio_seconds", "output"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"voice_count={len(voices)}")
    print(f"summary_tsv={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

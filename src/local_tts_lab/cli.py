from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-tts",
        description="Simple local TTS entrypoint for Apple Silicon experiments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local baseline availability.")
    doctor.set_defaults(func=run_doctor)

    list_voices = subparsers.add_parser(
        "list-voices",
        help="List voices exposed by the macOS `say` command.",
    )
    list_voices.set_defaults(func=run_list_voices)

    speak = subparsers.add_parser(
        "speak",
        help="Speak text locally with the built-in macOS `say` engine.",
    )
    speak.add_argument("text", help="Text to synthesize.")
    speak.add_argument("--voice", help="Voice name to pass to `say -v`.")
    speak.add_argument(
        "--rate",
        type=int,
        help="Speech rate in words per minute.",
    )
    speak.add_argument(
        "--output",
        type=Path,
        help="Optional output file path. Extension controls the container when supported by `say`.",
    )
    speak.add_argument(
        "--engine",
        default="macos-say",
        choices=["macos-say"],
        help="Speech backend. Only the built-in baseline is wired up in the first pass.",
    )
    speak.set_defaults(func=run_speak)

    return parser


def ensure_macos_say() -> str:
    if platform.system() != "Darwin":
        raise SystemExit("This baseline CLI currently expects macOS because it shells out to `say`.")

    say_bin = shutil.which("say")
    if not say_bin:
        raise SystemExit("The `say` command was not found on PATH.")

    return say_bin


def run_doctor(_: argparse.Namespace) -> int:
    say_bin = shutil.which("say")
    print(f"platform={platform.system()} {platform.machine()}")
    print(f"python={sys.version.split()[0]}")
    print(f"say={'found' if say_bin else 'missing'}")
    if say_bin:
        print(f"say_path={say_bin}")
    print(f"pytorch_enable_mps_fallback={os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK', 'unset')}")
    return 0 if say_bin else 1


def run_list_voices(_: argparse.Namespace) -> int:
    say_bin = ensure_macos_say()
    result = subprocess.run(
        [say_bin, "-v", "?"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    sys.stdout.write(result.stdout)
    return 0


def run_speak(args: argparse.Namespace) -> int:
    say_bin = ensure_macos_say()
    command = [say_bin]

    if args.voice:
        command.extend(["-v", args.voice])

    if args.rate:
        command.extend(["-r", str(args.rate)])

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        command.extend(["-o", str(args.output)])

    command.append(args.text)

    result = subprocess.run(command, check=False)
    return result.returncode


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import os
import platform
import shutil
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

from local_tts_lab.backends import (
    backend_available,
    describe_result,
    install_piper_voices,
    list_backends,
    synthesize,
    warm_import_note,
)
from local_tts_lab.kokoro_service import daemon_main as kokoro_daemon_main
from local_tts_lab.kokoro_service import kokoro_say_main as kokoro_say_main
from local_tts_lab.paths import COMPARE_DIR, OUTPUTS_DIR, ensure_runtime_dirs, latest_compare_root
from local_tts_lab.presets import DEFAULT_VOICES, SAMPLE_TEXTS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-tts",
        description="Local TTS lab entrypoint for Apple Silicon experiments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local baseline availability.")
    doctor.set_defaults(func=run_doctor)

    backends = subparsers.add_parser("backends", help="List supported backends and availability.")
    backends.set_defaults(func=run_backends)

    list_voices = subparsers.add_parser(
        "list-voices",
        help="List voices exposed by the macOS `say` command.",
    )
    list_voices.set_defaults(func=run_list_voices)

    speak = subparsers.add_parser(
        "speak",
        help="Synthesize speech with one local backend.",
    )
    speak.add_argument("text", help="Text to synthesize.")
    speak.add_argument("--backend", default="macos-say", choices=list_backends(), help="Speech backend.")
    speak.add_argument("--lang", default="en", choices=["en", "fr"], help="Language preset.")
    speak.add_argument("--voice", help="Backend-specific voice override.")
    speak.add_argument(
        "--rate",
        type=int,
        help="Speech rate in words per minute for macOS say only.",
    )
    speak.add_argument(
        "--output",
        type=Path,
        help="Optional output file path. Extension controls the container when supported by `say`.",
    )
    speak.set_defaults(func=run_speak)

    compare = subparsers.add_parser(
        "compare",
        help="Generate the preset sample for several backends and print quick timings.",
    )
    compare.add_argument("--lang", default="en", choices=["en", "fr"], help="Language preset.")
    compare.add_argument(
        "--backends",
        nargs="*",
        choices=list_backends(),
        default=["macos-say", "kokoro", "melo", "piper"],
        help="Backends to compare.",
    )
    compare.set_defaults(func=run_compare)

    compare_suite = subparsers.add_parser(
        "compare-suite",
        help="Run the preset compare flow for English and French in one timestamped directory.",
    )
    compare_suite.add_argument(
        "--langs",
        nargs="*",
        choices=["en", "fr"],
        default=["en", "fr"],
        help="Languages to benchmark.",
    )
    compare_suite.add_argument(
        "--backends",
        nargs="*",
        choices=list_backends(),
        default=["macos-say", "kokoro", "melo", "piper"],
        help="Backends to compare.",
    )
    compare_suite.set_defaults(func=run_compare_suite)

    install = subparsers.add_parser("install", help="Install helper assets for one backend.")
    install.add_argument("target", choices=["piper-voices"], help="Install target.")
    install.set_defaults(func=run_install)

    kokoro_daemon = subparsers.add_parser(
        "kokoro-daemon",
        help="Manage the warm Kokoro daemon used by kokoro-say.",
    )
    kokoro_daemon.add_argument("daemon_args", nargs=argparse.REMAINDER)
    kokoro_daemon.set_defaults(func=run_kokoro_daemon)

    kokoro_say = subparsers.add_parser(
        "kokoro-say",
        help="Speak text through the warm Kokoro daemon.",
    )
    kokoro_say.add_argument("say_args", nargs=argparse.REMAINDER)
    kokoro_say.set_defaults(func=run_kokoro_say)

    play_compare = subparsers.add_parser(
        "play-compare",
        help="Play generated clips from the latest compare run.",
    )
    play_compare.add_argument("--lang", default="en", choices=["en", "fr"], help="Language directory to play.")
    play_compare.add_argument(
        "--backends",
        nargs="*",
        choices=list_backends(),
        help="Optional subset of backends to play in order.",
    )
    play_compare.add_argument(
        "--dir",
        type=Path,
        help="Optional compare root or language directory. Defaults to the latest compare run.",
    )
    play_compare.add_argument("--pause", type=float, default=0.35, help="Pause between clips in seconds.")
    play_compare.set_defaults(func=run_play_compare)

    return parser


def ensure_macos_say() -> str:
    if platform.system() != "Darwin":
        raise SystemExit("This baseline CLI currently expects macOS because it shells out to `say`.")

    say_bin = shutil.which("say")
    if not say_bin:
        raise SystemExit("The `say` command was not found on PATH.")

    return say_bin


def run_doctor(_: argparse.Namespace) -> int:
    ensure_runtime_dirs()
    say_bin = shutil.which("say")
    print(f"platform={platform.system()} {platform.machine()}")
    print(f"python={sys.version.split()[0]}")
    print(f"say={'found' if say_bin else 'missing'}")
    if say_bin:
        print(f"say_path={say_bin}")
    print(f"pytorch_enable_mps_fallback={os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK', 'unset')}")
    for backend in list_backends():
        available, note = backend_available(backend)
        print(f"{backend}={'ok' if available else 'unavailable'} note={note}")
    return 0 if say_bin else 1


def run_backends(_: argparse.Namespace) -> int:
    for backend in list_backends():
        available, note = backend_available(backend)
        voices = DEFAULT_VOICES.get(backend, {})
        print(f"{backend:<10} available={available} note={note} defaults={voices}")
    print(warm_import_note())
    return 0


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
    ensure_runtime_dirs()
    if args.backend == "macos-say":
        say_bin = ensure_macos_say()
        command = [say_bin]
        if args.voice:
            command.extend(["-v", args.voice])
        elif args.lang in DEFAULT_VOICES["macos-say"]:
            command.extend(["-v", DEFAULT_VOICES["macos-say"][args.lang]])
        if args.rate:
            command.extend(["-r", str(args.rate)])
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            command.extend(["-o", str(args.output)])
        command.append(args.text)
        result = subprocess.run(command, check=False)
        return result.returncode

    output = args.output or OUTPUTS_DIR / f"{args.backend}-{args.lang}-manual.wav"
    result = synthesize(args.backend, args.lang, args.text, output, args.voice)
    print(describe_result(result))
    return 0


def run_compare(args: argparse.Namespace) -> int:
    compare_root = COMPARE_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    failures, _ = run_compare_matrix([args.lang], args.backends, compare_root)
    print(f"compare_dir={compare_root / args.lang}")
    return 0 if failures == 0 else 1


def run_compare_suite(args: argparse.Namespace) -> int:
    compare_root = COMPARE_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    failures, _ = run_compare_matrix(args.langs, args.backends, compare_root)
    print(f"compare_root={compare_root}")
    return 0 if failures == 0 else 1


def run_install(args: argparse.Namespace) -> int:
    if args.target == "piper-voices":
        for voice_name in install_piper_voices():
            print(f"downloaded={voice_name}")
        return 0
    return 1


def run_kokoro_daemon(args: argparse.Namespace) -> int:
    daemon_args = args.daemon_args or ["status"]
    return kokoro_daemon_main(daemon_args)


def run_kokoro_say(args: argparse.Namespace) -> int:
    say_args = args.say_args
    if say_args and say_args[0] == "--":
        say_args = say_args[1:]
    return kokoro_say_main(say_args)


def run_play_compare(args: argparse.Namespace) -> int:
    ensure_runtime_dirs()
    if platform.system() != "Darwin":
        raise SystemExit("Playback currently expects macOS because it shells out to `afplay`.")

    root = args.dir or latest_compare_root()
    if root is None:
        raise SystemExit(f"No compare runs found under {COMPARE_DIR}")
    lang_dir = root if root.name in {"en", "fr"} else root / args.lang
    if not lang_dir.exists():
        raise SystemExit(f"Missing compare directory: {lang_dir}")

    backends = args.backends or list_backends()
    played = 0
    for backend in backends:
        suffix = ".aiff" if backend == "macos-say" else ".wav"
        candidate = lang_dir / f"{backend}-{args.lang}{suffix}"
        if not candidate.exists():
            print(f"{backend:<10} skipped: missing {candidate.name}")
            continue
        print(f"playing={backend} file={candidate}")
        result = subprocess.run(["afplay", str(candidate)], check=False)
        if result.returncode != 0:
            return result.returncode
        played += 1
        if args.pause > 0:
            time.sleep(args.pause)
    return 0 if played > 0 else 1


def run_compare_matrix(langs: list[str], backends: list[str], compare_root: Path) -> tuple[int, Path]:
    ensure_runtime_dirs()
    compare_root.mkdir(parents=True, exist_ok=True)
    summary_path = compare_root / "summary.tsv"
    rows: list[dict[str, str]] = []
    failures = 0

    print(warm_import_note())
    for lang in langs:
        compare_dir = compare_root / lang
        compare_dir.mkdir(parents=True, exist_ok=True)
        text = SAMPLE_TEXTS[lang]
        print(f"lang={lang} text={text}")
        for backend in backends:
            available, note = backend_available(backend)
            if not available:
                print(f"{backend:<10} skipped: {note}")
                failures += 1
                rows.append(
                    {
                        "lang": lang,
                        "backend": backend,
                        "voice": "",
                        "elapsed_seconds": "",
                        "audio_seconds": "",
                        "status": f"skipped: {note}",
                        "output": "",
                    }
                )
                continue

            suffix = ".aiff" if backend == "macos-say" else ".wav"
            output = compare_dir / f"{backend}-{lang}{suffix}"
            try:
                result = synthesize(backend, lang, text, output)
                print(describe_result(result))
                rows.append(
                    {
                        "lang": lang,
                        "backend": backend,
                        "voice": result.voice,
                        "elapsed_seconds": f"{result.elapsed_seconds:.2f}",
                        "audio_seconds": "" if result.audio_seconds is None else f"{result.audio_seconds:.2f}",
                        "status": "ok",
                        "output": str(result.output_path),
                    }
                )
            except Exception as exc:
                print(f"{backend:<10} failed: {exc}")
                failures += 1
                rows.append(
                    {
                        "lang": lang,
                        "backend": backend,
                        "voice": "",
                        "elapsed_seconds": "",
                        "audio_seconds": "",
                        "status": f"failed: {exc}",
                        "output": str(output),
                    }
                )

    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["lang", "backend", "voice", "elapsed_seconds", "audio_seconds", "status", "output"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"summary_tsv={summary_path}")
    return failures, compare_root


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

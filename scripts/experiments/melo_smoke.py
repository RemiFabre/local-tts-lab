from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import nltk
import torch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a MeloTTS synthesis smoke test.")
    parser.add_argument("--language", required=True, choices=["EN", "FR"])
    parser.add_argument("--speaker", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps"])
    parser.add_argument("--check-only", action="store_true", help="Prepare dependencies and validate import only.")
    return parser


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_nltk_data() -> None:
    download_dir = repo_root() / "runtime" / "cache" / "nltk_data"
    download_dir.mkdir(parents=True, exist_ok=True)
    os.environ["NLTK_DATA"] = str(download_dir)
    if str(download_dir) not in nltk.data.path:
        nltk.data.path.insert(0, str(download_dir))

    resources = [
        ("taggers/averaged_perceptron_tagger_eng", "averaged_perceptron_tagger_eng"),
        ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
        ("corpora/cmudict", "cmudict"),
    ]
    for resource_path, download_name in resources:
        try:
            nltk.data.find(resource_path, paths=[str(download_dir)])
        except LookupError:
            nltk.download(download_name, download_dir=str(download_dir), quiet=True)


def ensure_unidic_layout() -> None:
    import unidic

    package_dir = Path(unidic.__file__).resolve().parent
    actual_dict_dir = package_dir / "unidic"
    if not (actual_dict_dir / "sys.dic").exists():
        subprocess.run([sys.executable, "-m", "unidic", "download"], check=True)
    if not (actual_dict_dir / "sys.dic").exists():
        raise RuntimeError(f"UniDic download did not produce {actual_dict_dir / 'sys.dic'}")

    mecabrc = actual_dict_dir / "mecabrc"
    mecabrc.write_text(f"dicdir = {actual_dict_dir}\n", encoding="utf-8")
    os.environ["MECABRC"] = str(mecabrc)

    dicdir = package_dir / "dicdir"
    if dicdir.exists() or dicdir.is_symlink():
        if dicdir.is_symlink() and dicdir.resolve() == actual_dict_dir:
            return
        if dicdir.is_symlink() or dicdir.is_file():
            dicdir.unlink()
        else:
            for child in dicdir.iterdir():
                if child.is_dir() and not child.is_symlink():
                    raise RuntimeError(f"Unexpected directory inside {dicdir}: {child}")
                child.unlink()
            dicdir.rmdir()
    dicdir.symlink_to(actual_dict_dir, target_is_directory=True)


def choose_device(requested: str) -> str:
    if requested == "cpu":
        return "cpu"
    if requested == "mps":
        return "mps"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def main() -> int:
    args = build_parser().parse_args()
    ensure_nltk_data()
    ensure_unidic_layout()

    from melo.api import TTS

    if args.check_only:
        print("melo_ready=true")
        return 0

    device = choose_device(args.device)
    if device == "mps":
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    start = time.perf_counter()
    model = TTS(language=args.language, device=device)
    speaker_ids = model.hps.data.spk2id
    model.tts_to_file(args.text, speaker_ids[args.speaker], args.output, speed=1.0)
    elapsed = time.perf_counter() - start
    print(f"device={device}")
    print(f"elapsed_seconds={elapsed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

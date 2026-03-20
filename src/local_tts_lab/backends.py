from __future__ import annotations

import contextlib
import io
import os
import platform
import subprocess
import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path

from local_tts_lab.paths import MODELS_DIR, REPO_ROOT, ensure_runtime_dirs
from local_tts_lab.presets import DEFAULT_VOICES


@dataclass
class SynthesisResult:
    backend: str
    language: str
    voice: str
    output_path: Path
    elapsed_seconds: float
    audio_seconds: float | None


def audio_duration_seconds(path: Path) -> float | None:
    suffix = path.suffix.lower()
    if suffix == ".wav":
        with contextlib.closing(wave.open(str(path), "rb")) as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            if rate:
                return frames / rate
    if suffix in {".aiff", ".aif"}:
        result = subprocess.run(
            ["afinfo", str(path)],
            check=False,
            text=True,
            capture_output=True,
        )
        for line in result.stdout.splitlines():
            if "estimated duration" in line.lower():
                try:
                    return float(line.split(":", 1)[1].strip().split()[0])
                except (IndexError, ValueError):
                    return None
    return None


def list_backends() -> list[str]:
    return ["macos-say", "kokoro", "melo", "piper"]


def backend_available(name: str) -> tuple[bool, str]:
    try:
        if name == "macos-say":
            if platform.system() != "Darwin":
                return False, "requires macOS"
            result = subprocess.run(["which", "say"], check=False, capture_output=True, text=True)
            return result.returncode == 0, "ok" if result.returncode == 0 else "missing say"
        if name == "kokoro":
            import kokoro  # noqa: F401

            return True, "ok"
        if name == "melo":
            melo_python = REPO_ROOT / ".venv-melo" / "bin" / "python"
            if not melo_python.exists():
                return False, f"missing {melo_python}"
            result = subprocess.run(
                [str(melo_python), "-c", "import melo; print(melo.__file__)"],
                check=False,
                text=True,
                capture_output=True,
            )
            return result.returncode == 0, "ok" if result.returncode == 0 else (result.stderr or result.stdout).strip()
        if name == "piper":
            from piper import PiperVoice  # noqa: F401

            return True, "ok"
    except Exception as exc:  # pragma: no cover - availability probe
        return False, str(exc)
    return False, "unknown backend"


def synthesize(backend: str, language: str, text: str, output_path: Path, voice: str | None = None) -> SynthesisResult:
    ensure_runtime_dirs()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if backend == "macos-say":
        return _synthesize_macos_say(language, text, output_path, voice)
    if backend == "kokoro":
        return _synthesize_kokoro(language, text, output_path, voice)
    if backend == "melo":
        return _synthesize_melo(language, text, output_path, voice)
    if backend == "piper":
        return _synthesize_piper(language, text, output_path, voice)
    raise ValueError(f"Unsupported backend: {backend}")


def _synthesize_macos_say(language: str, text: str, output_path: Path, voice: str | None) -> SynthesisResult:
    chosen_voice = voice or DEFAULT_VOICES["macos-say"][language]
    start = time.perf_counter()
    subprocess.run(["say", "-v", chosen_voice, "-o", str(output_path), text], check=True)
    elapsed = time.perf_counter() - start
    return SynthesisResult("macos-say", language, chosen_voice, output_path, elapsed, audio_duration_seconds(output_path))


def _synthesize_kokoro(language: str, text: str, output_path: Path, voice: str | None) -> SynthesisResult:
    import soundfile as sf
    import numpy as np
    from kokoro import KPipeline

    lang_code = {"en": "a", "fr": "f"}[language]
    chosen_voice = voice or DEFAULT_VOICES["kokoro"][language]
    start = time.perf_counter()
    pipeline = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M")
    chunks: list[np.ndarray] = []
    for _, _, audio in pipeline(text, voice=chosen_voice, speed=1):
        chunks.append(np.asarray(audio))
    if not chunks:
        raise RuntimeError("Kokoro returned no audio.")
    audio = np.concatenate(chunks)
    sf.write(output_path, audio, 24000)
    elapsed = time.perf_counter() - start
    return SynthesisResult("kokoro", language, chosen_voice, output_path, elapsed, audio_duration_seconds(output_path))


def _synthesize_melo(language: str, text: str, output_path: Path, voice: str | None) -> SynthesisResult:
    melo_python = REPO_ROOT / ".venv-melo" / "bin" / "python"
    if not melo_python.exists():
        raise FileNotFoundError(f"Missing Melo environment at {melo_python}")

    lang_name = {"en": "EN", "fr": "FR"}[language]
    chosen_voice = voice or DEFAULT_VOICES["melo"][language]
    start = time.perf_counter()
    env = dict(os.environ)
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    result = subprocess.run(
        [
            str(melo_python),
            str(REPO_ROOT / "scripts" / "experiments" / "melo_smoke.py"),
            "--language",
            lang_name,
            "--speaker",
            chosen_voice,
            "--text",
            text,
            "--output",
            str(output_path),
        ],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    elapsed = time.perf_counter() - start
    return SynthesisResult("melo", language, chosen_voice, output_path, elapsed, audio_duration_seconds(output_path))


def _piper_voice_paths(voice_name: str) -> tuple[Path, Path]:
    data_dir = MODELS_DIR / "piper"
    model_path = data_dir / f"{voice_name}.onnx"
    config_path = data_dir / f"{voice_name}.onnx.json"
    if not model_path.exists() or not config_path.exists():
        raise FileNotFoundError(
            f"Missing Piper voice files for {voice_name}. Run the install helper to download them into {data_dir}."
        )
    return model_path, config_path


def _synthesize_piper(language: str, text: str, output_path: Path, voice: str | None) -> SynthesisResult:
    from piper import PiperVoice

    chosen_voice = voice or DEFAULT_VOICES["piper"][language]
    model_path, _ = _piper_voice_paths(chosen_voice)
    start = time.perf_counter()
    voice_model = PiperVoice.load(str(model_path))
    with wave.open(str(output_path), "wb") as wav_file:
        voice_model.synthesize_wav(text, wav_file)
    elapsed = time.perf_counter() - start
    return SynthesisResult("piper", language, chosen_voice, output_path, elapsed, audio_duration_seconds(output_path))


def install_piper_voices() -> list[str]:
    ensure_runtime_dirs()
    data_dir = MODELS_DIR / "piper"
    data_dir.mkdir(parents=True, exist_ok=True)
    downloads: list[str] = []
    for language in ("en", "fr"):
        voice_name = DEFAULT_VOICES["piper"][language]
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "piper.download_voices",
                "--data-dir",
                str(data_dir),
                voice_name,
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        downloads.append(voice_name)
    return downloads


def describe_result(result: SynthesisResult) -> str:
    audio_s = f"{result.audio_seconds:.2f}s" if result.audio_seconds is not None else "unknown"
    return (
        f"{result.backend:<10} lang={result.language} voice={result.voice} "
        f"elapsed={result.elapsed_seconds:.2f}s audio={audio_s} output={result.output_path}"
    )


def warm_import_note() -> str:
    buffer = io.StringIO()
    buffer.write("Python backends will include model load in their timing.\n")
    buffer.write("Repeat a command twice if you want an informal warm-path comparison.\n")
    return buffer.getvalue().strip()

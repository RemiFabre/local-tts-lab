from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = REPO_ROOT / "runtime"
CACHE_DIR = RUNTIME_DIR / "cache"
OUTPUTS_DIR = RUNTIME_DIR / "outputs"
MODELS_DIR = RUNTIME_DIR / "models"
COMPARE_DIR = OUTPUTS_DIR / "compare"
KOKORO_RUNTIME_DIR = CACHE_DIR / "kokoro-service"
KOKORO_SOCKET_PATH = KOKORO_RUNTIME_DIR / "kokoro.sock"
KOKORO_PID_PATH = KOKORO_RUNTIME_DIR / "kokoro.pid"
KOKORO_LOG_PATH = KOKORO_RUNTIME_DIR / "kokoro.log"
KOKORO_TEMP_OUTPUT_DIR = OUTPUTS_DIR / "kokoro-live"


def ensure_runtime_dirs() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    KOKORO_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    KOKORO_TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def latest_compare_root() -> Path | None:
    if not COMPARE_DIR.exists():
        return None
    candidates = sorted(
        (path for path in COMPARE_DIR.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    )
    return candidates[-1] if candidates else None

from __future__ import annotations

import argparse
import atexit
import json
import os
import resource
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from local_tts_lab.paths import (
    KOKORO_LOG_PATH,
    KOKORO_PID_PATH,
    KOKORO_SOCKET_PATH,
    KOKORO_TEMP_OUTPUT_DIR,
    OUTPUTS_DIR,
    ensure_runtime_dirs,
)
from local_tts_lab.presets import DEFAULT_VOICES


DEFAULT_REPO_ID = "hexgrad/Kokoro-82M"
DEFAULT_SPEED = 1.0
LANG_TO_CODE = {"en": "a", "fr": "f"}
LANG_VOICE_PREFIXES = {
    "en": ("af_", "am_", "bf_", "bm_"),
    "fr": ("ff_", "fm_"),
}


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)


def daemon_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def read_pid() -> int | None:
    try:
        return int(KOKORO_PID_PATH.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def stale_runtime_files() -> None:
    pid = read_pid()
    if pid is not None and daemon_alive(pid):
        return
    if KOKORO_SOCKET_PATH.exists():
        KOKORO_SOCKET_PATH.unlink()
    if KOKORO_PID_PATH.exists():
        KOKORO_PID_PATH.unlink()


def choose_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def repo_voice_ids() -> list[str]:
    from huggingface_hub import list_repo_files

    files = list_repo_files(DEFAULT_REPO_ID, repo_type="model")
    return sorted({path.split("/")[-1][:-3] for path in files if path.startswith("voices/") and path.endswith(".pt")})


def cached_voice_ids() -> list[str]:
    cache_root = Path.home() / ".cache" / "huggingface" / "hub" / "models--hexgrad--Kokoro-82M" / "snapshots"
    if not cache_root.exists():
        return []
    snapshots = sorted(path for path in cache_root.iterdir() if path.is_dir())
    if not snapshots:
        return []
    voice_dir = snapshots[-1] / "voices"
    if not voice_dir.exists():
        return []
    return sorted({path.stem for path in voice_dir.glob("*.pt")})


def list_available_voices(language: str | None = None) -> list[str]:
    try:
        voices = repo_voice_ids()
    except Exception:
        voices = cached_voice_ids()
    if language is None:
        return voices
    prefixes = LANG_VOICE_PREFIXES[language]
    return [voice for voice in voices if voice.startswith(prefixes)]


@dataclass
class KokoroSynthesisResult:
    language: str
    voice: str
    output_path: Path
    elapsed_seconds: float
    audio_seconds: float


class KokoroEngine:
    def __init__(self, repo_id: str = DEFAULT_REPO_ID):
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
        from kokoro.model import KModel

        self._np = np
        self._sf = sf
        self.repo_id = repo_id
        self.device = choose_device()
        self.loaded_at = time.time()
        self.requests_handled = 0

        self.model = KModel(repo_id=repo_id).to(self.device).eval()
        self.pipelines = {
            "en": KPipeline(lang_code=LANG_TO_CODE["en"], repo_id=repo_id, model=self.model),
            "fr": KPipeline(lang_code=LANG_TO_CODE["fr"], repo_id=repo_id, model=self.model),
        }
        for language, pipeline in self.pipelines.items():
            pipeline.load_voice(DEFAULT_VOICES["kokoro"][language])

    def synthesize(
        self,
        language: str,
        text: str,
        output_path: Path,
        voice: str | None = None,
        speed: float = DEFAULT_SPEED,
    ) -> KokoroSynthesisResult:
        pipeline = self.pipelines[language]
        chosen_voice = voice or DEFAULT_VOICES["kokoro"][language]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()
        chunks: list[self._np.ndarray] = []
        for _, _, audio in pipeline(text, voice=chosen_voice, speed=speed):
            chunks.append(self._np.asarray(audio))
        if not chunks:
            raise RuntimeError("Kokoro returned no audio.")
        audio = self._np.concatenate(chunks)
        self._sf.write(output_path, audio, 24000)
        elapsed = time.perf_counter() - start
        self.requests_handled += 1
        return KokoroSynthesisResult(
            language=language,
            voice=chosen_voice,
            output_path=output_path,
            elapsed_seconds=elapsed,
            audio_seconds=len(audio) / 24000,
        )

    def status(self) -> dict[str, object]:
        return {
            "pid": os.getpid(),
            "device": self.device,
            "repo_id": self.repo_id,
            "loaded_at_epoch": self.loaded_at,
            "uptime_seconds": round(time.time() - self.loaded_at, 2),
            "requests_handled": self.requests_handled,
            "rss_mb": round(rss_mb(), 1),
            "socket_path": str(KOKORO_SOCKET_PATH),
            "voices": {lang: DEFAULT_VOICES["kokoro"][lang] for lang in ("en", "fr")},
        }


class KokoroRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        raw = self.rfile.readline()
        if not raw:
            return
        try:
            request = json.loads(raw.decode("utf-8"))
            response = self.server.dispatch(request)
        except Exception as exc:  # pragma: no cover - defensive server response
            response = {"ok": False, "error": str(exc)}
        self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))
        self.wfile.flush()


class KokoroServer(socketserver.UnixStreamServer):
    def __init__(self, socket_path: str, handler: type[KokoroRequestHandler], engine: KokoroEngine):
        self.engine = engine
        super().__init__(socket_path, handler)

    def dispatch(self, request: dict[str, object]) -> dict[str, object]:
        action = request.get("action")
        if action == "ping":
            return {"ok": True, "result": self.engine.status()}
        if action == "status":
            return {"ok": True, "result": self.engine.status()}
        if action == "synthesize":
            text = str(request["text"]).strip()
            language = str(request.get("lang", "en"))
            voice = request.get("voice")
            speed = float(request.get("speed", DEFAULT_SPEED))
            output_path = Path(str(request["output"]))
            result = self.engine.synthesize(language, text, output_path, voice=voice, speed=speed)
            return {
                "ok": True,
                "result": {
                    "lang": result.language,
                    "voice": result.voice,
                    "output": str(result.output_path),
                    "elapsed_seconds": round(result.elapsed_seconds, 2),
                    "audio_seconds": round(result.audio_seconds, 2),
                    "rss_mb": round(rss_mb(), 1),
                },
            }
        if action == "shutdown":
            threading.Thread(target=self.shutdown, daemon=True).start()
            return {"ok": True, "result": {"message": "shutdown_requested"}}
        raise ValueError(f"Unsupported action: {action}")


def send_request(request: dict[str, object], timeout: float = 120.0) -> dict[str, object]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(str(KOKORO_SOCKET_PATH))
        client.sendall((json.dumps(request) + "\n").encode("utf-8"))
        data = b""
        while not data.endswith(b"\n"):
            chunk = client.recv(65536)
            if not chunk:
                break
            data += chunk
    if not data:
        raise RuntimeError("No response from Kokoro service.")
    response = json.loads(data.decode("utf-8"))
    if not response.get("ok"):
        raise RuntimeError(str(response.get("error", "unknown Kokoro service error")))
    return response["result"]


def wait_for_service(timeout: float = 30.0) -> dict[str, object]:
    deadline = time.time() + timeout
    last_error = "service did not start"
    while time.time() < deadline:
        try:
            return send_request({"action": "ping"}, timeout=2.0)
        except Exception as exc:  # pragma: no cover - startup loop
            last_error = str(exc)
            time.sleep(0.25)
    if KOKORO_LOG_PATH.exists():
        tail = KOKORO_LOG_PATH.read_text(encoding="utf-8")[-2000:]
        raise RuntimeError(f"{last_error}\n\nLast Kokoro daemon log:\n{tail}")
    raise RuntimeError(last_error)


def ensure_service_running() -> dict[str, object]:
    ensure_runtime_dirs()
    stale_runtime_files()
    try:
        return send_request({"action": "ping"}, timeout=2.0)
    except Exception:
        pass

    env = dict(os.environ)
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    with KOKORO_LOG_PATH.open("a", encoding="utf-8") as log_file:
        subprocess.Popen(
            [sys.executable, "-m", "local_tts_lab.kokoro_service", "serve"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            cwd=str(Path(__file__).resolve().parents[2]),
            env=env,
            start_new_session=True,
        )
    return wait_for_service()


def stop_service() -> dict[str, object]:
    result = send_request({"action": "shutdown"}, timeout=5.0)
    deadline = time.time() + 10.0
    while time.time() < deadline:
        pid = read_pid()
        if pid is None or not daemon_alive(pid):
            stale_runtime_files()
            return result
        time.sleep(0.1)
    return result


def serve_forever() -> int:
    ensure_runtime_dirs()
    stale_runtime_files()
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    engine = KokoroEngine()
    if KOKORO_SOCKET_PATH.exists():
        KOKORO_SOCKET_PATH.unlink()
    server = KokoroServer(str(KOKORO_SOCKET_PATH), KokoroRequestHandler, engine)
    KOKORO_PID_PATH.write_text(f"{os.getpid()}\n", encoding="utf-8")

    def cleanup() -> None:
        if KOKORO_SOCKET_PATH.exists():
            KOKORO_SOCKET_PATH.unlink()
        if KOKORO_PID_PATH.exists():
            KOKORO_PID_PATH.unlink()

    atexit.register(cleanup)

    def handle_signal(signum: int, _frame: object) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    server.serve_forever(poll_interval=0.25)
    return 0


def human_status(status: dict[str, object]) -> str:
    return (
        f"pid={status['pid']} device={status['device']} rss_mb={status['rss_mb']} "
        f"uptime_seconds={status['uptime_seconds']} requests_handled={status['requests_handled']} "
        f"socket={status['socket_path']}"
    )


def build_daemon_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the warm Kokoro daemon.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the daemon in the foreground.")
    serve.set_defaults(func=run_serve)

    start = subparsers.add_parser("start", help="Start the daemon if needed.")
    start.set_defaults(func=run_start)

    status = subparsers.add_parser("status", help="Show daemon status.")
    status.set_defaults(func=run_status)

    stop = subparsers.add_parser("stop", help="Stop the daemon.")
    stop.set_defaults(func=run_stop)

    restart = subparsers.add_parser("restart", help="Restart the daemon.")
    restart.set_defaults(func=run_restart)

    return parser


def run_serve(_: argparse.Namespace) -> int:
    return serve_forever()


def run_start(_: argparse.Namespace) -> int:
    status = ensure_service_running()
    print(human_status(status))
    return 0


def run_status(_: argparse.Namespace) -> int:
    try:
        status = send_request({"action": "status"}, timeout=2.0)
    except Exception as exc:
        print(f"not_running error={exc}")
        return 1
    print(human_status(status))
    return 0


def run_stop(_: argparse.Namespace) -> int:
    try:
        result = stop_service()
    except Exception as exc:
        print(f"not_running error={exc}")
        return 1
    print(result["message"])
    return 0


def run_restart(_: argparse.Namespace) -> int:
    try:
        stop_service()
    except Exception:
        pass
    status = ensure_service_running()
    print(human_status(status))
    return 0


def daemon_main(argv: list[str] | None = None) -> int:
    parser = build_daemon_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def read_text_arg(text_parts: list[str]) -> str:
    if text_parts:
        return " ".join(text_parts).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Pass text as an argument or pipe it on stdin.")


def default_live_output(language: str) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    token = uuid.uuid4().hex[:8]
    return KOKORO_TEMP_OUTPUT_DIR / f"kokoro-{language}-{timestamp}-{token}.wav"


def build_kokoro_say_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kokoro-say",
        description="Speak text through the warm Kokoro daemon.",
    )
    parser.add_argument("text", nargs="*", help="Text to speak. Reads stdin when omitted.")
    parser.add_argument("--lang", default="en", choices=["en", "fr"], help="Language preset.")
    parser.add_argument("--voice", help="Optional Kokoro voice override.")
    parser.add_argument("--list-voices", action="store_true", help="List available Kokoro voices for the chosen language.")
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED, help="Speech speed.")
    parser.add_argument("--output", type=Path, help="Optional wav output path.")
    parser.add_argument("--no-play", action="store_true", help="Generate audio without playing it.")
    parser.add_argument("--print-path", action="store_true", help="Print the output path.")
    return parser


def kokoro_say_main(argv: list[str] | None = None) -> int:
    parser = build_kokoro_say_parser()
    args = parser.parse_args(argv)
    if args.list_voices:
        for voice in list_available_voices(args.lang):
            print(voice)
        return 0
    text = read_text_arg(args.text)
    ensure_service_running()

    ephemeral = args.output is None and not args.no_play
    output_path = args.output or default_live_output(args.lang)
    result = send_request(
        {
            "action": "synthesize",
            "lang": args.lang,
            "voice": args.voice,
            "speed": args.speed,
            "text": text,
            "output": str(output_path),
        }
    )
    status = send_request({"action": "status"}, timeout=2.0)
    if not args.no_play:
        subprocess.run(["afplay", str(output_path)], check=True)
    if args.print_path or args.no_play or args.output:
        print(output_path)
    print(
        " ".join(
            [
                f"lang={result['lang']}",
                f"voice={result['voice']}",
                f"elapsed_seconds={result['elapsed_seconds']}",
                f"audio_seconds={result['audio_seconds']}",
                f"daemon_rss_mb={result['rss_mb']}",
                f"requests_handled={status['requests_handled']}",
            ]
        ),
        file=sys.stderr,
    )
    if ephemeral and output_path.exists():
        output_path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(daemon_main())

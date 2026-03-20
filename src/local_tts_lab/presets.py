from __future__ import annotations


SAMPLE_TEXTS = {
    "en": (
        "Hello from the local TTS lab. This benchmark is checking quality and startup cost "
        "for a short English sample."
    ),
    "fr": (
        "Bonjour depuis le laboratoire TTS local. Ce test compare la qualite de la voix "
        "et le temps de demarrage sur un court extrait en francais."
    ),
}


DEFAULT_VOICES = {
    "macos-say": {
        "en": "Samantha",
        "fr": "Thomas",
    },
    "kokoro": {
        "en": "af_heart",
        "fr": "ff_siwis",
    },
    "piper": {
        "en": "en_US-lessac-medium",
        "fr": "fr_FR-siwis-medium",
    },
    "melo": {
        "en": "EN-US",
        "fr": "FR",
    },
}

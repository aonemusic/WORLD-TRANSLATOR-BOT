"""Environment-based configuration and supported language metadata."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# The list is intentionally broader than any single Argos model catalog. Exact
# availability depends on the open translation packages available at runtime.
LANGUAGES: dict[str, str] = {
    "ar": "Arabic", "bn": "Bengali", "zh": "Chinese", "nl": "Dutch",
    "en": "English", "fa": "Persian", "fr": "French", "de": "German",
    "el": "Greek", "gu": "Gujarati", "he": "Hebrew", "hi": "Hindi",
    "id": "Indonesian", "it": "Italian", "ja": "Japanese", "kn": "Kannada",
    "ko": "Korean", "ml": "Malayalam", "mr": "Marathi", "ne": "Nepali",
    "pl": "Polish", "pt": "Portuguese", "ru": "Russian", "es": "Spanish",
    "sw": "Swahili", "ta": "Tamil", "te": "Telugu", "th": "Thai",
    "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu", "vi": "Vietnamese",
}

@dataclass(frozen=True)
class Settings:
    bot_token: str
    libretranslate_url: str | None
    whisper_model: str
    max_download_mb: int
    ocr_languages: str


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is missing. Set it as an environment variable.")
    endpoint = os.getenv("LIBRETRANSLATE_URL", "").strip().rstrip("/") or None
    return Settings(
        bot_token=token,
        libretranslate_url=endpoint,
        whisper_model=os.getenv("WHISPER_MODEL", "tiny").strip() or "tiny",
        max_download_mb=max(1, int(os.getenv("MAX_DOWNLOAD_MB", "20"))),
        ocr_languages=os.getenv("TESSERACT_LANGUAGES", "eng+mal+ara+hin+urd+tam+spa+fra+deu+chi_sim+jpn"),
    )

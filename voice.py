"""Lazy-loaded local speech recognition using Faster-Whisper."""
from __future__ import annotations

import logging
import threading

log = logging.getLogger(__name__)
_MODEL_LOCK = threading.Lock()
_MODEL = None


def transcribe_audio(audio_path: str, model_size: str = "tiny") -> str:
    """Transcribe audio locally. Model weights download on first invocation."""
    global _MODEL
    from faster_whisper import WhisperModel

    with _MODEL_LOCK:
        if _MODEL is None:
            log.info("Loading Faster-Whisper model '%s' on CPU", model_size)
            _MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = _MODEL.transcribe(audio_path, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    if not text:
        raise ValueError("No clear speech was detected in that audio.")
    return text

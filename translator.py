"""Open-source translation adapter: optional LibreTranslate, then Argos Translate."""
from __future__ import annotations

import logging
import threading
from functools import lru_cache

import httpx
from langdetect import DetectorFactory, detect

from config import LANGUAGES

log = logging.getLogger(__name__)
DetectorFactory.seed = 0
_ARGOS_LOCK = threading.Lock()


def split_text(text: str, limit: int = 2800) -> list[str]:
    """Split text at paragraph/sentence/word boundaries under a safe model size."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    current = ""
    for paragraph in text.splitlines():
        parts = [paragraph]
        if len(paragraph) > limit:
            parts = []
            sentence = ""
            for token in paragraph.split(" "):
                candidate = f"{sentence} {token}".strip()
                if len(candidate) > limit and sentence:
                    parts.append(sentence)
                    sentence = token
                else:
                    sentence = candidate
            if sentence:
                parts.append(sentence)
        for part in parts:
            candidate = f"{current}\n{part}".strip()
            if len(candidate) > limit and current:
                chunks.append(current)
                current = part
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def detect_language(text: str) -> str:
    text = text.strip()
    if len(text) < 3:
        raise ValueError(
            "This message is too short for automatic language detection. "
            "Choose the source language manually, or send a longer message."
        )
    try:
        code = detect(text)
    except Exception as exc:
        raise ValueError("I couldn't identify the source language. Please choose it manually.") from exc
    # Common detector and Argos code variants.
    code = {"zh-cn": "zh", "zh-tw": "zh", "iw": "he"}.get(code.lower(), code.lower())
    if code not in LANGUAGES:
        raise ValueError(
            "Automatic detection found a language that isn't in this bot's source-language list. "
            "Choose a supported source language manually with /languages."
        )
    return code


def _argos_prepare(source: str, target: str):
    import argostranslate.package
    import argostranslate.translate

    with _ARGOS_LOCK:
        available = argostranslate.package.get_available_packages()
        installed = argostranslate.translate.get_installed_languages()
        installed_codes = {lang.code for lang in installed}
        packages = {(p.from_code, p.to_code): p for p in available}
        # Prefer a direct model. If unavailable, use an English pivot when both
        # legs are present in the upstream catalog.
        paths = [[(source, target)]]
        if source != "en" and target != "en":
            paths.append([(source, "en"), ("en", target)])
        selected = next((path for path in paths if all(pair in packages for pair in path)), None)
        if selected is None:
            raise RuntimeError(
                f"No Argos translation model is available for {source} → {target}. "
                "Try another language pair or configure a self-hosted LibreTranslate URL."
            )
        for from_code, to_code in selected:
            if from_code not in installed_codes or to_code not in installed_codes:
                package = packages[(from_code, to_code)]
                log.info("Installing open translation model %s -> %s", from_code, to_code)
                path = package.download()
                argostranslate.package.install_from_path(path)
                installed_codes.update((from_code, to_code))
        languages = {lang.code: lang for lang in argostranslate.translate.get_installed_languages()}
        return languages, selected


def _argos_translate(text: str, source: str, target: str) -> str:
    import argostranslate.translate

    languages, path = _argos_prepare(source, target)
    translated = text
    for from_code, to_code in path:
        translation = languages[from_code].get_translation(languages[to_code])
        translated = translation.translate(translated)
    return translated


def _translate_chunk(text: str, source: str, target: str, endpoint: str | None) -> str:
    if endpoint:
        try:
            response = httpx.post(
                f"{endpoint}/translate",
                json={"q": text, "source": source, "target": target, "format": "text"},
                timeout=90.0,
            )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and payload.get("translatedText"):
                return str(payload["translatedText"])
            raise RuntimeError("LibreTranslate returned no translatedText field.")
        except Exception as exc:
            log.warning("LibreTranslate request failed; trying local Argos: %s", exc)
    return _argos_translate(text, source, target)


def translate_text(text: str, source: str, target: str, endpoint: str | None = None) -> tuple[str, str]:
    """Translate text and return (translation, resolved source language)."""
    text = text.strip()
    if not text:
        raise ValueError("Please send some text to translate.")
    if target not in LANGUAGES:
        raise ValueError("That target language is not supported in the menu.")
    if source == "auto":
        source = detect_language(text)
    if source not in LANGUAGES:
        raise ValueError("I couldn't identify a supported source language. Choose it with /languages.")
    if source == target:
        return text, source
    chunks = split_text(text)
    result = "\n".join(_translate_chunk(chunk, source, target, endpoint) for chunk in chunks)
    if not result.strip():
        raise RuntimeError("The translation engine returned an empty result.")
    return result, source

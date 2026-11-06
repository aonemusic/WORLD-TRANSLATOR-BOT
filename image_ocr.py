"""Image text extraction through the local Tesseract OCR engine."""
from __future__ import annotations

from PIL import Image, ImageOps
import pytesseract


def extract_image_text(image_path: str, configured_languages: str = "eng") -> str:
    try:
        installed = set(pytesseract.get_languages(config=""))
    except Exception as exc:
        raise RuntimeError("Tesseract OCR is not installed or could not be started.") from exc
    requested = [code.strip() for code in configured_languages.split("+") if code.strip()]
    available = [code for code in requested if code in installed]
    if "eng" in installed and "eng" not in available:
        available.insert(0, "eng")
    if not available:
        available = ["eng"] if "eng" in installed else []
    if not available:
        raise RuntimeError("No Tesseract language data is installed. Install at least English (eng).")
    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        text = pytesseract.image_to_string(image, lang="+".join(available)).strip()
    if not text:
        raise ValueError("I couldn't find readable text in that image.")
    return text

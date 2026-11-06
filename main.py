"""WORLD TRANSLATOR Telegram bot entry point."""
from __future__ import annotations

import asyncio
import logging
import os
import threading
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

from config import LANGUAGES, get_settings
from document import extract_document, write_translated_document
from image_ocr import extract_image_text
from keyboards import language_home, language_picker, main_menu, retry_keyboard
from translator import translate_text
from voice import transcribe_audio

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
# HTTPX logs full Telegram API request URLs at INFO, including the bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("world_translator")
SETTINGS = get_settings()


def _user_prefs(context: ContextTypes.DEFAULT_TYPE) -> dict[str, str]:
    prefs = context.user_data
    prefs.setdefault("source", "auto")
    prefs.setdefault("target", "en")
    return prefs


async def _translate(text: str, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, str]:
    prefs = _user_prefs(context)
    return await asyncio.to_thread(
        translate_text, text, prefs["source"], prefs["target"], SETTINGS.libretranslate_url
    )


async def _send_long_text(update: Update, text: str) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    # Telegram messages have a 4096 character cap; keep a margin for headers.
    pieces: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        while len(line) > 3900:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(line[:3900])
            line = line[3900:]
        if len(current) + len(line) > 3900 and current:
            pieces.append(current)
            current = line
        else:
            current += line
    if current:
        pieces.append(current)
    for piece in pieces:
        await chat.send_message(piece)


async def _do_translation(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    msg = update.effective_message
    if msg is None:
        return
    status = await msg.reply_text("⏳ Translating…")
    try:
        translated, source = await _translate(text, context)
        source_name = LANGUAGES.get(source, source)
        target_name = LANGUAGES.get(_user_prefs(context)["target"], "English")
        await status.delete()
        await _send_long_text(update, f"🌐 {source_name} → {target_name}\n\n{translated}")
        # No successful translation history is retained.
        context.user_data.pop("retry_text", None)
    except Exception as exc:
        log.warning("Translation failed (%s)", type(exc).__name__)
        await status.edit_text(
            "⚠️ I couldn't translate that right now. Check the language pair or try again.",
            reply_markup=retry_keyboard(),
        )
        # Keep only the current failed request in memory for a short-lived retry;
        # it is never written to disk and is cleared on success/cancel.
        context.user_data["retry_text"] = text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _user_prefs(context)
    if update.effective_message:
        await update.effective_message.reply_text(
            "🌍 *WORLD TRANSLATOR*\n\nTranslate text, voice, images, and documents with open-source tools.\n\nChoose an option to get started:",
            parse_mode="Markdown", reply_markup=main_menu(),
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "Send text while Translate Text is active, or send a voice message, photo, PDF, DOCX, or TXT file.\n\n"
            "Commands: /start, /translate, /languages, /settings, /about, /cancel.\n"
            "Choose a target language in Select Language. Text translation uses local Argos models, or an optional self-hosted LibreTranslate server."
        )


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "text"
    if update.effective_message:
        await update.effective_message.reply_text("✍️ Send the text you want translated. Use /cancel to leave this mode.")


async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prefs = _user_prefs(context)
    if update.effective_message:
        await update.effective_message.reply_text(
            "🌐 Choose a source or target language. Exact translation-pair availability depends on the installed open model catalog.",
            reply_markup=language_home(prefs["source"], prefs["target"]),
        )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prefs = _user_prefs(context)
    if update.effective_message:
        await update.effective_message.reply_text(
            f"⚙️ Current source: {('Automatic detection' if prefs['source'] == 'auto' else LANGUAGES.get(prefs['source'], prefs['source']))}\n"
            f"Target: {LANGUAGES.get(prefs['target'], prefs['target'])}\n\nPreferences are temporary and reset when the bot restarts.",
            reply_markup=language_home(prefs["source"], prefs["target"]),
        )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "WORLD TRANSLATOR\nOpen-source translation using Argos Translate, Faster-Whisper and Tesseract OCR.\n"
            "No user database or translation-history store is used. Language models may download on first use."
        )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("mode", None)
    context.user_data.pop("retry_text", None)
    if update.effective_message:
        await update.effective_message.reply_text("Cancelled. Choose an option from the menu.", reply_markup=main_menu())


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or not msg.text:
        return
    if context.user_data.get("mode") != "text":
        await msg.reply_text("Choose 🌍 Translate Text first, or use /translate.", reply_markup=main_menu())
        return
    await _do_translation(update, context, msg.text)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    data = query.data or ""
    prefs = _user_prefs(context)
    msg = query.message
    if data == "menu:home":
        context.user_data.pop("mode", None)
        await query.edit_message_text("🌍 *WORLD TRANSLATOR*\n\nChoose an option:", parse_mode="Markdown", reply_markup=main_menu())
    elif data == "menu:text":
        context.user_data["mode"] = "text"
        await query.edit_message_text("✍️ Send the text you want translated. Use /cancel to exit.", reply_markup=main_menu())
    elif data in {"menu:voice", "menu:image", "menu:document"}:
        context.user_data.pop("mode", None)
        prompt = {
            "menu:voice": "🎤 Send a voice message or audio file to transcribe and translate.",
            "menu:image": "🖼 Send a photo or image containing text.",
            "menu:document": "📄 Send a PDF, DOCX, or TXT document.",
        }[data]
        await query.edit_message_text(prompt, reply_markup=main_menu())
    elif data == "menu:settings":
        source = "Automatic detection" if prefs["source"] == "auto" else LANGUAGES.get(prefs["source"], prefs["source"])
        target = LANGUAGES.get(prefs["target"], prefs["target"])
        await query.edit_message_text(f"⚙️ Source: {source}\nTarget: {target}\n\nThese preferences are held temporarily in memory.", reply_markup=language_home(prefs["source"], prefs["target"]))
    elif data == "menu:about":
        await query.edit_message_text("WORLD TRANSLATOR\nOpen-source tools. No user database or saved translation history. Models may download on first use.", reply_markup=main_menu())
    elif data == "langs:home":
        await query.edit_message_text("🌐 Language settings", reply_markup=language_home(prefs["source"], prefs["target"]))
    elif data in {"langs:source", "langs:target"}:
        which = data.split(":", 1)[1]
        await query.edit_message_text(f"Choose {which} language:", reply_markup=language_picker(which))
    elif data.startswith("lang:"):
        _, which, code = data.split(":", 2)
        if which in {"source", "target"} and (code == "auto" and which == "source" or code in LANGUAGES):
            prefs[which] = code
        await query.edit_message_text("🌐 Language settings updated.", reply_markup=language_home(prefs["source"], prefs["target"]))
    elif data == "langs:swap":
        if prefs["source"] == "auto":
            await query.answer("Choose a specific source language before swapping.", show_alert=True)
        else:
            prefs["source"], prefs["target"] = prefs["target"], prefs["source"]
            await query.edit_message_text("⇄ Languages swapped.", reply_markup=language_home(prefs["source"], prefs["target"]))
    elif data == "retry":
        text = context.user_data.get("retry_text")
        if text:
            await _do_translation(update, context, text)
        else:
            await query.edit_message_text("No failed translation is available to retry.", reply_markup=main_menu())
    elif data == "cancel":
        context.user_data.pop("retry_text", None)
        await query.edit_message_text("Cancelled.", reply_markup=main_menu())


async def _download(update: Update, telegram_file, path: Path) -> None:
    size = telegram_file.file_size or 0
    if size > SETTINGS.max_download_mb * 1024 * 1024:
        raise ValueError(f"That file is too large. The current limit is {SETTINGS.max_download_mb} MB.")
    await telegram_file.download_to_drive(custom_path=str(path))


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return
    media = msg.voice or msg.audio
    if media is None:
        return
    status = await msg.reply_text("🎤 Downloading and transcribing audio locally…")
    try:
        with tempfile.TemporaryDirectory(prefix="wt_voice_") as temp_dir:
            audio_path = Path(temp_dir) / "audio.bin"
            await _download(update, await context.bot.get_file(media.file_id), audio_path)
            recognized = await asyncio.to_thread(transcribe_audio, str(audio_path), SETTINGS.whisper_model)
            translated, source = await _translate(recognized, context)
        await status.delete()
        target = LANGUAGES.get(_user_prefs(context)["target"], "English")
        await _send_long_text(update, f"🎤 Recognized ({LANGUAGES.get(source, source)}):\n{recognized}\n\n🌐 Translation ({target}):\n{translated}")
    except Exception as exc:
        log.warning("Voice processing failed (%s)", type(exc).__name__)
        await status.edit_text("⚠️ I couldn't process that audio. Check the file size and try another recording. The first transcription may take longer while the local model downloads.")


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or not msg.photo:
        return
    status = await msg.reply_text("🖼 Reading text from the image…")
    try:
        photo = msg.photo[-1]
        with tempfile.TemporaryDirectory(prefix="wt_image_") as temp_dir:
            image_path = Path(temp_dir) / "image.jpg"
            await _download(update, await context.bot.get_file(photo.file_id), image_path)
            original = await asyncio.to_thread(extract_image_text, str(image_path), SETTINGS.ocr_languages)
            translated, source = await _translate(original, context)
        await status.delete()
        target = LANGUAGES.get(_user_prefs(context)["target"], "English")
        await _send_long_text(update, f"🖼 Extracted text ({LANGUAGES.get(source, source)}):\n{original}\n\n🌐 Translation ({target}):\n{translated}")
    except Exception as exc:
        log.warning("Image OCR failed (%s)", type(exc).__name__)
        await status.edit_text("⚠️ I couldn't read that image. Try a clearer photo with well-lit, sharply focused text.")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or not msg.document:
        return
    document = msg.document
    suffix = Path(document.file_name or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        await msg.reply_text("Supported document formats are PDF, DOCX, and TXT.")
        return
    status = await msg.reply_text("📄 Extracting and translating the document…")
    try:
        with tempfile.TemporaryDirectory(prefix="wt_doc_") as temp_dir:
            source_path = Path(temp_dir) / f"input{suffix}"
            await _download(update, await context.bot.get_file(document.file_id), source_path)
            original, source_format = await asyncio.to_thread(extract_document, str(source_path))
            translated, source = await _translate(original, context)
            output_suffix = ".docx" if source_format == ".docx" else ".txt"
            output_path = Path(temp_dir) / f"translated{output_suffix}"
            await asyncio.to_thread(write_translated_document, translated, source_format, str(output_path))
            await status.delete()
            target = LANGUAGES.get(_user_prefs(context)["target"], "English")
            await msg.reply_text(f"🌐 {LANGUAGES.get(source, source)} → {target}\n\nOriginal text was extracted and translated. Scanned PDFs need OCR before upload.")
            with output_path.open("rb") as file_obj:
                await msg.reply_document(document=file_obj, filename=f"translated{output_suffix}", caption="Translated document")
    except Exception as exc:
        log.warning("Document processing failed (%s)", type(exc).__name__)
        details = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Please try a smaller, valid file."
        await status.edit_text(f"⚠️ Document processing failed. {details}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    log.error("Unhandled bot error (%s)", type(error).__name__ if error else "unknown")


def start_health_server() -> ThreadingHTTPServer:
    """Bind a tiny HTTP health endpoint for Render's Web Service monitor."""
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in {"/", "/health"}:
                self.send_error(404)
                return
            body = b"WORLD TRANSLATOR is running.\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            # Routine Render health probes should not clutter application logs.
            return

    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, name="render-health", daemon=True).start()
    log.info("Render health endpoint listening on 0.0.0.0:%s", port)
    return server


def main() -> None:
    start_health_server()
    app = Application.builder().token(SETTINGS.bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("translate", translate_command))
    app.add_handler(CommandHandler("languages", languages_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_handler))
    app.add_handler(MessageHandler(filters.PHOTO, image_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)
    log.info("Starting WORLD TRANSLATOR with long polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

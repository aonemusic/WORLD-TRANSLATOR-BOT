"""Polished Telegram inline keyboards using Bot API button styles."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import LANGUAGES


def _button(text: str, data: str, style: str = "primary") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data, style=style)


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_button("🌍 Translate Text", "menu:text", "primary")],
        [_button("🎤 Voice Translation", "menu:voice", "success"), _button("🖼 Image Translation", "menu:image", "primary")],
        [_button("📄 Document Translation", "menu:document", "success")],
        [_button("🌐 Select Language", "langs:home", "primary")],
        [_button("⚙️ Settings", "menu:settings", "primary"), _button("ℹ️ About", "menu:about", "primary")],
    ])


def language_home(source: str, target: str) -> InlineKeyboardMarkup:
    src = "Automatic" if source == "auto" else LANGUAGES.get(source, source)
    dst = LANGUAGES.get(target, target)
    return InlineKeyboardMarkup([
        [_button(f"Source: {src}", "langs:source", "primary")],
        [_button(f"Target: {dst}", "langs:target", "success")],
        [_button("⇄ Swap source / target", "langs:swap", "primary")],
        [_button("⬅️ Main menu", "menu:home", "danger")],
    ])


def language_picker(which: str) -> InlineKeyboardMarkup:
    options = [(name, code) for code, name in LANGUAGES.items()]
    if which == "source":
        options.insert(0, ("✨ Automatic detection", "auto"))
    buttons = [_button(name, f"lang:{which}:{code}", "primary") for name, code in options]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([_button("⬅️ Back", "langs:home", "danger")])
    return InlineKeyboardMarkup(rows)


def retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_button("🔁 Retry translation", "retry", "success")],
        [_button("✖ Cancel", "cancel", "danger")],
    ])


def translation_error_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_button("🌐 Choose language pair", "langs:home", "primary")],
        [_button("🔁 Retry translation", "retry", "success"), _button("✖ Cancel", "cancel", "danger")],
    ])

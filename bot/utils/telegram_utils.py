"""Telegram messaging utilities."""
from telegram import Update
from telegram.error import BadRequest


async def send_markdown_message(update: Update, text: str) -> None:
    """Send message with Markdown formatting, fallback to plain text on error.

    Args:
        update: Telegram update
        text: Message text to send

    Returns:
        Message object that was sent
    """
    try:
        # Try to send with Markdown formatting
        return await update.message.reply_text(text, parse_mode='Markdown')
    except BadRequest as e:
        # If Markdown fails, send as plain text
        return await update.message.reply_text(text)

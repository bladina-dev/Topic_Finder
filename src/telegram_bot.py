"""Telegram Bot — send-only module for delivering reports.

No persistent listener needed — works with GitHub Actions.
Uses the Telegram Bot API directly for simplicity.
"""

from __future__ import annotations

import asyncio
import httpx

from .config import settings


TELEGRAM_API = "https://api.telegram.org/bot{token}"
MAX_MESSAGE_LENGTH = 4096


async def _send_message(
    text: str,
    parse_mode: str = "Markdown",
    chat_id: str | None = None,
) -> bool:
    """Send a single message via Telegram Bot API.

    Args:
        text: Message text.
        parse_mode: Telegram parse mode ("Markdown" or "HTML").
        chat_id: Override chat ID (defaults to config).

    Returns:
        True if message sent successfully.
    """
    token = settings.telegram_bot_token
    target_chat = chat_id or settings.telegram_chat_id

    if not token:
        print("[Telegram] No bot token configured, skipping send.")
        return False
    if not target_chat:
        print("[Telegram] No chat_id configured, skipping send.")
        return False

    url = f"{TELEGRAM_API.format(token=token)}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": parse_mode,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                return True
            else:
                print(f"[Telegram] Send failed: {response.status_code} — {response.text}")
                return False
    except Exception as e:
        print(f"[Telegram] Error sending message: {e}")
        return False


async def send_text(text: str, chat_id: str | None = None) -> bool:
    """Send a plain text message, splitting if too long.

    Args:
        text: Message to send.
        chat_id: Override chat ID.

    Returns:
        True if all chunks sent successfully.
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        return await _send_message(text, parse_mode="Markdown", chat_id=chat_id)

    # Split into chunks at newline boundaries
    chunks = _split_message(text)
    success = True
    for chunk in chunks:
        if not await _send_message(chunk, parse_mode="Markdown", chat_id=chat_id):
            success = False
    return success


async def send_report(report_text: str, chat_id: str | None = None) -> bool:
    """Send a formatted report to Telegram.

    Args:
        report_text: Pre-formatted report text (from report_writer.format_telegram_report).
        chat_id: Override chat ID.

    Returns:
        True if sent successfully.
    """
    return await send_text(report_text, chat_id=chat_id)


async def send_top_angles(
    angles: list[dict],
    chat_id: str | None = None,
) -> bool:
    """Send a quick summary of top angles.

    Args:
        angles: List of angle dicts with 'headline', 'total', 'hook'.
        chat_id: Override chat ID.

    Returns:
        True if sent successfully.
    """
    from .report_writer import simplified_grade

    lines = ["🏆 *Top Angles Right Now:*", ""]
    for i, angle in enumerate(angles[:5], 1):
        total = angle.get("total", 0)
        grade_emoji, action = simplified_grade(total)
        lines.append(f"{i}. {grade_emoji} *{angle.get('headline', '')}*")
        lines.append(f"   Score: {total}/60 — {action}")
        if angle.get("hook"):
            lines.append(f"   🪝 _{angle['hook'][:100]}_")
        lines.append("")

    return await send_text("\n".join(lines), chat_id=chat_id)


def _split_message(text: str) -> list[str]:
    """Split a long message into chunks that fit Telegram's limit.

    Tries to split at newlines to preserve formatting.
    """
    chunks: list[str] = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            if current:
                chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        chunks.append(current)

    return chunks


def send_text_sync(text: str, chat_id: str | None = None) -> bool:
    """Synchronous wrapper for send_text. Use in scripts/CLI."""
    return asyncio.run(send_text(text, chat_id=chat_id))


def send_report_sync(report_text: str, chat_id: str | None = None) -> bool:
    """Synchronous wrapper for send_report. Use in scripts/CLI."""
    return asyncio.run(send_report(report_text, chat_id=chat_id))

"""Approval Bot — listens for Telegram inline keyboard callbacks and updates Obsidian files.

Run this script in a persistent terminal session (or tmux) to receive approve/skip taps
from the inline keyboard buttons sent by run_and_report.py.

Usage:
    UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/approval_bot.py
"""

from __future__ import annotations

import html as _html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from src.config import settings
from src.obsidian_sync import update_angle_status


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle approve/skip button taps from inline keyboards."""
    query = update.callback_query
    if not query or not query.data:
        return

    try:
        action, filename_stem = query.data.split(":", 1)
    except ValueError:
        await query.answer("Invalid callback data.")
        return

    if action not in ("approve", "skip"):
        await query.answer("Unknown action.")
        return

    print(f"[ApprovalBot] {action}: {filename_stem}")

    new_status = "approved" if action == "approve" else "skipped"
    success = update_angle_status(settings.obsidian_vault_path, filename_stem, new_status)

    if success:
        answer_text = "Approved!" if action == "approve" else "Skipped!"
        label = "✅ APPROVED" if action == "approve" else "❌ SKIPPED"
        await query.answer(answer_text)
        if query.message and query.message.text:
            original = _html.escape(query.message.text)
            await query.edit_message_text(
                text=f"{original}\n\n{label}",
                parse_mode="HTML",
            )
    else:
        await query.answer("❌ Failed to update file.")


def main() -> None:
    token = settings.telegram_bot_token
    if not token:
        print("[ApprovalBot] No TELEGRAM_BOT_TOKEN configured. Exiting.")
        sys.exit(1)

    print("[ApprovalBot] Listening for approve/skip callbacks...")

    app = Application.builder().token(token).build()
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

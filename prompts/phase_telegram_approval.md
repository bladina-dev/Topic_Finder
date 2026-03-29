# Telegram Approval Bot — Interactive Approve/Skip with Trend Context

**Date:** 2026-03-18 | **Repo:** `~/Documents/antigravity/marketing-agent/`
**Prereqs:** Obsidian vault working (phase_obsidian_feedback done), Telegram bot working

---

## Critical Warnings

| Warning | Fix |
|:---|:---|
| W1: UV cache | Use `UV_CACHE_DIR=/tmp/uv-cache` prefix if cache errors |
| W2: Never `git add -A` | Stage specific files only |
| W3: python-telegram-bot version | Use python-telegram-bot v20+ (async, already in requirements) |
| W4: Callback data limit | Telegram inline keyboard callback_data has 64 byte limit — use short file IDs |
| W5: Never crash the pipeline | Approval message failures must not crash the main pipeline |

---

## The Prompt

```
Read ~/Documents/antigravity/marketing-agent/src/telegram_bot.py and ~/Documents/antigravity/marketing-agent/src/obsidian_sync.py and ~/Documents/antigravity/marketing-agent/scripts/run_and_report.py and ~/Documents/antigravity/marketing-agent/src/models.py. Add interactive Telegram approval with trend context so the user can approve or skip angles from their phone. First add a new function to src/telegram_bot.py called send_angle_for_approval(trend: Trend, angle: ContentAngle, grade: str, angle_file: str) -> bool. This function sends a Telegram message with this format: first line "📡 TREND: {trend.title}" in bold, then a simple paragraph using trend.description (if available) or "Source: {trend.source_name or trend.source.value} | {trend.url}" to explain what the trend is about, then a blank line, then "📌 {angle.headline}" in bold, then the hook text in italics truncated to 200 chars, then a line with "{grade} | 🎯 {comma-joined trigger types} | {angle.platform.value}", then an InlineKeyboardMarkup with two buttons in one row: InlineKeyboardButton("✅ Approve", callback_data="approve:{angle_file_stem}") and InlineKeyboardButton("❌ Skip", callback_data="skip:{angle_file_stem}") where angle_file_stem is the filename without extension truncated to 50 chars to fit the 64-byte callback_data limit. Use parse_mode="HTML" instead of Markdown to avoid the parsing errors — use <b> for bold, <i> for italic, and make sure to escape any < > & characters in the trend/angle text using html.escape(). Second, add a function update_angle_status(vault_path: str, filename_stem: str, new_status: str) -> bool to src/obsidian_sync.py. This reads the markdown file matching the filename_stem in vault_path/angles/, finds the "status: " line in the YAML frontmatter, replaces its value with new_status, writes the file back, returns True on success. Third, create ~/Documents/antigravity/marketing-agent/scripts/approval_bot.py — a standalone script that runs the Telegram bot in long-polling mode to listen for inline keyboard callbacks. Use python-telegram-bot v20+ async Application. Register a CallbackQueryHandler that: parses callback_data as "action:filename_stem", calls update_angle_status with the vault path from settings and the parsed action and filename, answers the callback query with "Approved!" or "Skipped!" text, edits the original message to append a line at the bottom saying "✅ APPROVED" or "❌ SKIPPED" so the user sees visual confirmation, uses html.escape on all user-facing text. The bot should print "[ApprovalBot] Listening for approve/skip callbacks..." on startup and "[ApprovalBot] {action}: {filename_stem}" on each callback. Fourth, modify scripts/run_and_report.py: after step 5 (Obsidian sync), add step 6 that sends individual approval messages. Only send angles with grade fire or good (skip weak angles). Import send_angle_for_approval from src.telegram_bot. For each angle in the results that has grade fire or good, call send_angle_for_approval with the trend, angle, grade string, and the angle filename that was written by obsidian_sync. To get the filename, modify push_angles in obsidian_sync.py to return a list of tuples (angle, trend, filename) instead of just a count, or return both count and a list of written filenames. Wrap step 6 in try/except so failures never crash the pipeline. Add a 0.5 second asyncio.sleep between messages to avoid Telegram rate limits. Print "[6/6] Sending {n} angles for approval..." and "[6/6] Done: {n} angles sent for mobile approval". Add OBSIDIAN_VAULT_PATH to .env if not already there. Run "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/telegram_bot.py src/obsidian_sync.py scripts/run_and_report.py scripts/approval_bot.py". IMPORTANT GIT SAFETY: never use git add -A. Stage with "git add src/telegram_bot.py src/obsidian_sync.py scripts/run_and_report.py scripts/approval_bot.py" and commit "feat: Telegram approval bot with trend context and inline keyboards".
```

---

## How It Works

```
Pipeline Run:
  Steps 1-5: (same as before — trends, angles, reports, telegram summary, obsidian)
  Step 6 NEW: For each Fire/Good angle, send individual Telegram message:

  ┌─────────────────────────────────────────┐
  │ 📡 TREND: Saudi Vision 2030 Q2 Update   │
  │ Latest economic data shows 12% growth   │
  │ in non-oil sectors. Source: Gulf News    │
  │                                          │
  │ 📌 Why Vision 2030 Changes Everything    │
  │ Everyone's talking about it. But nobody  │
  │ is connecting the dots to YOUR business  │
  │                                          │
  │ 🔥 Fire | 🎯 fomo, curiosity_gap | linkedin │
  │                                          │
  │  [✅ Approve]    [❌ Skip]               │
  └─────────────────────────────────────────┘

User taps "Approve" on iPad/Android:
  → approval_bot.py receives callback
  → Updates obsidian-vault/angles/{file}.md → status: approved
  → Replies "✅ Approved!" in Telegram

Next pipeline run:
  → Reads approved/skipped from Obsidian
  → AI adapts to your patterns
```

---

## Running the Approval Bot

```bash
# Terminal 1: Run the approval bot (keeps listening)
cd ~/Documents/antigravity/marketing-agent
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/approval_bot.py

# Terminal 2: Run the pipeline (whenever you want)
cd ~/Documents/antigravity/marketing-agent
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_and_report.py
```

The approval bot must stay running to receive button taps. You can run it in the background or as a tmux/screen session.

---

## Validation After Running

```bash
# Lint check
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/telegram_bot.py src/obsidian_sync.py scripts/approval_bot.py

# Start approval bot in background
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/approval_bot.py &

# Run pipeline
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_and_report.py

# Check Telegram — you should see individual angle messages with buttons
# Tap Approve on one, Skip on another
# Then check the obsidian files changed:
grep "status:" obsidian-vault/angles/*.md | head -5
```

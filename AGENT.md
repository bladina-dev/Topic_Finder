# AGENT.md — Topic Finder (Marketing Agent)

This file provides guidance to Claude Code when working in this repository.

## What This Project Does

Autonomous marketing agent for the Saudi/Gulf market. Scans trends (Tavily, YouTube, Google Trends), generates content angles in Arabic and English using Gemini/Claude, benchmarks quality across 6 dimensions, and delivers reports via Telegram. Runs on a schedule via GitHub Actions — no server required.

## Project State

| Version | Status |
|---------|--------|
| v0.1.0 | Core pipeline: Tavily + Gemini + benchmark |
| v0.2.0 | CSV sources, Telegram delivery, GitHub Actions |
| v0.3.0 | YouTube scanner (yt-dlp + YouTube Data API v3) |
| **v0.4.0** | **In progress — google.genai migration, parse fix, cliché expansion** |

> See `docs/v0.4.0-plan.md` for full scope.

## Run Commands

```bash
# Install
uv sync

# Test pipeline (no API calls)
uv run python run_benchmark.py --mode mock --no-judge

# Live run
uv run python run_benchmark.py --mode live --trends 4 --angles 3

# Full pipeline + report + Telegram send
uv run python scripts/run_and_report.py

# CLI
uv run marketing-agent generate --sources saudi_general
uv run marketing-agent sources list
uv run marketing-agent report
```

## Architecture

```
src/
  pipeline.py         — orchestrates scan → generate → benchmark
  trend_scanner.py    — Tavily, Google Trends (with retry), targeted CSV sources
  yt_scanner.py       — YouTube channel scan + trending KSA (YouTube Data API v3)
  ai_orchestrator.py  — multi-provider angle generation (Gemini / Claude)
  benchmark.py        — 6-dimension scoring: CN/TD/VM/BA/CR/HP
  source_manager.py   — CSV-based source management
  report_writer.py    — Markdown / HTML / JSON / Telegram formatting
  telegram_bot.py     — send-only Telegram bot (@Trendozer_bot)
  config.py           — Pydantic Settings (loads .env)
  models.py           — all Pydantic data models
  cli.py              — Typer CLI
  api.py              — FastAPI server

sources/              — CSV source lists (editable in Excel/Sheets)
scripts/run_and_report.py  — GitHub Actions entrypoint
.github/workflows/    — scheduled_run.yml (6AM+6PM Cairo), telegram_command.yml
reports/              — dated output files (gitignored)
brand_data/           — ChromaDB brand memory (gitignored)
```

## Known Issues / Fixed in v0.4.0

- ~~`google.generativeai` deprecated~~ — migrated to `google.genai` ✅
- ~~Angle parse errors~~ — improved JSON extraction + raw response logging ✅
- ~~Google Trends 404 spam~~ — gated behind `google_trends_enabled=False` ✅
- ~~`pyproject.toml` at 0.2.0`~~ — bumped to `0.3.0` ✅
- ~~Cliché patterns thin~~ — EN 12→22, AR 6→14 patterns ✅

## Key Environment Variables

```env
GOOGLE_API_KEY=          # Gemini + YouTube Data API
TAVILY_API_KEY=          # Trend scanning
TELEGRAM_BOT_TOKEN=      # @Trendozer_bot
TELEGRAM_CHAT_ID=        # Delivery target
ANTHROPIC_API_KEY=       # Claude provider (optional)
YOUTUBE_DATA_API_KEY=    # YouTube trending KSA
```

## Scoring System

Each angle is scored across 6 dimensions (max 60):
- **CN** Creative Novelty — **TD** Psych Trigger Depth — **VM** Viral Mechanics
- **BA** Brand Alignment — **CR** Cultural Relevance — **HP** Hook Power

Grades: 🔥 Fire (≥48) · ✅ Good (≥36) · ⚠️ Weak (<36)

## Content Rules

- Arabic angles consistently score higher on Cultural Relevance (9-10 vs 3-6 for EN)
- Cliché blocklist in `ai_orchestrator.py` — expand after every live run
- Gulf-specific psych triggers in `psychology.py` (6 types)
- EN angles must reference Saudi/Gulf entities (Aramco, NEOM, stc, Vision 2030)

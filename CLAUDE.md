# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered autonomous marketing agent that discovers trends, generates psychologically-engineered content angles, and delivers reports — focused on the Saudi/Gulf market. Runs twice-daily via GitHub Actions.

## Commands

```bash
# Install dependencies (Python 3.13 required)
uv sync

# Lint / format
uv run ruff check src/
uv run ruff format src/

# Run CLI commands
marketing-agent scan [--mock] [--max 8]
marketing-agent generate [--mock] [--max-trends 8] [--angles 3] [--provider gemini|claude|lmstudio]
marketing-agent video [--mock] [--max-trends 4] [--angles 3] [--pick 0]
marketing-agent upload path/to/brand.pdf [--name "Brand Name"]
marketing-agent serve [--host 0.0.0.0] [--port 8000]

# Run benchmark (no API calls)
uv run python run_benchmark.py --mode mock --no-judge

# GitHub Actions entrypoint
uv run python scripts/run_and_report.py
```

There is no test suite yet — verification is done via `--mock` flags or live runs.

## Architecture

**Pipeline flow:**

```
Trend Scanner → Psychology Engine → AI Orchestrator → Benchmark → Report/Delivery
                                                               ↘ Video Converter (optional)
```

**Core modules in `src/`:**

| File | Responsibility |
|------|---------------|
| `pipeline.py` | Orchestrates the full trend→angles flow |
| `trend_scanner.py` | Discovers trends via Tavily, Google Trends, YouTube |
| `yt_scanner.py` | YouTube-specific: transcripts, Data API v3, yt-dlp |
| `psychology.py` | 6 psychological trigger types with Gulf-specific templates; cliché detection |
| `ai_orchestrator.py` | Routes to Gemini (default), Claude, or LM Studio; generates 3 angle formats per trend |
| `benchmark.py` | 6-dimension scoring (0–60); grades: 🔥 Fire (≥48), ✅ Good (≥36), ⚠️ Weak (<36) |
| `brand_ingestion.py` | Uploads brand PDFs → ChromaDB vector store |
| `video_converter.py` | Converts top angle → Remotion-compatible JSON for YouTube Shorts |
| `report_writer.py` | Outputs MD/HTML/JSON reports and Telegram-formatted text |
| `telegram_bot.py` | Send-only Telegram integration with 4096-char chunking |
| `source_manager.py` | Reads `sources/*.csv` — edit in Excel, no code changes needed |
| `config.py` | Pydantic settings loaded from `.env` (falls back to `/tmp/.marketing-agent.env`) |
| `models.py` | Core Pydantic models: `Trend`, `ContentAngle`, `BrandProfile`, `AgentOutput` |
| `cli.py` | Typer CLI entry point |
| `api.py` | FastAPI REST endpoints |

**Three content angle formats generated per trend:**
1. **Micro-story** — Character-driven narrative with unresolved tension
2. **Data Provocateur** — Surprising stat + contrarian take
3. **Cultural Connector** — Arabic idiom + local context (includes Arabic text)

**Video output** targets Saudi colloquial Arabic (عامية), 5–6 mandatory scenes (hook → intro → point → list → CTA), and outputs JSON for a Remotion TypeScript renderer.

## Key Configuration

Required environment variables (see `.env.example`):
- `GOOGLE_API_KEY` — Gemini (primary AI provider)
- `ANTHROPIC_API_KEY` — Claude fallback
- `TAVILY_API_KEY` — Web trend search
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — Delivery

Optional:
- `YOUTUBE_DATA_API_KEY` — Falls back to `GOOGLE_API_KEY`

## Sources

`sources/saudi_general.csv` and `sources/youtube_channels.csv` drive trend discovery. Add/remove sources by editing the CSVs directly — no code changes required.

## Automation

- `.github/workflows/scheduled_run.yml` — Cron at 03:00 UTC and 15:00 UTC (6 AM & 6 PM Cairo)
- `.github/workflows/telegram_command.yml` — Webhook for manual triggers

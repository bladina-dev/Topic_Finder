# Marketing Agent — Autonomous Gulf/KSA Content Engine

An AI agent that scans trends (Tavily, YouTube, Google Trends), applies Gulf-specific psychological triggers, and generates Arabic/English content angles scored across 6 quality dimensions. Runs on a schedule via GitHub Actions — no server required.

**Current version:** v0.3.0 · **Next:** v0.4.0 in progress

---

## Features

| Feature | Details |
|---------|---------|
| Trend Scanning | Tavily (general + targeted domains), YouTube channels + KSA trending |
| AI Generation | Gemini 2.5 Flash (primary), Claude Sonnet (fallback), LM Studio (local) |
| Psych Triggers | 6 Gulf-specific triggers: FOMO, Zeigarnik, Curiosity Gap, Loss Aversion, Social Proof, Gain |
| Cultural Context | Auto-injects Ramadan, Eid, Riyadh Season, Vision 2030, Saudi work week |
| Quality Benchmark | 6-dimension AI judge: CN / TD / VM / BA / CR / HP (max 60) |
| Delivery | Telegram bot (@Trendozer_bot) — 🔥/✅/⚠️ graded reports |
| Scheduling | GitHub Actions cron — 6 AM + 6 PM Cairo/Riyadh |
| Source Management | CSV-based — editable in Excel, no code needed |

---

## Quick Start

```bash
# Install
uv sync

# Test (no API calls)
uv run python run_benchmark.py --mode mock --no-judge

# Live run
uv run python run_benchmark.py --mode live --trends 4 --angles 3

# Full pipeline + Telegram report
uv run python scripts/run_and_report.py
```

## Configuration

```bash
cp .env.example .env
```

Required keys:
```env
GOOGLE_API_KEY=        # Gemini generation + YouTube Data API
TAVILY_API_KEY=        # Trend scanning
TELEGRAM_BOT_TOKEN=    # @Trendozer_bot
TELEGRAM_CHAT_ID=      # Delivery target
```

Optional:
```env
ANTHROPIC_API_KEY=     # Claude fallback provider
YOUTUBE_DATA_API_KEY=  # YouTube trending KSA (falls back to GOOGLE_API_KEY)
GOOGLE_TRENDS_ENABLED= # false by default (pytrends SA endpoint broken as of March 2026)
```

---

## CLI Commands

```bash
uv run marketing-agent generate --sources saudi_general   # Generate angles from CSV source list
uv run marketing-agent sources list                       # Show available CSV source files
uv run marketing-agent sources add path/to/sources.csv    # Add a new source file
uv run marketing-agent report                             # Generate + benchmark + save + send to Telegram
uv run marketing-agent run                                # Full pipeline (same as GitHub Actions)
```

---

## Project Structure

```
src/
  pipeline.py           — scan → generate → benchmark orchestration
  trend_scanner.py      — Tavily, targeted CSV, Google Trends (optional)
  yt_scanner.py         — YouTube channel scan + KSA trending (YouTube Data API v3)
  ai_orchestrator.py    — multi-provider generation (Gemini / Claude / LM Studio)
  benchmark.py          — 6-dimension scoring + cliché detection
  source_manager.py     — CSV source management
  report_writer.py      — MD / HTML / JSON / Telegram output
  telegram_bot.py       — send-only bot (@Trendozer_bot)
  config.py             — Pydantic Settings
  cli.py                — Typer CLI entry point
  api.py                — FastAPI server

sources/                — CSV source lists (edit in Excel/Sheets)
  saudi_general.csv     — 100 Saudi/Gulf sources across 10 verticals
  youtube_channels.csv  — 30 KSA/Gulf YouTube channels

scripts/run_and_report.py  — GitHub Actions entrypoint
.github/workflows/
  scheduled_run.yml     — cron: 03:00 + 15:00 UTC (6AM + 6PM Cairo)
  telegram_command.yml  — /today, /sources, /status via Telegram webhook
```

---

## Scoring System

Each angle is judged across 6 dimensions (0–10 each, max 60):

| Code | Dimension | What it measures |
|------|-----------|-----------------|
| CN | Creative Novelty | Fresh angle vs. cliché |
| TD | Psych Trigger Depth | Does the trigger create a real reaction? |
| VM | Viral Mechanics | Would people share/save/screenshot? |
| BA | Brand Alignment | Coherent brand voice |
| CR | Cultural Relevance | KSA/Gulf resonance (0=Western, 10=deeply local) |
| HP | Hook Power | First sentence scroll-stop power |

**Grades:** 🔥 Fire (≥48, ready to post) · ✅ Good (≥36, needs polish) · ⚠️ Weak (<36, skip)

**Live benchmark results (2026-03-17):** avg 39.9/60 (🟡 B), top angle 49/60

---

## Roadmap

| Version | Status | Focus |
|---------|--------|-------|
| v0.1.0 | ✅ Done | Core pipeline: Tavily + Gemini + benchmark |
| v0.2.0 | ✅ Done | CSV sources, Telegram, GitHub Actions |
| v0.3.0 | ✅ Done | YouTube scanner (yt-dlp + YouTube Data API v3) |
| v0.4.0 | 🔄 In progress | google.genai migration, parse fixes, cliché expansion |
| v0.5.0 | Planned | Predictive trend scoring, memory/learning layer |

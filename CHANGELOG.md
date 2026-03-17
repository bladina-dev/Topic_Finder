# Changelog

All notable changes to the Marketing Agent project.

## [0.4.0] — 2026-03-17

### Fixed
- **`src/ai_orchestrator.py`** — Migrated from deprecated `google.generativeai` to `google.genai` SDK
  - Replaced `genai.configure()` + `GenerativeModel` with `genai.Client` + `client.models.generate_content()`
  - Fixed Claude model ID: `claude-sonnet-4-20250514` → `claude-sonnet-4-6`
  - Improved JSON parse error handling: strips ` ```json ` language tags, logs raw response on failure
- **`src/trend_scanner.py`** — Google Trends gated behind `google_trends_enabled` flag (defaults `False`) — eliminates 404 retry spam
- **`pyproject.toml`** — Version bumped to `0.3.0`, replaced `google-generativeai` dep with `google-genai>=1.0.0`

### Changed
- **`src/ai_orchestrator.py`** — Expanded banned cliché patterns in `ANGLE_GENERATION_PROMPT` (+14 EN + AR patterns observed in live runs)
- **`src/benchmark.py`** — Expanded `CLICHE_PATTERNS_EN` (+8) and `CLICHE_PATTERNS_AR` (+7) with patterns confirmed in live output
- **`src/config.py`** — Added `google_trends_enabled: bool = False`

### Added
- **`AGENT.md`** — Claude Code context file for this repo
- **`docs/v0.4.0-plan.md`** — This version's implementation plan

## [0.3.0] — 2026-03-14

### Added — YouTube Scanner (3 free tools)
- **`src/yt_scanner.py`** — YouTube scanning engine with two functions:
  - `scan_youtube_sources()` — scans known channels via `yt-dlp` + `youtube-transcript-api`, extracts marketing insights using Gemini Flash
  - `scan_trending_ksa()` — discovers trending videos in Saudi Arabia by category using **YouTube Data API v3**, calculates view velocity and engagement scoring
- **`sources/youtube_channels.csv`** — 30 Saudi/Gulf YouTube channels across verticals (tech, finance, entertainment, lifestyle, news)
- `published_at` and `source_name` fields added to `Trend` model — every trend now carries its original publication date and source attribution
- Date parsing helper `_parse_date()` and URL domain extraction across all scanners
- All reports (Telegram, Markdown, HTML, JSON) now display **source links** (🔗) and **publish dates** (📅) per trend
- Dependencies: `yt-dlp`, `youtube-transcript-api`, `google-api-python-client`

### Changed
- `src/models.py` — `Trend` model extended with `published_at: Optional[datetime]` and `source_name: str`
- `src/trend_scanner.py` — Tavily, targeted, and Google Trends scanners enriched with `published_at`, `source_name`, and `url`
- `src/report_writer.py` — added `_relative_time()`, `_short_domain()` helpers; Telegram/Markdown/HTML/JSON formats now include trend provenance
- `src/config.py` — added `youtube_scan_enabled`, `youtube_max_per_channel`, `youtube_sources`, `youtube_data_api_key`
- `.env.example` — added YouTube configuration variables

## [0.2.0] — 2026-03-14

### Added — Team-Friendly Features
- **`src/source_manager.py`** — CSV-based source management (load, list, filter, add)
- **`src/report_writer.py`** — simplified 🔥/✅/⚠️ scoring + MD/HTML/JSON reports
- **`src/telegram_bot.py`** — send-only Telegram bot (`@Trendozer_bot`)
- **`scripts/run_and_report.py`** — standalone entrypoint for GitHub Actions
- **`sources/saudi_general.csv`** — 100 Saudi/Gulf data sources across 10 verticals
- **`docs/v0.0.2-plan.md`** — feature plan documentation
- **`.github/workflows/scheduled_run.yml`** — twice daily at 6AM + 6PM Cairo
- **`.github/workflows/telegram_command.yml`** — `/today`, `/sources`, `/status` webhook commands

### Changed
- `src/models.py` — added `TrendSource.TARGETED`, `TrendSource.YOUTUBE`, `SourceEntry` model with `youtube_handle`
- `src/config.py` — added telegram, reports, sources, schedule settings
- `src/trend_scanner.py` — targeted scanning, Google Trends retry with backoff, emoji-aware dedup
- `pyproject.toml` — version 0.2.0, new deps (tenacity, python-telegram-bot)
- `.gitignore` — added reports/ and brand_data/

## [0.1.0] — 2026-03-09

### Added — Initial Release
- Core trend scanning with Tavily + Google Trends
- AI orchestration with Gemini/Claude for angle generation
- 6-dimension benchmark scoring (CN/TD/VM/BA/CR/HP)
- ChromaDB brand memory
- Basic CLI interface

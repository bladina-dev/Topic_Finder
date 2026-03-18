# Topic Finder — Autonomy & Robustness Backlog

**Written:** 2026-03-18
**Written by:** Claude Code (Sonnet 4.6) after full codebase audit
**Last updated:** 2026-03-18 — re-verified after `git pull` (pulled commits: `c2de444`, `f8d0311`)
**Status:** Awaiting agent review + Mohamed approval before implementation

---

## Instructions for the Agent Reading This

1. **Before presenting anything to Mohamed — verify each item is still relevant.**
   Check the actual file and line numbers listed. If the issue is already fixed, mark it `✅ RESOLVED` and skip it.

2. **Group remaining items by priority and present them as a numbered approval list.**
   Do NOT start coding. Wait for Mohamed to say "approve X" or "approve all" or "skip X".

3. **After approval, follow Superpowers workflow:**
   Antigravity plans → Claude CLI builds → Antigravity reviews.
   Each item below maps to one implementation phase.

4. **Update this file after each item is completed** — mark it `✅ DONE` with the date.

---

## ⚠️ URGENT — Fix Before Next Run (Added 2026-03-18 post-pull)

### [URGENT-A] Schedule progression plan — 3 phases ✅ INTENTIONAL
**Status:** `✅ PHASE 1 ACTIVE — every 5 min for testing`
**Decision by Mohamed:** 2026-03-18

| Phase | Schedule | Cron | Runs/day | When to move |
|-------|----------|------|----------|-------------|
| **Phase 1 (now)** | Every 5 min | `*/5 * * * *` | 288 | Once pipeline is stable end-to-end |
| **Phase 2** | 10× per day | `0 4,6,8,10,12,14,16,18,20,22 * * *` | 10 | Once content quality is consistently good |
| **Phase 3** | 4× per day | `0 3,9,15,21 * * *` | 4 | Production steady state (6AM, 12PM, 6PM, 12AM Cairo) |

**Note for agents:** Do NOT revert the 5-minute schedule. It is intentional for testing. When Mohamed says "move to Phase 2", update the cron to `0 4,6,8,10,12,14,16,18,20,22 * * *`. When he says "move to Phase 3", use `0 3,9,15,21 * * *`.

---

### [URGENT-B] New files (music, voiceover, video_assembler) missing from workflow env
**Status:** `✅ DONE 2026-03-18` — Added AZURE_SPEECH_KEY + AZURE_SPEECH_REGION to scheduled_run.yml
**What happened:** Recent commits added `music_generator.py` (MiniMax API) and `voiceover.py` (ElevenLabs API) but their API keys are **not in `.github/workflows/scheduled_run.yml`** env section.
**Missing keys:**
```yaml
MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
```
Without these, both services silently fall back (music uses a static file, voiceover returns a path that doesn't exist). The pipeline "succeeds" but produces broken video output.

---

### [URGENT-C] New files have the same critical gaps as the rest of the codebase
**Status:** `✅ DONE 2026-03-18`
These files were added after our original audit and have identical problems:

| File | Issue |
|------|-------|
| `src/music_generator.py` | No retry, no timeout on httpx MiniMax call |
| `src/voiceover.py` | No retry, no timeout on httpx ElevenLabs call |
| `src/scheduler.py` | Bare `except Exception: print()` — silent failure, no alert |
| `src/video_assembler.py` | `subprocess` ffmpeg with no timeout |

These must be included in P1 retry/logging fixes.

---

## Priority 1 — Critical (Silent Failures & Fake Data)

### [P1-A] Retry logic on all external API calls
**Status:** `⏳ NOT DONE`
**Why it matters:** Any network blip or rate limit causes permanent failure. GitHub Actions jobs silently succeed with zero content generated.
**Files to fix:**
- `src/ai_orchestrator.py:258-277` — add exponential backoff around Gemini, Claude, LM Studio calls
- `src/trend_scanner.py:145-153, 184-244` — add retry on Tavily requests
- `src/telegram_bot.py:51-61` — add retry on 429 and 5xx responses
- `src/yt_scanner.py:33-40` — add retry on transcript fetch

**How to implement:** Use `tenacity` library — `@retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(3))`. Already in Python ecosystem, no new dep needed if added to pyproject.toml.

---

### [P1-B] Stop fake `[Parse Error]` angles reaching Telegram
**Status:** `⏳ NOT DONE`
**Why it matters:** When Gemini returns malformed JSON, a fake `ContentAngle` with headline `"[Parse Error]"` is created, benchmarked, scored, and sent to Telegram as real content.
**Files to fix:**
- `src/ai_orchestrator.py:310-324` — raise exception instead of returning fake angle; let pipeline skip and log
- `src/benchmark.py:394-395` — on judge failure, mark angle as `unscored` not neutral 5s; exclude from final report

---

### [P1-C] Telegram alert when pipeline fails
**Status:** `⏳ NOT DONE`
**Why it matters:** `scripts/run_and_report.py:80-86` tries to send a failure Telegram message but catches and ignores the exception. Mohamed has no way to know the pipeline failed.
**Files to fix:**
- `scripts/run_and_report.py:80-89` — use a minimal bare `httpx.post()` (no async, no wrapper) for failure notification so it cannot fail silently
- Add a dead-simple function `send_failure_alert(error: str)` that bypasses all pipeline state

---

### [P1-D] Add timeouts to every external call
**Status:** `⏳ NOT DONE`
**Why it matters:** Hanging requests freeze the GitHub Actions job until the 15-min global timeout kills it — wasting all API quota spent before the hang.
**Files to fix:**
- `src/trend_scanner.py:148-152` — add `timeout=30` to Tavily client
- `src/ai_orchestrator.py:180-186` — add `request_options={"timeout": 60}` to Gemini call
- `src/yt_scanner.py:50-74` — add `timeout=20` to transcript fetch

---

## Priority 2 — High (Breaks Autonomous Operation)

### [P2-A] Replace all `print()` with structured logging
**Status:** `⏳ NOT DONE`
**Why it matters:** Entire codebase uses `print()` only. No timestamps, no log levels, no tracebacks. Post-mortem debugging of GitHub Actions failures is blind.
**Files to fix:** All files in `src/` + `scripts/run_and_report.py`
**How:** Use Python standard `logging` module. One `logger = logging.getLogger(__name__)` per file. Configure in `config.py` with level from env var `LOG_LEVEL=INFO`.

---

### [P2-B] GitHub Actions hardening
**Status:** `⏳ NOT DONE`
**Why it matters:** Two scheduled cron jobs can collide. No failure notification. Secrets not validated before running.
**Files to fix:**
- `.github/workflows/scheduled_run.yml` — add:
  ```yaml
  concurrency:
    group: topic-finder-pipeline
    cancel-in-progress: false
  ```
  Add a secret validation step before running pipeline:
  ```yaml
  - name: Validate secrets
    run: |
      [ -n "${{ secrets.GOOGLE_API_KEY }}" ] || (echo "Missing GOOGLE_API_KEY" && exit 1)
      [ -n "${{ secrets.TAVILY_API_KEY }}" ] || (echo "Missing TAVILY_API_KEY" && exit 1)
      [ -n "${{ secrets.TELEGRAM_BOT_TOKEN }}" ] || (echo "Missing TELEGRAM_BOT_TOKEN" && exit 1)
  ```
  Add `timeout-minutes: 10` per step.

---

### [P2-C] Startup validation — check all APIs before pipeline runs
**Status:** `⏳ NOT DONE`
**Why it matters:** Config loads empty strings as valid. Failures are discovered mid-pipeline after quota has been spent.
**Files to fix:**
- `src/config.py` — add `validate()` method that checks each required key is non-empty and raises `ConfigError` with a clear message listing what's missing
- `scripts/run_and_report.py` — call `settings.validate()` as first step before any API calls

---

### [P2-D] Pipeline checkpoint — save state after scan step
**Status:** `⏳ NOT DONE`
**Why it matters:** If pipeline crashes at benchmark or report step, all Tavily + Gemini quota spent on scan+generate is wasted. Next run starts from scratch.
**How:** After `scan_trends()` returns, save results to `output/checkpoint-{date}.json`. At pipeline start, check if checkpoint exists from same day and load it instead of re-scanning.
**Files to fix:**
- `scripts/run_and_report.py` — add checkpoint save/load around scan step

---

## Priority 3 — Medium (Quality & Reliability)

### [P3-A] Fix silent YouTube video drops
**Status:** `⏳ NOT DONE`
**Why it matters:** `yt_scanner.py:127-129` returns `None` on failure and pipeline silently skips videos with nothing logged.
**Fix:** Log dropped videos to `output.errors` with reason. Surface count in Telegram report footer: "⚠️ 3 videos skipped (transcript unavailable)".

---

### [P3-B] Clean up disabled Google Trends code
**Status:** `⏳ NOT DONE`
**Why it matters:** `google_trends_enabled = False` but `pytrends` still imported and conditional logic still runs.
**Fix:** Remove `pytrends` from `pyproject.toml`, remove import, remove `scan_google_trends()` calls entirely. Add a comment: `# Google Trends removed 2026-03 — API returns 404. Revisit with alternative library.`

---

### [P3-C] Thread-safe API state + ChromaDB caching
**Status:** `⏳ NOT DONE`
**Why it matters:** `api.py:45` `_latest_output` is not thread-safe. `brand_ingestion.py` creates a new ChromaDB client on every call.
**Fix:** Wrap `_latest_output` with `asyncio.Lock()`. Cache ChromaDB client as a module-level singleton.

---

### [P3-D] Validate + escape trend titles in reports
**Status:** `⏳ NOT DONE`
**Why it matters:** Trend titles containing `|` break the markdown table in reports.
**Fix:** `report_writer.py` — escape `|` as `\|` and strip control characters from all trend titles before inserting into markdown.

---

### [P3-E] Add tests for critical pipeline paths
**Status:** `⏳ NOT DONE`
**Why it matters:** No tests exist for `pipeline.py`, `ai_orchestrator.py`, `benchmark.py`, `telegram_bot.py`, or `run_and_report.py`. Regressions ship undetected.
**Minimum viable test coverage:**
- `test_pipeline.py` — mock scan + generate + benchmark, assert output structure
- `test_ai_orchestrator.py` — test parse error handling (fake JSON input → no fake angle returned)
- `test_telegram_bot.py` — mock httpx, assert retry on 429
- `test_run_and_report.py` — assert failure alert is sent when pipeline raises

---

## What Was Fixed in the Pulled Commits (Do NOT re-implement)

| Commit | Fix |
|--------|-----|
| `c2de444` | `.env` loading in CLI via `python-dotenv` — minor but useful |
| `f8d0311` | Schedule change (this one is wrong — see URGENT-A above) |

## What Is Already Done (Do NOT re-implement)

These were fixed in v0.4.0 (check `CHANGELOG.md` to confirm):

| Item | Fixed in |
|------|---------|
| `google.generativeai` → `google.genai` migration | v0.4.0 |
| Angle parse error (JSON code fence stripping) | v0.4.0 |
| Google Trends disabled via config flag | v0.4.0 |
| Claude model ID updated to `claude-sonnet-4-6` | v0.4.0 |
| Cliché blocklist expanded (EN + AR) | v0.4.0 |

If any of the above are NOT in the codebase when you read this, add them back to the active list.

---

## Agent Presentation Template

When presenting to Mohamed, use this format:

```
📋 Topic Finder Autonomy Backlog — [today's date]

I pulled the latest from GitHub (2 new commits). Here's the full picture:

📅 SCHEDULE STATUS (do not change without Mohamed's instruction):
  [URGENT-A] Every 5 min = Phase 1 testing. INTENTIONAL. Do not revert.
             Phase 2 target: 10×/day → cron: 0 4,6,8,10,12,14,16,18,20,22 * * *
             Phase 3 target: 4×/day  → cron: 0 3,9,15,21 * * *
  [URGENT-B] MiniMax + ElevenLabs API keys missing from GitHub Actions env — video pipeline silent fails
  [URGENT-C] New files (music_generator, voiceover, scheduler) have same retry/logging gaps

🔴 CRITICAL (causes silent failures in production):
  [P1-A] Retry logic — all external API calls crash on first error (now includes new music/voiceover files)
  [P1-B] Fake [Parse Error] angles reaching Telegram as real content
  [P1-C] Pipeline failure alert silently swallowed — you never know when it fails
  [P1-D] No timeouts — hanging requests freeze the GitHub Actions job

🟠 HIGH (breaks autonomous operation):
  [P2-A] No structured logging — blind to failures in GH Actions
  [P2-B] GitHub Actions: no concurrency lock, no failure notification, no secret validation step
  [P2-C] No startup validation — bad config only discovered mid-pipeline
  [P2-D] No checkpoint — crash loses all API quota spent on scan step

🟡 MEDIUM (quality & reliability):
  [P3-A] YouTube drops silently (no logging, no report footer)
  [P3-B] Google Trends disabled but pytrends still imported
  [P3-C] Thread-safe state + ChromaDB caching
  [P3-D] Markdown table breaks on pipe characters in titles
  [P3-E] No tests for pipeline, orchestrator, benchmark, telegram

My recommendation:
  1. Fix URGENT-A right now (1 line change, no approval needed — it's clearly an accident)
  2. Then approve P1 + URGENT-B/C together as one implementation phase

Say "fix urgent" to start with URGENT-A, or "approve all" to do everything.
```

---

## Notes

- Each Priority group is designed to be one Superpowers phase (30–60 min).
- P1 can be implemented together as one phase — all are retry/error handling patterns.
- P2-A (logging) should be done before or alongside P1 so failures are visible during testing.
- Do NOT implement P3-E tests before P1+P2 are done — tests on broken code waste time.
- After P1+P2 are done, run a live benchmark and compare error rate to baseline (`live_run_output.txt`).

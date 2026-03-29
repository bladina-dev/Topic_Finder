# Notion Database Integration — Push Angles Automatically

**Date:** 2026-03-18 | **Repo:** `~/Documents/antigravity/marketing-agent/`
**Prereqs:** Pipeline runs successfully, `NOTION_API_KEY` in `.env`

---

## Critical Warnings

| Warning | Fix |
|:---|:---|
| W1: UV cache | Use `UV_CACHE_DIR=/tmp/uv-cache` prefix if cache errors |
| W2: Never `git add -A` | Stage specific files only |
| W3: No notion-client package | Use `httpx` REST calls directly — do NOT install the notion Python SDK |
| W4: API key optional | If `NOTION_API_KEY` is not set, skip Notion sync silently |
| W5: Never crash pipeline | Notion failures must be caught and logged, never crash the main pipeline |

---

## The Prompt

```
Read ~/Documents/antigravity/marketing-agent/src/models.py and ~/Documents/antigravity/marketing-agent/scripts/run_and_report.py. Add Notion database sync to the marketing agent pipeline. Create ~/Documents/antigravity/marketing-agent/src/notion_sync.py — a module that pushes generated ContentAngle objects to a Notion database after each pipeline run. Use the Notion REST API directly with httpx (do NOT install any notion Python SDK): all requests go to https://api.notion.com/v1/ with headers {"Authorization": "Bearer {NOTION_API_KEY}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}. The module needs three functions: (1) ensure_database(parent_page_id: str) -> str — checks if a database named "Marketing Agent Angles" already exists under the parent page by calling GET /v1/blocks/{parent_page_id}/children and looking for a child_database with matching title, if not found creates one via POST /v1/databases with these properties: Headline (title), Hook (rich_text), Trend (rich_text), Source (select with options: twitter_ksa, gulf_news, google_trends, youtube, cultural, targeted), Platform (select with options: twitter, instagram, linkedin, tiktok, general), Triggers (multi_select with options: zeigarnik, fomo, curiosity_gap, social_proof, gain, loss_aversion), Score (number, format: percent), Grade (select with options: Fire, Good, Weak), Date (date), Status (select with options: New, Approved, Published, Skipped, default: New), returns the database_id. (2) push_angles(output: AgentOutput, benchmark_results: list[dict] | None = None) -> int — iterates through output.results, for each TrendWithAngles iterates its angles, creates a Notion page per angle with all properties mapped, returns the count pushed. For the Grade property, use the same logic as report_writer.py simplified_grade: score >= 48 is Fire, >= 36 is Good, else Weak. If benchmark_results exist, find the matching result for each angle by headline to get the total score. (3) _create_angle_page(database_id: str, angle: ContentAngle, trend: Trend, grade: str, total_score: float) -> bool — makes POST /v1/pages with parent database_id and properties mapped from the angle and trend objects, returns True on success. Add NOTION_API_KEY and NOTION_PARENT_PAGE_ID to ~/Documents/antigravity/marketing-agent/src/config.py Settings class as notion_api_key: str = "" and notion_parent_page_id: str = "". Also add notion_database_id: str = "" for caching the database ID after first creation. Add these same three variables to ~/Documents/antigravity/marketing-agent/.env with NOTION_API_KEY=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 and NOTION_PARENT_PAGE_ID= (empty, user will fill in) and NOTION_DATABASE_ID= (empty, auto-populated). Modify ~/Documents/antigravity/marketing-agent/scripts/run_and_report.py to add Step 5 after the Telegram step: if settings.notion_api_key and settings.notion_parent_page_id are both set, import push_angles and ensure_database from src.notion_sync, call ensure_database to get or create the database, then call push_angles with the output and benchmark_results, print the count, wrap everything in try/except so Notion failures never crash the pipeline, just print a warning. Add NOTION_API_KEY, NOTION_PARENT_PAGE_ID, and NOTION_DATABASE_ID to ~/Documents/antigravity/marketing-agent/.github/workflows/scheduled_run.yml env section pulling from secrets. Make all httpx calls async with timeout=30. Print progress: "[Notion] Checking database...", "[Notion] Database ready: {db_id}", "[Notion] Pushing {n} angles...", "[Notion] Done: {count} angles synced to Notion". Run "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/notion_sync.py scripts/run_and_report.py". IMPORTANT GIT SAFETY: never use git add -A. Stage with "git add src/notion_sync.py src/config.py scripts/run_and_report.py .github/workflows/scheduled_run.yml .env" and commit "feat: add Notion database sync for marketing angles".
```

---

## Validation After Running

```bash
# Lint clean
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/notion_sync.py scripts/run_and_report.py

# Full pipeline with Notion sync (needs NOTION_API_KEY + NOTION_PARENT_PAGE_ID in .env)
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_and_report.py

# Verify in Notion: open your workspace and check for "Marketing Agent Angles" database
```

---

## After This Phase

The pipeline will be: **Trends → Angles → Benchmark → Reports → Telegram → Notion Database**

Each angle appears as a row in Notion with: Headline, Hook, Trend source, Platform, Psychology Triggers, Score, Grade (Fire/Good/Weak), Date, and Status (New/Approved/Published/Skipped).

Agencies can review angles in Notion, change Status from "New" to "Approved", and use the database as a content calendar.

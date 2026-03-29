# Notion Feedback Loop — AI Learns From Your Reviews

**Date:** 2026-03-18 | **Repo:** `~/Documents/antigravity/marketing-agent/`
**Prereqs:** Notion sync working (phase_notion_sync done), angles exist in Notion database

---

## Critical Warnings

| Warning | Fix |
|:---|:---|
| W1: UV cache | Use `UV_CACHE_DIR=/tmp/uv-cache` prefix if cache errors |
| W2: Never `git add -A` | Stage specific files only |
| W3: No notion-client package | Use `httpx` REST calls directly — reuse the existing pattern in src/notion_sync.py |
| W4: Never crash the pipeline | All Notion reads must be wrapped in try/except, returning empty patterns on failure |

---

## The Prompt

```
Read ~/Documents/antigravity/marketing-agent/src/notion_sync.py and ~/Documents/antigravity/marketing-agent/src/ai_orchestrator.py and ~/Documents/antigravity/marketing-agent/src/pipeline.py. Add a Notion feedback loop so the AI learns from the user's reviews. The idea: after the user changes the "Status" column in Notion from "New" to "Approved" or "Skipped", the next pipeline run reads those decisions and feeds them into the Gemini prompt as context. Add two new functions to src/notion_sync.py: (1) fetch_feedback(database_id: str) -> dict — queries the Notion database for all pages where Status is "Approved" or "Skipped" using POST /v1/databases/{database_id}/query with a filter {"or": [{"property": "Status", "select": {"equals": "Approved"}}, {"property": "Status", "select": {"equals": "Skipped"}}]}. Returns a dict with two keys: "approved" (list of dicts with headline, hook, trend, triggers, platform) and "skipped" (same structure). Limit to the last 50 results sorted by Date descending so we get recent feedback only. (2) format_feedback_prompt(feedback: dict) -> str — converts the feedback dict into a natural language prompt section like: "LEARNING FROM PAST REVIEWS: The client APPROVED these types of angles: [list the approved headlines, hooks, and which psychology triggers they used]. The client SKIPPED these types of angles: [list the skipped ones]. INSTRUCTIONS: Generate new angles that match the patterns of APPROVED angles. Avoid patterns similar to SKIPPED angles." If both lists are empty, return an empty string (no feedback yet). Modify src/pipeline.py run_pipeline function: before the angle generation loop, check if settings.notion_api_key and settings.notion_database_id are both set, if so call fetch_feedback to get past decisions, then call format_feedback_prompt to get a feedback_context string. Pass this feedback_context string to generate_angles_for_trend as a new optional parameter. Modify src/ai_orchestrator.py generate_angles_for_trend function: add an optional feedback_context: str = "" parameter. If feedback_context is not empty, append it to the prompt that gets sent to Gemini/Claude, right before the "Generate {angles_count} content angles" instruction. This way the AI sees what the user liked and disliked before generating new angles. Add a print statement in pipeline.py: "[Pipeline] Loaded feedback: {n_approved} approved, {n_skipped} skipped patterns" or "[Pipeline] No Notion feedback yet (all angles still 'New')" if empty. Make all httpx calls async with timeout=15. Run "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/notion_sync.py src/pipeline.py src/ai_orchestrator.py". IMPORTANT GIT SAFETY: never use git add -A. Stage with "git add src/notion_sync.py src/pipeline.py src/ai_orchestrator.py" and commit "feat: add Notion feedback loop — AI learns from approved/skipped angles".
```

---

## How It Works

```
Pipeline Run N:
  1. Scan trends
  2. READ Notion → "User approved 5 loss-aversion hooks, skipped 3 generic stats angles"
  3. Feed patterns into Gemini prompt
  4. Generate angles (now biased toward what user likes)
  5. Push new angles to Notion with Status="New"

User reviews in Notion:
  - Marks 3 angles "Approved" ✅
  - Marks 2 angles "Skipped" ❌

Pipeline Run N+1:
  - Reads updated feedback → AI adjusts even further
  - Self-improving cycle continues
```

---

## Validation After Running

```bash
# Lint clean
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/notion_sync.py src/pipeline.py src/ai_orchestrator.py

# Run pipeline — should show feedback loading
cd ~/Documents/antigravity/marketing-agent
uv run python scripts/run_and_report.py

# Expected output (first time, no reviews yet):
# [Pipeline] No Notion feedback yet (all angles still 'New')

# Then go to Notion, mark some angles as "Approved" or "Skipped", run again:
# [Pipeline] Loaded feedback: 3 approved, 2 skipped patterns
```

---

## After This Phase

The pipeline becomes **self-improving**: Trends → **Read Notion feedback** → Angles (biased by feedback) → Reports → Telegram → Notion

The more you review in Notion, the better the AI gets at matching your taste.

# Obsidian Vault Integration — Angles as Markdown + Feedback Loop

**Date:** 2026-03-18 | **Repo:** `~/Documents/antigravity/marketing-agent/`
**Prereqs:** Pipeline runs successfully, Obsidian installed on Mac

---

## Critical Warnings

| Warning | Fix |
|:---|:---|
| W1: UV cache | Use `UV_CACHE_DIR=/tmp/uv-cache` prefix if cache errors |
| W2: Never `git add -A` | Stage specific files only |
| W3: No external deps | This is pure file I/O — no new packages needed |
| W4: Never crash the pipeline | All file reads/writes must be wrapped in try/except |
| W5: YAML frontmatter | Use PyYAML (already available via pydantic) for frontmatter parsing |

---

## The Prompt

```
Read ~/Documents/antigravity/marketing-agent/src/models.py and ~/Documents/antigravity/marketing-agent/scripts/run_and_report.py and ~/Documents/antigravity/marketing-agent/src/pipeline.py and ~/Documents/antigravity/marketing-agent/src/ai_orchestrator.py and ~/Documents/antigravity/marketing-agent/src/config.py. Replace the Notion sync with a local Obsidian vault that saves angles as markdown files and reads feedback from YAML frontmatter. Create ~/Documents/antigravity/marketing-agent/src/obsidian_sync.py with these functions: (1) ensure_vault() -> Path — creates the vault directory at the path from settings.obsidian_vault_path (default: ./obsidian-vault), creates subfolders "angles" and ".obsidian" (so Obsidian recognizes it as a vault), returns the vault path. (2) push_angles(output, benchmark_results=None) -> int — iterates through output.results, for each TrendWithAngles iterates its angles, calls _write_angle_file for each, returns count written. (3) _write_angle_file(vault_path, angle, trend, grade, total_score) -> bool — writes a markdown file to vault_path/angles/ with filename format "{date}_{trend_slug}_{n}.md" where date is YYYY-MM-DD, trend_slug is the trend title lowercased with spaces replaced by hyphens truncated to 40 chars, n is an incrementing counter. The file content must have YAML frontmatter delimited by --- markers with these fields: status (default "new"), grade (fire/good/weak using the same logic as report_writer.py simplified_grade), trend (trend title), source (trend source value), platform (angle platform value), triggers (list of trigger type values from angle.psych_triggers), score (brand_alignment_score as float), total_score (benchmark total or 0), date (today ISO format), headline (the angle headline). After the frontmatter, write the angle content as markdown: an h1 with the headline, a blockquote with the hook, an h2 "Body Outline" with the body_outline, an h2 "Psychology Triggers" listing each trigger with its hook and rationale. (4) fetch_feedback(vault_path) -> dict — scans all .md files in vault_path/angles/, reads each file, parses the YAML frontmatter between the first two --- markers using a simple split approach (do NOT import yaml, just split on "---" and parse key: value lines manually to avoid adding a dependency), looks for files where status is "approved" or "skipped", returns a dict with two keys: "approved" (list of dicts with headline, hook, trend, triggers, platform extracted from frontmatter) and "skipped" (same). Only read files modified in the last 30 days to keep it fast. (5) format_feedback_prompt(feedback) -> str — if both approved and skipped lists are empty, return empty string. Otherwise build a prompt section: "LEARNING FROM PAST REVIEWS: The client APPROVED these angle patterns:" then for each approved angle list its headline and triggers, then "The client SKIPPED these angle patterns:" then for each skipped angle list its headline and triggers, then "INSTRUCTIONS: Generate new angles that match APPROVED patterns. Avoid patterns similar to SKIPPED angles. Prioritize the psychology triggers that appeared in approved angles." Add obsidian_vault_path: str = "./obsidian-vault" to the Settings class in src/config.py. Add OBSIDIAN_VAULT_PATH=./obsidian-vault to ~/Documents/antigravity/marketing-agent/.env. Modify src/pipeline.py run_pipeline: before the angle generation loop, if settings.obsidian_vault_path is set, call fetch_feedback to get past decisions, call format_feedback_prompt, print "[Pipeline] Loaded feedback: {n} approved, {n} skipped patterns" or "[Pipeline] No feedback yet", pass the feedback_context to generate_angles_for_trend. Modify src/ai_orchestrator.py generate_angles_for_trend: add optional feedback_context: str = "" parameter, if not empty append it to the system prompt right before the generation instruction. Modify scripts/run_and_report.py: replace the Notion sync step 5 with Obsidian sync — call ensure_vault then push_angles, print "[Obsidian] {count} angles saved to {vault_path}/angles/". Create vault_path/.obsidian/app.json with {"livePreview": true, "readableLineLength": true}. Do NOT remove src/notion_sync.py but do remove the Notion import and call from run_and_report.py — Obsidian replaces it. Run "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/obsidian_sync.py src/pipeline.py src/ai_orchestrator.py scripts/run_and_report.py". IMPORTANT GIT SAFETY: never use git add -A. Stage with "git add src/obsidian_sync.py src/config.py src/pipeline.py src/ai_orchestrator.py scripts/run_and_report.py .env" and commit "feat: replace Notion with Obsidian vault — angles as markdown + feedback loop".
```

---

## How It Works

```
Pipeline Run:
  1. Scan trends
  2. READ obsidian-vault/angles/*.md → find approved/skipped frontmatter
  3. Feed patterns into Gemini prompt as context
  4. Generate angles (biased toward what you liked)
  5. WRITE each angle as a new .md file in obsidian-vault/angles/

You open Obsidian:
  - See all angles as beautiful markdown notes
  - Edit frontmatter: status: new → approved ✅ or skipped ❌
  - Next pipeline run picks up your reviews automatically
```

### Example Angle File

```markdown
---
status: new
grade: fire
trend: Saudi Vision 2030 investments
source: gulf_news
platform: linkedin
triggers: [curiosity_gap, fomo]
score: 0.87
total_score: 52
date: 2026-03-18
headline: "🔥 Why Saudi Vision 2030 Changes Everything"
---

# 🔥 Why Saudi Vision 2030 Changes Everything

> Everyone's talking about Vision 2030. But nobody's connecting
> the dots to what it means for YOUR business...

## Body Outline

1. Context: What's happening
2. The hidden opportunity
3. Your action plan

## Psychology Triggers

- **curiosity_gap**: "Nobody's connecting the dots..."
  Rationale: Creates information asymmetry — reader needs to find out what dots.
- **fomo**: "Everyone's talking about..."
  Rationale: Implies they're already behind if not paying attention.
```

---

## Validation After Running

```bash
# Lint clean
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/obsidian_sync.py src/pipeline.py src/ai_orchestrator.py

# Run pipeline
cd ~/Documents/antigravity/marketing-agent
uv run python scripts/run_and_report.py

# Check vault was created with angle files
ls -la obsidian-vault/angles/

# Open in Obsidian: File > Open Vault > select obsidian-vault folder
```

---

## After This Phase

Open the `obsidian-vault` folder in Obsidian. You'll see every generated angle as a note. Edit `status: new` to `status: approved` or `status: skipped` on the ones you review. Next pipeline run automatically learns from your choices. Zero APIs, instant, works offline.

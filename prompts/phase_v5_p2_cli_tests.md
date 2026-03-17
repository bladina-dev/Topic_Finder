# V5 Phase 2 — CLI Video Command Integration Tests

**Date:** 2026-03-17 | **Repo:** `~/Documents/antigravity/marketing-agent/`
**Prereqs:** V5 Phase 1 done (8 tests pass in `tests/test_video_converter.py`)

---

## Critical Warnings

| Warning | Fix |
|:---|:---|
| W1: UV cache | Use `UV_CACHE_DIR=/tmp/uv-cache` prefix if cache errors |
| W2: Never `git add -A` | Stage specific files only |
| W3: Don't change src/ | This phase is TESTS ONLY — do NOT modify source code |

---

## The Prompt

```
Read ~/Documents/antigravity/marketing-agent/src/cli.py (the video command around line 133) and ~/Documents/antigravity/marketing-agent/tests/test_video_converter.py (8 existing tests, all passing). Create ~/Documents/antigravity/marketing-agent/tests/test_cli_video.py. The video CLI command uses Typer, runs run_pipeline then angle_to_video_data then saves JSON. Write 3-4 tests using pytest. Test that the video command with --mock flag: use unittest.mock.patch to mock run_pipeline to return a mock AgentOutput with 1 TrendWithAngles containing 2 mock ContentAngles, mock angle_to_video_data to return a simple dict with id, title, scenes, then invoke the video command using typer.testing.CliRunner with ["video", "--mock", "--output", "/tmp/test_video_output"], assert exit code is 0 and a JSON file was created in /tmp/test_video_output/. Test with --pick 2: same setup but add "--pick", "2" to the args, verify the second angle was selected (check that angle_to_video_data received the second angle). Test with no angles: mock run_pipeline to return AgentOutput with empty results, invoke video command, assert exit code is 1 and output contains "No angles" or error message. After tests, run a real E2E: "UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.cli video --mock" and verify output/videos/ contains a JSON file with valid VideoData structure. Run "UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v" to run all tests. Run "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/ tests/" for lint. IMPORTANT GIT SAFETY: never use git add -A. Stage with "git add tests/" then commit with "git commit -m 'test: add CLI video command integration tests'". Target: 3+ new tests pass, all 8 existing tests still pass, zero ruff errors.
```

---

## Validation After Running

```bash
# All tests should pass (8 existing + 3 new = 11+)
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v

# Lint clean
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/ tests/

# E2E mock produces valid JSON
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.cli video --mock
cat output/videos/fahad-ep-*.json | python -m json.tool
```

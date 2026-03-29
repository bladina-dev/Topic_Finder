# Phase B1: Dashboard Backend API

This phase adds 10 new API endpoints to src/api.py to support the marketing dashboard frontend.

## Instructions for Claude Code

Read the existing src/api.py, src/pipeline.py, src/source_manager.py, src/config.py, and src/models.py first. Follow the specs below. Run uv run pytest tests/ -v after to confirm no regressions. Commit with message "feat: Phase B1 - Dashboard backend API endpoints".

---

## Endpoint 1: Full Pipeline Scan (trends only)

Add GET /api/scan endpoint. Accept query params: mock (bool, default false), max_results (int, default 15), sources (str, default ""). Import run_pipeline from pipeline. Build source_names = [sources] if sources else None. Call await run_pipeline(mock=mock, max_trends=max_results, angles_per_trend=0, source_names=source_names). Return {"trends": [t.trend.model_dump() for t in output.results], "count": len(output.results), "errors": output.errors}.

## Endpoint 2: Full Pipeline with Angles

Update the existing POST /api/angles/generate endpoint. Add source_names support. Accept an optional "sources" field in GenerateRequest (add it to the model in models.py as sources: str = ""). Build source_names = [request.sources] if request.sources else None. Pass source_names=source_names to run_pipeline.

## Endpoint 3: List Source Files

Add GET /api/sources endpoint. Import list_source_files from source_manager. Return {"sources": list_source_files()}.

## Endpoint 4: Get Source Entries

Add GET /api/sources/{name} endpoint. Import load_sources from source_manager. Try to load sources, return {"name": name, "entries": [e.model_dump() for e in entries], "count": len(entries)}. On FileNotFoundError raise HTTPException 404.

## Endpoint 5: Add Source Entry

Add POST /api/sources/{name}/add endpoint. Accept JSON body with fields: vertical (str), source_type (str), handle_or_domain (str), label (str, default ""). Import add_source from source_manager. Call add_source(file_name=name, vertical=vertical, source_type=source_type, handle_or_domain=handle_or_domain, label=label). Return {"status": "added", "handle_or_domain": handle_or_domain}.

## Endpoint 6: Get Seed Keywords

Add GET /api/sources/{name}/seeds endpoint. Import load_seed_keywords from source_manager. Return {"name": name, "keywords": load_seed_keywords(name)}. On FileNotFoundError raise HTTPException 404.

## Endpoint 7: Get Settings

Add GET /api/settings endpoint. Return a dict of current settings with API keys masked. For each key field (tavily_api_key, serpapi_api_key, google_api_key, youtube_data_api_key, anthropic_api_key, notion_api_key, telegram_bot_token, elevenlabs_api_key, azure_speech_key) show only the last 4 characters preceded by "****" if set, or empty string if not set. Include non-secret fields as-is: default_ai_provider, agent_timezone, default_sources, youtube_scan_enabled, influencer_scan_enabled, google_trends_enabled, reports_path, obsidian_vault_path.

## Endpoint 8: Update Settings

Add POST /api/settings endpoint. Accept JSON body as dict. For each key in the body, if the value is not "****..." (i.e., not a masked placeholder), write it to the .env file. Implement a helper function _update_env_file(updates: dict[str, str]) that reads the existing .env file at the project root, updates matching KEY=value lines, appends any new keys, and writes back. After updating, reload settings by re-reading the env file. Return {"status": "updated", "keys_updated": list(updates.keys())}.

## Endpoint 9: Update Angle Status

Add POST /api/angles/status endpoint. Accept JSON body with filename_stem (str) and status (str, one of "approved", "skipped", "new"). Import update_angle_status from obsidian_sync. Call it with settings.obsidian_vault_path. Return {"status": "updated"} on success, raise HTTPException 400 on failure.

## Endpoint 10: Health Check Enhancement

Update the existing GET /api/health endpoint to include configured API status. Check which API keys are set (non-empty) and return their status. Return {"status": "healthy", "version": "0.5.1", "provider": settings.default_ai_provider, "apis": {"tavily": bool(settings.tavily_api_key), "serpapi": bool(settings.serpapi_api_key), "youtube": bool(settings.youtube_data_api_key or settings.google_api_key), "notion": bool(settings.notion_api_key), "telegram": bool(settings.telegram_bot_token)}}.

---

## Helper: _update_env_file

Create this as a standalone function in api.py or in config.py. It should:
1. Read the .env file from Path(__file__).parent.parent / ".env"
2. Parse existing lines into key=value pairs
3. For each update key, replace the existing line or append a new one
4. Write the file back
5. Preserve comments and blank lines

---

## Verification

Start the API server with: uv run python -m src.cli serve

Then test these curl commands:
- curl http://localhost:8000/api/health
- curl http://localhost:8000/api/scan?mock=true
- curl http://localhost:8000/api/sources
- curl http://localhost:8000/api/settings
- curl -X POST http://localhost:8000/api/angles/generate -H "Content-Type: application/json" -d '{"mock": true, "sources": "saudi_general"}'

Run uv run pytest tests/ -v to confirm no regressions.

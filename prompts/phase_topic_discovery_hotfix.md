# Phase: Topic Discovery Hotfixes (v0.5.1)

Live testing revealed 4 issues that need patching before the pipeline produces usable results. Fix all 4 in one pass.

## Fix 1: scan CLI must use full 3-layer pipeline

The scan command in src/cli.py calls scan_trends() directly on line 34. This skips the Influencer and Seed Keyword layers. Change the scan command to use run_pipeline() instead.

Modify src/cli.py scan command: import run_pipeline from pipeline. Build source_names = [sources] if sources else None. Call run_pipeline(mock=mock, max_trends=max_results, source_names=source_names, angles_per_trend=0). Add a new parameter angles_per_trend to run_pipeline if it doesn't already accept 0 gracefully — when angles_per_trend is 0, skip the angle generation step entirely and return trends only. Display the trends from output.results in the table. Keep the same table format.

Note: run_pipeline already has angles_per_trend param. When it's 0 the for loop over trends still runs but generates 0 angles per trend which is fine. The TrendWithAngles objects will have empty angles lists.

## Fix 2: Balance output mix across source types

Currently YouTube trending has jack_potential based on view velocity (0.85-0.95) while targeted domains are fixed at 0.75. This means YouTube completely dominates the final sorted output.

Modify src/trend_scanner.py scan_trends function: after collecting all trends and before the dedup step, cap YouTube trending jack_potential at 0.80 max. Add this code after the YouTube scanning section: for t in all_trends: if t.source == TrendSource.YOUTUBE: t.jack_potential = min(t.jack_potential, 0.80).

Also increase the default max_results in scan_trends from 8 to 15 so there is room for multiple source types to appear.

Update src/cli.py scan command: change the default for max_results from 8 to 15.

## Fix 3: Fix Gemini model name in yt_scanner.py

The model gemini-1.5-flash no longer exists. Find all occurrences of "gemini-1.5-flash" in src/yt_scanner.py and replace with "gemini-2.0-flash-lite". The google-genai SDK uses client.models.generate_content with the model name string.

## Fix 4: Add SerpAPI logging

Modify src/trend_scanner.py scan_trends function: add a print statement before the SerpAPI call: print("[TrendScanner] Running SerpAPI Google Trends KSA..."). After the call add: print(f"[TrendScanner] Got {len(serp_trends)} trends from SerpAPI"). If serpapi_api_key is empty add: print("[TrendScanner] SerpAPI skipped (no API key)").

Also in scan_serpapi_trends function: the SerpAPI google_trends engine does not return "trending_searches" key. Check the actual response format. The correct endpoint for trending searches is engine="google_trends_trending_now" with geo="SA". Update the engine parameter. Parse the results from the "trending_searches" key in the response. Each item has a "query" field. Print the raw keys of the SerpAPI response for debugging: print(f"[TrendScanner] SerpAPI response keys: {list(results.keys())}").

---

## Verification

Run uv run python -m src.cli scan --sources saudi_general and verify:
1. Output shows a mix of youtube, targeted, and gulf_news/serp_trends sources (not all youtube)
2. SerpAPI log lines appear showing it ran and how many trends it found
3. No Gemini model errors in the YouTube scanner logs
4. More than 8 total results appear (new default is 15)

Run uv run pytest tests/ -v and confirm 34+ tests still pass.

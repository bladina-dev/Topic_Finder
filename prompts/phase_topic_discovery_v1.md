# Phase: Topic Discovery Redesign (v0.5.0)

This phase implements a 3-layer topic discovery pipeline (Trends then Influencer Signals then Seed Keywords) with cross-reference scoring and a new CLI --sources flag.

## Instructions for Claude Code

Read docs/v0.5.0-plan.md first for the full architecture. Follow the 6 phases below in order. Write unit tests in tests/test_trend_scanner.py for each new scanner using mocked APIs. Run uv run pytest tests/ -v after each phase to confirm no regressions. Commit each phase with a message like feat: Phase 1 - Models and Config.

---

## Phase 1: Models & Config (DONE)

Already implemented. TrendSource, TopicOrigin enums and origin field on Trend model added. Config updated with serpapi_api_key, seed_keywords_sources, influencer_scan_enabled. pytrends removed and google-search-results added.

## Phase 2: CLI Flag (--sources)

Modify src/cli.py: add a --sources flag (type str, default empty string) to the scan, generate, and video commands. Import settings from src/config.py. In each command when sources is provided pass source_names=[sources] to scan_trends(), otherwise pass source_names=None. Do NOT pass source_names to run_pipeline yet because run_pipeline does not accept that parameter until Phase 6. For the generate and video commands just wire it to scan_trends for now. Verification: run uv run python -m src.cli scan --mock --sources saudi_general and confirm no error.

## Phase 3: Trend Discovery Fixes

Modify src/trend_scanner.py with these 3 changes:

Fix 1 - Replace the 3 generic Tavily queries on lines 136-140 with these 5 diverse topic-specific queries: "Saudi Arabia business news today", "Saudi tech startups latest", "KSA economy finance update this week", "Riyadh entertainment events culture", "Saudi e-commerce digital marketing news".

Fix 2 - Delete the entire scan_google_trends function (lines 247-290) since pytrends has been removed from dependencies. Replace it with scan_serpapi_trends(max_results: int = 5). Import serpapi.GoogleSearch inside the function body. Use parameters engine="google_trends", q="trending topics", geo="SA", hl="ar", api_key=settings.serpapi_api_key. Parse the trending results into Trend objects with source=TrendSource.SERP_TRENDS and origin=TopicOrigin.TREND. If settings.serpapi_api_key is empty return an empty list immediately without error.

Fix 3 - Update scan_trends() function: change the if source_names guard on line 314 to use a fallback. If source_names is None or empty set source_names = [settings.default_sources]. This ensures targeted scanning and YouTube scanning always run. Move the YouTube scan_trending_ksa call outside the source_names condition so it always runs when youtube_data_api_key or google_api_key is present. Replace the google_trends_enabled check on line 349 with a call to scan_serpapi_trends when settings.serpapi_api_key is set. Import TopicOrigin from models and tag all trends with origin=TopicOrigin.TREND.

Write tests in tests/test_trend_scanner.py: one test mocking AsyncTavilyClient to verify the 5 new query strings are used, one test for scan_serpapi_trends returning empty list when no API key.

## Phase 4: Influencer Signal Scanner

Create src/influencer_scanner.py (new file) with two async functions.

Function 1 - async def scan_influencer_domains(source_names: list[str], max_results: int = 10) -> list[Trend]. Import get_domains_for_scan from source_manager. Import AsyncTavilyClient from tavily. Import settings from config. If settings.tavily_api_key is empty return empty list. Load domains = get_domains_for_scan(source_names). Create Tavily client and search with query="latest news this week", include_domains=domains (batch in groups of 10 like scan_targeted_sources does). Build Trend objects with source=TrendSource.INFLUENCER, origin=TopicOrigin.INFLUENCER, jack_potential=0.75.

Function 2 - async def scan_influencer_youtube(source_names: list[str], max_per_channel: int = 2) -> list[Trend]. Import scan_youtube_sources from yt_scanner. Call it and get results. For each trend in results set trend.origin = TopicOrigin.INFLUENCER and trend.source = TrendSource.INFLUENCER. Return the modified list.

Write tests in tests/test_influencer_scanner.py: mock get_domains_for_scan and AsyncTavilyClient. Assert that all returned trends have origin=INFLUENCER. Assert the Tavily query is "latest news this week" not "trending topics".

## Phase 5: Seed Keyword Enrichment

Create sources/seed_keywords.csv as a proper CSV file with these exact contents:
vertical,keyword,intent,label
tech,AI in Saudi Arabia,informational,Core content pillar
tech,Saudi startups funding,informational,Startup ecosystem
finance,Tadawul stocks analysis,commercial,Finance pillar
marketing,social media marketing Saudi Arabia,commercial,Marketing pillar
ecommerce,e-commerce growth KSA,informational,E-commerce pillar
culture,Riyadh entertainment events,navigational,Culture events

Modify src/source_manager.py: add a function load_seed_keywords(name: str = "seed_keywords") -> list[dict]. It should read sources/{name}.csv using csv.DictReader. Required columns are vertical, keyword, intent, label. Return list of dicts with those 4 keys. Raise FileNotFoundError if CSV does not exist.

Create src/seed_scanner.py (new file) with one async function: async def scan_seed_keywords(source_name: str = "seed_keywords", max_results: int = 6) -> list[Trend]. Import load_seed_keywords from source_manager. Import AsyncTavilyClient from tavily. Import settings from config. If settings.tavily_api_key is empty return empty list. Load keywords via load_seed_keywords(source_name). For each keyword dict run Tavily search with query="latest {keyword} 2026" using the keyword value. Build Trend objects with source=TrendSource.SEED_KEYWORD, origin=TopicOrigin.SEED_KEYWORD, jack_potential=0.7. Stop after max_results total trends.

Write tests in tests/test_seed_scanner.py: mock load_seed_keywords and AsyncTavilyClient. Assert origin is SEED_KEYWORD on all results.

## Phase 6: Topic Mixer & Scoring in Pipeline

Modify src/pipeline.py: update run_pipeline signature to accept source_names: list[str] | None = None.

Update the scan_trends call to pass source_names=source_names.

After scanning trends add two new blocks: if not mock and settings.influencer_scan_enabled then import scan_influencer_domains and scan_influencer_youtube from influencer_scanner and run both passing source_names or [settings.default_sources] as fallback, extend the trends list with results. Then if not mock import scan_seed_keywords from seed_scanner and run it, extend trends list with results.

Before generating angles add a call to deduplicate_and_score. Implement this function in pipeline.py: def deduplicate_and_score(trends: list[Trend]) -> list[Trend]. Import _normalize_title from trend_scanner (it is a module-level function so import it directly as from .trend_scanner import _normalize_title). Normalize each title and group trends by normalized key. For each group keep the trend with highest jack_potential. Count distinct origin values in the group. If 2 or more distinct origins exist boost the kept trend jack_potential by min(jack_potential + 0.1, 1.0). Return sorted by jack_potential descending.

Now go back to src/cli.py and update the generate and video commands: pass source_names=[sources] if sources is provided to run_pipeline() now that it accepts the parameter.

Write tests in tests/test_pipeline.py: test deduplicate_and_score where a topic with TREND and INFLUENCER origin gets +0.1 boost. Test a topic with only TREND origin gets no boost. Test dedup keeps highest jack_potential among duplicates.

Final verification: uv run pytest tests/ -v then uv run python -m src.cli scan --sources saudi_general --mock.

---

## Copy-Paste Prompts for Claude CLI

### Phase 1 (DONE)

### Phase 2
Read prompts/phase_topic_discovery_v1.md and execute Phase 2 (CLI Flag). Add a --sources flag to scan, generate, and video in src/cli.py. For now only pass source_names to scan_trends not run_pipeline. Verify with uv run python -m src.cli scan --mock --sources saudi_general.

### Phase 3
Read prompts/phase_topic_discovery_v1.md and execute Phase 3 (Trend Discovery Fixes). Replace the 3 generic Tavily queries with 5 diverse ones, delete scan_google_trends and replace with scan_serpapi_trends using serpapi library with graceful fallback, fix scan_trends to always use source_names with fallback to default_sources and always run YouTube trending. Write tests. Run uv run pytest tests/ -v.

### Phase 4
Read prompts/phase_topic_discovery_v1.md and execute Phase 4 (Influencer Signal Scanner). Create src/influencer_scanner.py with scan_influencer_domains using Tavily domain-locking with query "latest news this week" and scan_influencer_youtube reusing yt_scanner but tagging origin as INFLUENCER. Write tests in tests/test_influencer_scanner.py. Run uv run pytest tests/ -v.

### Phase 5
Read prompts/phase_topic_discovery_v1.md and execute Phase 5 (Seed Keyword Enrichment). Create sources/seed_keywords.csv with 6 brand pillar rows, add load_seed_keywords to src/source_manager.py, create src/seed_scanner.py with scan_seed_keywords. Write tests in tests/test_seed_scanner.py. Run uv run pytest tests/ -v.

### Phase 6
Read prompts/phase_topic_discovery_v1.md and execute Phase 6 (Topic Mixer and Scoring). Update run_pipeline in src/pipeline.py to accept source_names then orchestrate all 3 layers. Implement deduplicate_and_score with +0.1 boost for multi-layer topics capped at 1.0. Update cli.py to pass source_names to run_pipeline. Write tests in tests/test_pipeline.py. Run uv run pytest tests/ -v. Final check: uv run python -m src.cli scan --sources saudi_general --mock.

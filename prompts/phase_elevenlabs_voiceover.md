# ElevenLabs Arabic Voiceover Integration

**Date:** 2026-03-17 | **Repo:** `~/Documents/antigravity/marketing-agent/`
**Prereqs:** V5 Phase 2 done (11+ tests pass), `ELEVENLABS_API_KEY` in `.env`

---

## Critical Warnings

| Warning | Fix |
|:---|:---|
| W1: UV cache | Use `UV_CACHE_DIR=/tmp/uv-cache` prefix if cache errors |
| W2: Never `git add -A` | Stage specific files only |
| W3: No elevenlabs package | Use `httpx` REST calls directly — do NOT install the elevenlabs Python SDK |
| W4: API key optional | If `ELEVENLABS_API_KEY` is not set and `--voiceover` is used, print warning and skip |

---

## The Prompt

```
Read ~/Documents/antigravity/marketing-agent/src/video_converter.py and ~/Documents/antigravity/marketing-agent/src/cli.py. Add ElevenLabs Arabic voiceover generation to the video pipeline. Create ~/Documents/antigravity/marketing-agent/src/voiceover.py — a module that takes VideoData JSON, extracts all scene headlines and body text, concatenates them into a single Arabic script, then calls the ElevenLabs API to generate an MP3 voiceover. Use the ElevenLabs REST API directly with httpx (do NOT install the elevenlabs Python package): POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id} with headers {"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"} and body {"text": script_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}. The response is raw MP3 audio bytes — save to output/voiceovers/{video_id}.mp3. For the voice_id, use a default Arabic male voice "pNInz6obpgDQGcFmaJgB" (Adam) or let the user pass --voice-id. Add a --voiceover flag to the video CLI command that, after generating the VideoData JSON, also generates the voiceover MP3. If ELEVENLABS_API_KEY is not set and --voiceover is used, print a warning "⚠️ ELEVENLABS_API_KEY not set — skipping voiceover" and skip. Create a _extract_script_from_video_data(video_data: dict) -> str function that builds a natural reading script from the scenes — for each scene, take the headline and body text, join them with periods, skip the intro scene (type=="intro") since it's always the same "معكم فهد الحربي". Add a --mock-voiceover flag that generates a placeholder text file instead of calling the API (for testing without API credits). Print progress: "🎤 Extracting script from {n} scenes...", "🔊 Generating voiceover ({len(script)} chars)...", "✅ Voiceover saved: {path}". Create output/voiceovers/.gitkeep. Write 2 tests in tests/test_voiceover.py: test _extract_script_from_video_data returns non-empty Arabic text containing scene content, test that generate_voiceover with mocked httpx.post returns bytes and saves file. Run "UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v" then "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/ tests/". IMPORTANT GIT SAFETY: never use git add -A. Stage with "git add src/voiceover.py tests/test_voiceover.py src/cli.py output/voiceovers/.gitkeep" and commit "feat(voiceover): add ElevenLabs Arabic voiceover generation". Target: 2 new tests pass, all existing tests still pass, zero ruff errors.
```

---

## Validation After Running

```bash
# All tests pass (existing + 2 new voiceover tests)
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v

# Lint clean
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/ tests/

# E2E with mock voiceover (no API key needed)
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.cli video --mock --mock-voiceover

# E2E with real voiceover (needs ELEVENLABS_API_KEY in .env)
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.cli video --mock --voiceover
```

---

## After This Phase

The pipeline will be: Topic → Trends → Angles → VideoData JSON → **Voiceover MP3**

Next integration to add: **MiniMax Audio** for background music generation.

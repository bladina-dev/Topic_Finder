# MiniMax Audio — Background Music Generation + FFmpeg Merge

**Date:** 2026-03-17 | **Repo:** `~/Documents/antigravity/marketing-agent/`
**Prereqs:** ElevenLabs voiceover done, 13/13 tests pass

---

## Critical Warnings

| Warning | Fix |
|:---|:---|
| W1: UV cache | Use `UV_CACHE_DIR=/tmp/uv-cache` prefix if cache errors |
| W2: Never `git add -A` | Stage specific files only |
| W3: No minimax package | Use `httpx` REST calls directly |
| W4: FFmpeg must be installed | Check with `which ffmpeg` — install via `brew install ffmpeg` on Mac or `apt install ffmpeg` on Ubuntu |
| W5: API key optional | If `MINIMAX_API_KEY` is not set and `--bg-music` is used, fall back to the existing static MP3 file |

---

## The Prompt

```
Read ~/Documents/antigravity/marketing-agent/src/voiceover.py (just built — ElevenLabs integration pattern), ~/Documents/antigravity/marketing-agent/src/video_converter.py, and ~/Documents/antigravity/marketing-agent/src/cli.py. You are adding two features: (1) AI-generated background music via MiniMax Audio API, and (2) FFmpeg merge to combine Remotion video + voiceover + music into a final MP4.

PART 1 — Create ~/Documents/antigravity/marketing-agent/src/music_generator.py:
- Create generate_bg_music(prompt: str, output_path: str, mock: bool = False) -> str async function
- If mock=True, copy the existing static bgMusic file "EleEnergetic, Social Media Creator_pre_sp109_s50_sb75_v3.mp3" from public/ or write a placeholder and return the path
- If mock=False, call the MiniMax Music Generation API: POST https://api.minimax.chat/v1/music_generation with headers {"Authorization": "Bearer " + os.environ["MINIMAX_API_KEY"], "Content-Type": "application/json"} and body {"model": "music-01", "prompt": prompt, "refer_voice": null}. The response JSON has an "audio_file" field with base64-encoded audio — decode and save to output/music/{video_id}_bg.mp3
- Create _generate_music_prompt(video_data: dict) -> str that takes VideoData and generates a music prompt like "Energetic upbeat background music for a 45-second Arabic YouTube Short about {topic}. Modern, motivational, no vocals, suitable for career content."
- If MINIMAX_API_KEY is not set and mock is False, print "⚠️ MINIMAX_API_KEY not set — using default background music" and return the path to the existing static bgMusic file
- Create output/music/.gitkeep

PART 2 — Create ~/Documents/antigravity/marketing-agent/src/video_assembler.py:
- Create assemble_video(video_path: str, voiceover_path: str | None, music_path: str | None, output_path: str) -> str function
- Use subprocess.run to call ffmpeg to merge: if voiceover and music are both provided, mix them with ffmpeg using filter_complex "[1:a]volume=1.0[voice];[2:a]volume=0.15[music];[voice][music]amix=inputs=2:duration=first[aout]" -map 0:v -map "[aout]". If only voiceover, just add it as audio track. If only music, add music at low volume. If neither, just copy the video as-is.
- Print progress: "🎬 Assembling final video...", "✅ Final video: {output_path}"
- Check that ffmpeg is available with shutil.which("ffmpeg"), if not raise RuntimeError("ffmpeg not found — install with: brew install ffmpeg")

PART 3 — Update src/cli.py video command:
- Add --bg-music flag (generates AI background music via MiniMax)
- Add --mock-music flag (uses placeholder, no API key needed)
- Add --assemble flag (runs FFmpeg merge after all assets are ready)
- The full flow with all flags: video --mock --mock-voiceover --mock-music --assemble should: generate VideoData JSON, create placeholder voiceover, use default music, then print what ffmpeg command would run (since no actual Remotion render is done in this step, just print the command)
- Print the full pipeline summary at the end:
  "📋 Pipeline Summary:
   📄 VideoData: output/videos/{id}.json
   🎤 Voiceover: output/voiceovers/{id}.mp3
   🎵 Music: output/music/{id}_bg.mp3
   🎬 To assemble: python -m src.cli assemble --video out/{id}.mp4 --voiceover output/voiceovers/{id}.mp3 --music output/music/{id}_bg.mp3"

PART 4 — Tests:
- Create tests/test_music_generator.py: test _generate_music_prompt returns non-empty string containing topic info, test generate_bg_music with mock=True returns a path to an existing file
- Create tests/test_video_assembler.py: test assemble_video raises RuntimeError when ffmpeg not found (patch shutil.which to return None), test assemble_video constructs correct ffmpeg command (patch subprocess.run and verify the args)

Run "UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v" then "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/ tests/". IMPORTANT GIT SAFETY: never use git add -A. Stage with "git add src/music_generator.py src/video_assembler.py tests/test_music_generator.py tests/test_video_assembler.py src/cli.py output/music/.gitkeep" and commit "feat(pipeline): add MiniMax music generation and FFmpeg video assembly". Target: 4 new tests pass, all existing tests still pass, zero ruff errors.
```

---

## Validation After Running

```bash
# All tests pass (13 existing + 4 new = 17+)
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v

# Lint clean
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/ tests/

# Full pipeline E2E (all mocked — no API keys needed)
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.cli video --mock --mock-voiceover --mock-music

# Check FFmpeg is available
which ffmpeg
```

---

## After This Phase

The full pipeline will be:
```
Topic → Trends → Angles → VideoData JSON
                              ├── Voiceover MP3 (ElevenLabs)
                              ├── Background Music (MiniMax or static)
                              └── Remotion render → MP4
                                       └── FFmpeg merge → Final MP4 with audio
```

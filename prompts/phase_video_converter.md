# Claude CLI Prompt: Video Pipeline — ContentAngle → VideoData Converter

## ROLE
You are a senior Python engineer adding a `video` command to an existing marketing agent CLI. You are writing a CONVERTER that transforms `ContentAngle` objects into `VideoData` JSON files compatible with a Remotion video template.

## REQUIRED READING
Before writing ANY code, read these files in order:
1. `src/models.py` — understand `ContentAngle`, `Trend`, `PsychTrigger`, `Platform` models
2. `src/cli.py` — understand the existing Typer CLI structure (`scan`, `generate`, `upload`, `serve`)
3. `src/pipeline.py` — understand how `run_pipeline()` returns `AgentOutput` with `TrendWithAngles`
4. `src/ai_orchestrator.py` — understand the Gemini/Claude generation and cultural context injection

## CONTEXT: THE VIDEO TEMPLATE
The Remotion template at `~/Downloads/SamCV /video/` expects this exact data shape:

```typescript
interface VideoScene {
    type: 'hook' | 'intro' | 'point' | 'story' | 'list' | 'cta';
    emoji?: string;
    headline: string;      // Arabic text, supports \n for line breaks
    body?: string;          // Smaller text below headline
    items?: string[];       // List items for 'list' type scenes
    camera?: 'zoom' | 'pan' | 'tilt' | 'static';
    durationInFrames?: number;  // 30fps. Typical: 75-180 frames
}

interface VideoData {
    id: string;             // e.g., "fahad-ep-20260316-ai-jobs-ksa"
    title: string;          // Arabic video title
    pillar: 'career' | 'workplace' | 'ai' | 'story' | 'sidehustle';
    voiceover?: string;     // Audio file in /public/
    bgMusic?: string;
    bgMusicVolume?: number; // 0-1, typically 0.15
    scenes: VideoScene[];   // 5-6 scenes following: hook → intro → points → cta
}
```

Scene pattern that works (from 5 existing videos):
- **hook** (90 frames): Big emoji + bold headline, zoom camera
- **intro** (75 frames): "معكم فهد الحربي" + "خبير مهني — SamimlyCV", static camera
- **point** (120 frames): Key insight with emoji + body text, pan/tilt camera
- **list** (150 frames): 3-5 bullet items with staggered animation, tilt camera
- **cta** (90 frames): Subscribe message + "SamimlyCV" button, zoom camera

## TASK — Add `video` Command to CLI

### What to create:

#### 1. `src/video_converter.py` [NEW]
A module that converts a `ContentAngle` (or full `AgentOutput`) into `VideoData` JSON.

**Approach A — Direct conversion (no LLM needed):**
Map ContentAngle fields to VideoData scenes deterministically:
```python
def angle_to_video_data(angle: ContentAngle, trend: Trend) -> dict:
    """Convert a ContentAngle into VideoData JSON."""
    scenes = [
        # Scene 1: Hook — use the angle's hook text
        {"type": "hook", "emoji": _pick_emoji(trend), "headline": _to_arabic_headline(angle.hook), "camera": "zoom", "durationInFrames": 90},
        
        # Scene 2: Intro — always the same
        {"type": "intro", "emoji": "💼", "headline": "معكم فهد الحربي", "body": "خبير مهني — SamimlyCV", "camera": "static", "durationInFrames": 75},
        
        # Scene 3: Main point — from angle headline
        {"type": "point", "emoji": _trigger_emoji(angle.psych_triggers), "headline": angle.headline, "body": _first_sentence(angle.body_outline), "camera": "pan", "durationInFrames": 120},
        
        # Scene 4: Supporting point or list — from body outline
        _body_to_scene(angle.body_outline),
        
        # Scene 5: CTA — always the same
        {"type": "cta", "emoji": "🚀", "headline": "تابعني عشان تعرف أكثر\nعن مستقبل الشغل", "body": "SamimlyCV", "camera": "zoom", "durationInFrames": 90},
    ]
    ...
```

**Approach B — LLM-powered (richer output, use if content needs Arabic translation):**
If the angle is in English (angles 1 & 2 are English, angle 3 is Arabic), use Gemini to:
1. Translate to Gulf Arabic dialect
2. Expand into 5-6 scenes
3. Add appropriate emojis and camera movements

**Use Approach B** — the angles mix English/Arabic and need creative adaptation for video format. Use the existing `generate_content()` from `ai_orchestrator.py`.

The Gemini prompt should:
- Take the ContentAngle as input context
- Output a valid VideoData JSON
- Preserve the psychological trigger in the hook scene
- Use Gulf Arabic dialect (not formal MSA)
- Follow the exact scene pattern from existing videos
- Include the cultural context from `get_cultural_context()`

#### 2. Add `video` command to `src/cli.py`

```python
@app.command()
def video(
    mock: bool = typer.Option(False, "--mock", "-m", help="Use mock data"),
    max_trends: int = typer.Option(4, "--max-trends", "-t", help="Max trends"),
    angles: int = typer.Option(3, "--angles", "-a", help="Angles per trend"),
    pick: int = typer.Option(0, "--pick", "-k", help="Which angle to convert (0=best)"),
    output_dir: Path = typer.Option("output/videos", "--output", "-o", help="Output directory"),
    provider: str = typer.Option("", "--provider", "-p", help="AI provider"),
):
    """Full pipeline: scan trends → generate angles → convert best angle to video JSON."""
```

This command should:
1. Run `run_pipeline()` to get trends + angles
2. Pick the best angle (highest `brand_alignment_score`, or by `--pick` index)
3. Convert it to VideoData JSON using `video_converter.py`
4. Save to `output/videos/{video_id}.json`
5. Print the Remotion render command

#### 3. Create `output/videos/.gitkeep` [NEW]

### Usage example:
```bash
# Full auto: scan → generate → convert → save
uv run python -m src.cli video --max-trends 4 --angles 3

# With mock data (for testing without API calls)
uv run python -m src.cli video --mock

# Pick a specific angle
uv run python -m src.cli video --max-trends 2 --pick 1

# Specify provider
uv run python -m src.cli video --provider claude
```

Expected output:
```
🔍 Scanning Trends...
[Pipeline] Found 4 trends

🚀 Generating angles...
[Pipeline] ✓ AI adoption in Gulf: 3 angles

🎬 Converting best angle to video script...
✅ Video script saved: output/videos/fahad-ep-20260316-ai-gulf.json

To render:
  cd "~/Downloads/SamCV /video"
  npx remotion render FahadYouTubeShort --props="$(pwd)/output/videos/fahad-ep-20260316-ai-gulf.json" out/fahad-ep-20260316-ai-gulf.mp4
```

## CRITICAL RULES

### From docs in cognee-mcp (apply same principles here):
1. **NEVER use `contextlib.suppress`** — always show errors
2. **Test with real data** — run `uv run python -m src.cli video --mock` AND without mock
3. **Print progress** at each pipeline step

### Architecture:
4. **Reuse existing code** — use `run_pipeline()`, `generate_content()`, `get_cultural_context()`
5. **Don't duplicate models** — import `ContentAngle`, `Trend` from `src.models`
6. **Keep video_converter.py focused** — only `angle → VideoData` conversion
7. **The Gemini prompt for scene generation is critical** — study the 5 existing videos in VideoData.ts to match the style
8. **Gulf Arabic dialect** — casual, warm, not formal MSA. Study existing video headlines for tone.

### Existing video style reference (Arabic, Gulf dialect):
```
Hook: "هل الذكاء الاصطناعي\nبياخد شغلك؟"  (not "هل سيحل الذكاء الاصطناعي محل وظيفتك")
Point: "الحقيقة اللي محدش بيقولها:"  (not "الحقائق التي لا يخبرك بها أحد")
CTA:   "تابعني عشان نتكلم\nعن مستقبل الشغل"  (not "تابعنا للمزيد")
```

## VALIDATION CHECKLIST
- [ ] `ruff check src/` passes clean
- [ ] `uv run python -m src.cli video --mock` produces a valid JSON file
- [ ] JSON matches VideoData interface (all required fields present)
- [ ] Scenes follow pattern: hook → intro → 2-3 points/list → cta
- [ ] Arabic text is Gulf dialect, not formal MSA
- [ ] `--pick` flag works to select different angles
- [ ] Output includes the Remotion render command
- [ ] Test with 2 different topics (mock + live if possible)

## GIT COMMIT
```bash
git add src/video_converter.py src/cli.py output/ && git commit -m "feat(video): add angle-to-video converter CLI command" && git push
```

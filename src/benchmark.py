"""Benchmark — AI-powered quality evaluation of generated content angles."""

from __future__ import annotations

import json
import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .models import AgentOutput, ContentAngle, TrendWithAngles


# ─── Scoring Models ───────────────────────────────────────────────────────────

class Grade(str, Enum):
    A = "A"  # 48-60 — Viral-worthy
    B = "B"  # 36-47 — Good, needs polish
    C = "C"  # 24-35 — Mediocre
    D = "D"  # 0-23  — Generic, overhaul needed


class AngleScore(BaseModel):
    """Score for a single content angle across 6 dimensions."""
    headline: str = ""
    creative_novelty: float = Field(default=0, ge=0, le=10)
    psych_trigger_depth: float = Field(default=0, ge=0, le=10)
    viral_mechanics: float = Field(default=0, ge=0, le=10)
    brand_alignment: float = Field(default=0, ge=0, le=10)
    cultural_relevance: float = Field(default=0, ge=0, le=10)
    hook_power: float = Field(default=0, ge=0, le=10)
    total: float = 0
    grade: Grade = Grade.D
    cliches_found: list[str] = Field(default_factory=list)
    heuristic_flags: list[str] = Field(default_factory=list)
    justification: str = ""
    language: str = "en"  # "en" or "ar"

    def compute_total(self):
        self.total = (
            self.creative_novelty
            + self.psych_trigger_depth
            + self.viral_mechanics
            + self.brand_alignment
            + self.cultural_relevance
            + self.hook_power
        )
        if self.total >= 48:
            self.grade = Grade.A
        elif self.total >= 36:
            self.grade = Grade.B
        elif self.total >= 24:
            self.grade = Grade.C
        else:
            self.grade = Grade.D


class BenchmarkReport(BaseModel):
    """Full benchmark report for an agent run."""
    timestamp: datetime = Field(default_factory=datetime.now)
    mode: str = ""  # "mock" | "live"
    angles_evaluated: int = 0
    overall_grade: Grade = Grade.D
    avg_total: float = 0
    avg_creative_novelty: float = 0
    avg_psych_trigger_depth: float = 0
    avg_viral_mechanics: float = 0
    avg_brand_alignment: float = 0
    avg_cultural_relevance: float = 0
    avg_hook_power: float = 0
    total_cliches: int = 0
    top_angles: list[AngleScore] = Field(default_factory=list)
    weakest_dimensions: list[str] = Field(default_factory=list)
    scores: list[AngleScore] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ─── Cliché / Heuristic Detection ────────────────────────────────────────────

CLICHE_PATTERNS_EN = [
    r"top \d+",
    r"you won'?t believe",
    r"here'?s (how|why|what)",
    r"game.?changer",
    r"unlock the secret",
    r"everything you need to know",
    r"the ultimate guide",
    r"this changes everything",
    r"take your .* to the next level",
    r"in today'?s (fast|ever)",
    r"in this article",
    r"did you know",
]

CLICHE_PATTERNS_AR = [
    r"أفضل \d+",
    r"لن تصدق",
    r"كل ما تحتاج",
    r"الدليل الشامل",
    r"نصائح هامة",
    r"أسرار النجاح",
]

VIRAL_SIGNAL_WORDS = [
    "secret", "nobody", "actually", "truth", "mistake", "wrong",
    "surprising", "shocking", "hidden", "unpopular", "controversial",
    "سر", "الحقيقة", "خطأ", "صادم", "مفاجأة",
]

ARABIC_SIGNALS = [
    "السعودية", "رمضان", "رؤية 2030", "الرياض", "جدة", "نيوم",
    "الخليج", "المملكة", "عيد", "هلال", "موسم", "ابن",
]


def detect_language(text: str) -> str:
    """Detect if text is primarily Arabic or English."""
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return "ar" if arabic_chars > len(text) * 0.2 else "en"


def run_heuristic_checks(angle: ContentAngle) -> AngleScore:
    """Run fast heuristic checks on an angle (no AI needed)."""
    score = AngleScore(headline=angle.headline)
    combined_text = f"{angle.headline} {angle.hook} {angle.body_outline}".lower()
    score.language = detect_language(combined_text)

    # Choose cliché patterns based on language
    patterns = CLICHE_PATTERNS_AR if score.language == "ar" else CLICHE_PATTERNS_EN

    # Cliché detection
    for pattern in patterns:
        if re.search(pattern, combined_text, re.IGNORECASE):
            score.cliches_found.append(pattern)

    if score.cliches_found:
        score.heuristic_flags.append(f"🚩 {len(score.cliches_found)} cliché(s) detected")

    # Trigger mismatch: says FOMO but no urgency words
    if angle.psych_triggers:
        for trigger in angle.psych_triggers:
            if trigger.type.value == "fomo":
                urgency_words = ["now", "hurry", "limited", "fast", "last chance",
                                 "عاجل", "الآن", "محدود", "فرصة"]
                if not any(w in combined_text for w in urgency_words):
                    score.heuristic_flags.append("⚠️ FOMO trigger but no urgency words in hook")

            if trigger.type.value == "curiosity_gap":
                gap_words = ["secret", "hidden", "nobody", "actually", "truth",
                             "سر", "الحقيقة", "لا أحد", "مخفي"]
                if not any(w in combined_text for w in gap_words):
                    score.heuristic_flags.append("⚠️ Curiosity gap trigger but no gap words")

    # Emoji overload
    emoji_count = sum(1 for c in angle.headline if ord(c) > 0x1F300)
    if emoji_count > 3:
        score.heuristic_flags.append(f"⚠️ Emoji overload ({emoji_count} emojis in headline)")

    # Viral signals (positive)
    viral_hits = sum(1 for w in VIRAL_SIGNAL_WORDS if w in combined_text)
    if viral_hits >= 2:
        score.heuristic_flags.append(f"✅ Strong viral signals ({viral_hits} power words)")

    # Data hooks (numbers, stats)
    if re.search(r'\d+%|\d+x|\$\d+|\d+ million|\d+ billion', combined_text):
        score.heuristic_flags.append("✅ Data hook detected (numbers/stats)")

    # Arabic/KSA cultural signals
    ksa_hits = sum(1 for w in ARABIC_SIGNALS if w in combined_text)
    if ksa_hits >= 1:
        score.heuristic_flags.append(f"✅ KSA/Gulf cultural signals ({ksa_hits} references)")

    return score


# ─── AI Judge ─────────────────────────────────────────────────────────────────

JUDGE_PROMPT_EN = """You are a BRUTALLY HONEST senior creative director at a top Gulf-region marketing agency.
Your job is to score content angles. Be harsh — most agency output is mediocre and you know it.

Score this marketing content angle on exactly 6 dimensions (0-10 each).

TREND: {trend_title}
HEADLINE: {headline}
HOOK: {hook}
BODY OUTLINE: {body_outline}
PSYCH TRIGGERS USED: {triggers}
TARGET PLATFORM: {platform}

Score each dimension with a number 0-10:
1. creative_novelty: Is this a fresh, unexpected angle? Or a boring "Top 5 tips" cliché? Be harsh.
2. psych_trigger_depth: Does the psychological trigger ACTUALLY create the intended effect? Or does it just name-drop the trigger?
3. viral_mechanics: Would real people share/save/retweet this? Think: hot take, micro-story, controversy, awe, relatable pain.
4. brand_alignment: Even without knowing the specific brand, does this angle feel like it could represent a coherent brand voice?
5. cultural_relevance: How well does this resonate with KSA/Gulf audiences? Ramadan, Vision 2030, Saudi culture, Arabic language? 0 = totally Western, 10 = deeply local.
6. hook_power: Rate ONLY the first sentence of the hook. Would it stop a thumb mid-scroll on Twitter/Instagram?

Also list any CLICHÉ PATTERNS you spotted.

Respond ONLY in this JSON format (no markdown):
{{
    "creative_novelty": 7,
    "psych_trigger_depth": 5,
    "viral_mechanics": 6,
    "brand_alignment": 8,
    "cultural_relevance": 3,
    "hook_power": 7,
    "cliches": ["pattern1"],
    "justification": "2-3 sentence overall assessment"
}}"""

JUDGE_PROMPT_AR = """أنت مدير إبداعي صريح للغاية في وكالة تسويق رائدة في منطقة الخليج.
مهمتك تقييم زوايا المحتوى التسويقي. كن قاسياً — معظم إنتاج الوكالات عادي وأنت تعرف ذلك.

قيّم هذه الزاوية التسويقية على 6 أبعاد (0-10 لكل بعد):

الترند: {trend_title}
العنوان: {headline}
الخطاف: {hook}
ملخص المحتوى: {body_outline}
المحفزات النفسية: {triggers}
المنصة المستهدفة: {platform}

قيّم كل بعد برقم 0-10:
1. creative_novelty: هل هذه زاوية مبتكرة؟ أم مجرد "أفضل 5 نصائح" مملة؟
2. psych_trigger_depth: هل المحفز النفسي يعمل فعلاً؟ أم مجرد ذكر اسمه بدون تأثير حقيقي؟
3. viral_mechanics: هل الناس الحقيقيون سيشاركون هذا؟ فكر: رأي جريء، قصة قصيرة، جدل مثير.
4. brand_alignment: هل تبدو هذه الزاوية متماسكة مع صوت علامة تجارية؟
5. cultural_relevance: ما مدى صدى هذا مع جمهور السعودية/الخليج؟ رمضان، رؤية 2030، الثقافة السعودية؟
6. hook_power: قيّم الجملة الأولى فقط. هل ستوقف الإبهام أثناء التمرير على تويتر؟

كذلك اذكر أي أنماط مكررة (كليشيهات) لاحظتها.

أجب فقط بهذا التنسيق JSON (بدون markdown):
{{
    "creative_novelty": 7,
    "psych_trigger_depth": 5,
    "viral_mechanics": 6,
    "brand_alignment": 8,
    "cultural_relevance": 3,
    "hook_power": 7,
    "cliches": ["نمط1"],
    "justification": "تقييم شامل في 2-3 جمل"
}}"""


async def judge_angle_with_ai(
    angle: ContentAngle,
    trend_title: str,
    language: str = "en",
) -> AngleScore:
    """Use Gemini as an AI judge to score a content angle."""
    from .ai_orchestrator import generate_with_gemini

    triggers_text = ", ".join(
        f"{t.type.value}: '{t.hook}'" for t in angle.psych_triggers
    ) or "none specified"

    prompt_template = JUDGE_PROMPT_AR if language == "ar" else JUDGE_PROMPT_EN

    prompt = prompt_template.format(
        trend_title=trend_title,
        headline=angle.headline,
        hook=angle.hook,
        body_outline=angle.body_outline or "(not provided)",
        triggers=triggers_text,
        platform=angle.platform.value,
    )

    try:
        raw = await generate_with_gemini(
            system_prompt="You are a marketing content quality judge. Respond only in JSON.",
            user_prompt=prompt,
        )

        # Parse JSON response
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            data = json.loads(text)

        score = AngleScore(
            headline=angle.headline,
            creative_novelty=min(10, max(0, float(data.get("creative_novelty", 5)))),
            psych_trigger_depth=min(10, max(0, float(data.get("psych_trigger_depth", 5)))),
            viral_mechanics=min(10, max(0, float(data.get("viral_mechanics", 5)))),
            brand_alignment=min(10, max(0, float(data.get("brand_alignment", 5)))),
            cultural_relevance=min(10, max(0, float(data.get("cultural_relevance", 5)))),
            hook_power=min(10, max(0, float(data.get("hook_power", 5)))),
            cliches_found=data.get("cliches", []),
            justification=data.get("justification", ""),
            language=language,
        )
        score.compute_total()
        return score

    except Exception as e:
        # Return a neutral score on failure
        score = AngleScore(
            headline=angle.headline,
            creative_novelty=5, psych_trigger_depth=5, viral_mechanics=5,
            brand_alignment=5, cultural_relevance=5, hook_power=5,
            justification=f"AI judge failed: {e}",
            language=language,
        )
        score.compute_total()
        return score


# ─── Benchmark Runner ─────────────────────────────────────────────────────────

async def benchmark_output(
    output: AgentOutput,
    use_ai_judge: bool = True,
    mode: str = "mock",
) -> BenchmarkReport:
    """Run the full benchmark on an AgentOutput.

    Args:
        output: The agent's generated output.
        use_ai_judge: If True, use Gemini to score (requires API key).
        mode: "mock" or "live" — for the report label.

    Returns:
        BenchmarkReport with all scores and grades.
    """
    all_scores: list[AngleScore] = []
    errors: list[str] = []

    for result in output.results:
        trend = result.trend
        for angle in result.angles:
            # Step 1: Heuristic checks
            heuristic = run_heuristic_checks(angle)
            language = heuristic.language

            if use_ai_judge:
                # Step 2: AI judge
                try:
                    ai_score = await judge_angle_with_ai(
                        angle, trend.title, language=language,
                    )
                    # Merge heuristic flags into AI score
                    ai_score.heuristic_flags = heuristic.heuristic_flags
                    ai_score.cliches_found = list(set(
                        ai_score.cliches_found + heuristic.cliches_found
                    ))

                    # Apply heuristic adjustments
                    if heuristic.cliches_found:
                        ai_score.creative_novelty = max(0, ai_score.creative_novelty - 2)
                    for flag in heuristic.heuristic_flags:
                        if "FOMO trigger but no urgency" in flag:
                            ai_score.psych_trigger_depth = max(0, ai_score.psych_trigger_depth - 2)
                        if "Emoji overload" in flag:
                            ai_score.hook_power = max(0, ai_score.hook_power - 1)
                        if "KSA/Gulf cultural signals" in flag:
                            ai_score.cultural_relevance = min(10, ai_score.cultural_relevance + 1)
                        if "Data hook" in flag:
                            ai_score.viral_mechanics = min(10, ai_score.viral_mechanics + 1)

                    ai_score.compute_total()
                    all_scores.append(ai_score)
                except Exception as e:
                    errors.append(f"Judge failed for '{angle.headline[:40]}': {e}")
            else:
                # Heuristic-only scoring (rough estimates)
                heuristic.creative_novelty = 5 - len(heuristic.cliches_found) * 2
                heuristic.psych_trigger_depth = 6 if angle.psych_triggers else 3
                heuristic.viral_mechanics = 5 + sum(
                    1 for w in VIRAL_SIGNAL_WORDS
                    if w in f"{angle.headline} {angle.hook}".lower()
                )
                heuristic.brand_alignment = angle.brand_alignment_score * 10
                ksa_hits = sum(
                    1 for w in ARABIC_SIGNALS
                    if w in f"{angle.headline} {angle.hook}".lower()
                )
                heuristic.cultural_relevance = min(10, 3 + ksa_hits * 2)
                heuristic.hook_power = min(10, 5 + (1 if "?" in angle.hook else 0)
                                           + (1 if any(c in angle.hook for c in "🔥⚡💡🚀") else 0))
                heuristic.compute_total()
                all_scores.append(heuristic)

    if not all_scores:
        return BenchmarkReport(
            mode=mode, errors=["No angles to evaluate"]
        )

    # Compute aggregates
    n = len(all_scores)
    report = BenchmarkReport(
        mode=mode,
        angles_evaluated=n,
        avg_total=sum(s.total for s in all_scores) / n,
        avg_creative_novelty=sum(s.creative_novelty for s in all_scores) / n,
        avg_psych_trigger_depth=sum(s.psych_trigger_depth for s in all_scores) / n,
        avg_viral_mechanics=sum(s.viral_mechanics for s in all_scores) / n,
        avg_brand_alignment=sum(s.brand_alignment for s in all_scores) / n,
        avg_cultural_relevance=sum(s.cultural_relevance for s in all_scores) / n,
        avg_hook_power=sum(s.hook_power for s in all_scores) / n,
        total_cliches=sum(len(s.cliches_found) for s in all_scores),
        scores=all_scores,
        errors=errors,
    )

    # Overall grade
    if report.avg_total >= 48:
        report.overall_grade = Grade.A
    elif report.avg_total >= 36:
        report.overall_grade = Grade.B
    elif report.avg_total >= 24:
        report.overall_grade = Grade.C
    else:
        report.overall_grade = Grade.D

    # Top 3 angles
    sorted_scores = sorted(all_scores, key=lambda s: s.total, reverse=True)
    report.top_angles = sorted_scores[:3]

    # Weakest dimensions
    dims = {
        "Creative Novelty": report.avg_creative_novelty,
        "Psych Trigger Depth": report.avg_psych_trigger_depth,
        "Viral Mechanics": report.avg_viral_mechanics,
        "Brand Alignment": report.avg_brand_alignment,
        "Cultural Relevance": report.avg_cultural_relevance,
        "Hook Power": report.avg_hook_power,
    }
    report.weakest_dimensions = [
        k for k, v in sorted(dims.items(), key=lambda x: x[1])[:2]
    ]

    return report


def format_report(report: BenchmarkReport) -> str:
    """Format a BenchmarkReport as a rich terminal-friendly string."""
    grade_emoji = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}
    ge = grade_emoji.get(report.overall_grade.value, "⚪")

    def bar(val: float, max_val: float = 10) -> str:
        filled = int(val / max_val * 10)
        return "▓" * filled + "░" * (10 - filled)

    lines = [
        "",
        "╔════════════════════════════════════════════════════════════╗",
        "║         MARKETING AGENT BENCHMARK REPORT                  ║",
        "╠════════════════════════════════════════════════════════════╣",
        f"║ Mode: {report.mode:<10}  Angles evaluated: {report.angles_evaluated:<16} ║",
        f"║ Overall Grade: {ge} {report.overall_grade.value} (avg {report.avg_total:.1f}/60)                       ║",
        "║                                                           ║",
        "║ Dimension Averages:                                       ║",
        f"║   Creative Novelty    {bar(report.avg_creative_novelty)}  {report.avg_creative_novelty:.1f}/10  ║",
        f"║   Psych Trigger Depth {bar(report.avg_psych_trigger_depth)}  {report.avg_psych_trigger_depth:.1f}/10  ║",
        f"║   Viral Mechanics     {bar(report.avg_viral_mechanics)}  {report.avg_viral_mechanics:.1f}/10  ║",
        f"║   Brand Alignment     {bar(report.avg_brand_alignment)}  {report.avg_brand_alignment:.1f}/10  ║",
        f"║   Cultural Relevance  {bar(report.avg_cultural_relevance)}  {report.avg_cultural_relevance:.1f}/10  ║",
        f"║   Hook Power          {bar(report.avg_hook_power)}  {report.avg_hook_power:.1f}/10  ║",
        "║                                                           ║",
    ]

    if report.top_angles:
        lines.append("║ Top Angles:                                               ║")
        for i, a in enumerate(report.top_angles[:3], 1):
            title = a.headline[:42]
            viral = " ← VIRAL" if a.total >= 48 else ""
            lines.append(f"║   {i}. \"{title}\" ({a.total:.0f}/60){viral} ║")
        lines.append("║                                                           ║")

    if report.weakest_dimensions:
        weak = ", ".join(report.weakest_dimensions)
        lines.append(f"║ Weakest: {weak:<49}║")

    lines.append(f"║ Clichés: {report.total_cliches}/{report.angles_evaluated} angles                                        ║")
    lines.append("╚════════════════════════════════════════════════════════════╝")
    lines.append("")

    return "\n".join(lines)

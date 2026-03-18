"""Obsidian vault sync — saves angles as markdown files, reads feedback from YAML frontmatter."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.models import AgentOutput, ContentAngle, Trend


def _grade(total_score: float) -> str:
    if total_score >= 48:
        return "fire"
    if total_score >= 36:
        return "good"
    return "weak"


def _trend_slug(title: str) -> str:
    slug = title.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return slug[:40]


def ensure_vault() -> Path:
    """Create the Obsidian vault directory structure if it doesn't exist.

    Returns the vault path.
    """
    from src.config import settings

    vault_path = Path(settings.obsidian_vault_path)
    (vault_path / "angles").mkdir(parents=True, exist_ok=True)
    obsidian_dir = vault_path / ".obsidian"
    obsidian_dir.mkdir(exist_ok=True)
    app_json = obsidian_dir / "app.json"
    if not app_json.exists():
        app_json.write_text(
            json.dumps({"livePreview": True, "readableLineLength": True}, indent=2),
            encoding="utf-8",
        )
    return vault_path


def _write_angle_file(
    vault_path: Path,
    angle: ContentAngle,
    trend: Trend,
    grade: str,
    total_score: float,
    n: int = 0,
) -> bool:
    """Write a single angle as a markdown file with YAML frontmatter.

    Filename format: {YYYY-MM-DD}_{trend-slug}_{nnn}.md
    Returns True on success.
    """
    try:
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        slug = _trend_slug(trend.title)
        filename = f"{today}_{slug}_{n:03d}.md"
        filepath = vault_path / "angles" / filename

        triggers = [t.type.value for t in angle.psych_triggers]
        triggers_yaml = "[" + ", ".join(triggers) + "]" if triggers else "[]"
        headline_safe = angle.headline.replace('"', '\\"')

        frontmatter = "\n".join([
            "---",
            "status: new",
            f"grade: {grade}",
            f"trend: {trend.title}",
            f"source: {trend.source.value}",
            f"platform: {angle.platform.value}",
            f"triggers: {triggers_yaml}",
            f"score: {round(angle.brand_alignment_score, 4)}",
            f"total_score: {round(total_score, 1)}",
            f"date: {today}",
            f'headline: "{headline_safe}"',
            "---",
        ])

        hook_block = "\n".join(f"> {line}" for line in angle.hook.split("\n"))

        trigger_items: list[str] = []
        for t in angle.psych_triggers:
            trigger_items.append(f'- **{t.type.value}**: "{t.hook}"')
            if t.rationale:
                trigger_items.append(f"  Rationale: {t.rationale}")

        body = "\n".join([
            frontmatter,
            "",
            f"# {angle.headline}",
            "",
            hook_block,
            "",
            "## Body Outline",
            "",
            angle.body_outline,
            "",
            "## Psychology Triggers",
            "",
            "\n".join(trigger_items) if trigger_items else "_No triggers recorded._",
        ])

        filepath.write_text(body, encoding="utf-8")
        return True

    except Exception as e:
        print(f"[Obsidian] Warning: failed to write '{angle.headline[:40]}': {e}")
        return False


def push_angles(
    output: AgentOutput,
    benchmark_results: list[dict] | None = None,
) -> int:
    """Write all ContentAngle objects from output as markdown files in the vault.

    Returns the count of angles successfully written.
    """
    vault_path = ensure_vault()

    score_map: dict[str, float] = {}
    if benchmark_results:
        for result in benchmark_results:
            headline = result.get("headline", "")
            if headline:
                score_map[headline] = float(result.get("total", 0.0))

    count = 0
    n = 0
    for trend_with_angles in output.results:
        trend = trend_with_angles.trend
        for angle in trend_with_angles.angles:
            total_score = score_map.get(angle.headline, 0.0)
            grade = _grade(total_score)
            if _write_angle_file(
                vault_path=vault_path,
                angle=angle,
                trend=trend,
                grade=grade,
                total_score=total_score,
                n=n,
            ):
                count += 1
            n += 1

    return count


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Parse YAML frontmatter manually — no yaml import needed."""
    result: dict[str, str] = {}
    parts = content.split("---")
    if len(parts) < 3:
        return result
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def fetch_feedback(vault_path: Path) -> dict:
    """Scan vault/angles/ for approved/skipped markdown files.

    Only reads files modified in the last 30 days.
    Returns dict with 'approved' and 'skipped' lists.
    """
    angles_dir = vault_path / "angles"
    if not angles_dir.exists():
        return {"approved": [], "skipped": []}

    approved: list[dict] = []
    skipped: list[dict] = []
    cutoff = datetime.now(tz=timezone.utc).timestamp() - (30 * 24 * 3600)

    try:
        for md_file in sorted(angles_dir.glob("*.md")):
            try:
                if md_file.stat().st_mtime < cutoff:
                    continue
                content = md_file.read_text(encoding="utf-8")
                fm = _parse_frontmatter(content)
                status = fm.get("status", "new").lower()
                if status not in ("approved", "skipped"):
                    continue

                raw_triggers = fm.get("triggers", "[]")
                triggers = [
                    t.strip().strip('"').strip("'")
                    for t in raw_triggers.strip("[]").split(",")
                    if t.strip()
                ]

                # Extract first blockquote line as hook
                hook = ""
                body_section = content.split("---", 2)[-1] if "---" in content else content
                for line in body_section.splitlines():
                    if line.strip().startswith("> "):
                        hook = line.strip()[2:]
                        break

                entry = {
                    "headline": fm.get("headline", ""),
                    "hook": hook,
                    "trend": fm.get("trend", ""),
                    "triggers": triggers,
                    "platform": fm.get("platform", ""),
                }

                if status == "approved":
                    approved.append(entry)
                else:
                    skipped.append(entry)

            except Exception:
                continue

    except Exception as e:
        print(f"[Obsidian] Warning: fetch_feedback scan failed: {e}")

    return {"approved": approved, "skipped": skipped}


def format_feedback_prompt(feedback: dict) -> str:
    """Convert feedback dict into a natural language prompt section for the AI.

    Returns empty string if no feedback yet.
    """
    approved = feedback.get("approved", [])
    skipped = feedback.get("skipped", [])

    if not approved and not skipped:
        return ""

    lines = ["═══ LEARNING FROM PAST REVIEWS ═══"]

    if approved:
        lines.append(
            f"\nThe client APPROVED these angle patterns ({len(approved)} examples):"
        )
        for item in approved:
            triggers_str = ", ".join(item["triggers"]) if item["triggers"] else "none"
            lines.append(f'  • Headline: "{item["headline"]}"')
            lines.append(f"    Triggers: {triggers_str}")

    if skipped:
        lines.append(
            f"\nThe client SKIPPED these angle patterns ({len(skipped)} examples):"
        )
        for item in skipped:
            triggers_str = ", ".join(item["triggers"]) if item["triggers"] else "none"
            lines.append(f'  • Headline: "{item["headline"]}"')
            lines.append(f"    Triggers: {triggers_str}")

    lines.append(
        "\nINSTRUCTIONS: Generate new angles that match APPROVED patterns. "
        "Avoid patterns similar to SKIPPED angles. "
        "Prioritize the psychology triggers that appeared in approved angles."
    )

    return "\n".join(lines)

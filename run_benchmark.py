"""Benchmark runner — CLI script to evaluate marketing agent quality."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent dir to path for running as script
sys.path.insert(0, str(Path(__file__).parent))

from src.benchmark import benchmark_output, format_report, BenchmarkReport
from src.pipeline import run_pipeline
from src.models import AIProvider


REPORT_DIR = Path("/tmp/marketing-agent-data/benchmarks")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


async def run_benchmark(
    mode: str = "mock",
    use_ai_judge: bool = True,
    max_trends: int = 8,
    angles_per_trend: int = 3,
) -> BenchmarkReport:
    """Run a full benchmark cycle."""
    is_mock = mode == "mock"
    provider = None  # Uses default from settings

    print(f"\n{'='*60}")
    print(f"  BENCHMARK — Mode: {mode.upper()}")
    print(f"  AI Judge: {'Gemini' if use_ai_judge else 'Heuristic-only'}")
    print(f"  Trends: {max_trends}, Angles/trend: {angles_per_trend}")
    print(f"{'='*60}\n")

    # Step 1: Generate angles
    print("[1/2] Generating content angles...")
    output = await run_pipeline(
        mock=is_mock,
        max_trends=max_trends,
        angles_per_trend=angles_per_trend,
        provider=provider,
    )

    if not output.results:
        print("❌ No content generated. Check API keys and connectivity.")
        return BenchmarkReport(mode=mode, errors=["No content generated"])

    print(f"  → {output.trend_count} trends, {output.angle_count} angles\n")

    # Step 2: Benchmark
    print("[2/2] Running quality benchmark...")
    report = await benchmark_output(output, use_ai_judge=use_ai_judge, mode=mode)

    # Print report
    print(format_report(report))

    # Print per-angle breakdown
    print("\n--- Per-Angle Breakdown ---")
    for i, score in enumerate(report.scores, 1):
        grade_e = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}.get(score.grade.value, "⚪")
        lang_tag = f"[{'عربي' if score.language == 'ar' else 'EN'}]"
        print(f"\n  {i}. {grade_e} [{score.total:.0f}/60] {lang_tag} {score.headline[:60]}")
        print(f"     CN={score.creative_novelty:.0f} TD={score.psych_trigger_depth:.0f} VM={score.viral_mechanics:.0f} "
              f"BA={score.brand_alignment:.0f} CR={score.cultural_relevance:.0f} HP={score.hook_power:.0f}")
        if score.cliches_found:
            print(f"     🚩 Clichés: {', '.join(score.cliches_found)}")
        if score.heuristic_flags:
            for flag in score.heuristic_flags:
                print(f"     {flag}")
        if score.justification:
            print(f"     💬 {score.justification[:120]}")

    # Save JSON report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"benchmark_{mode}_{timestamp}.json"
    report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2, default=str))
    print(f"\n📄 Report saved: {report_path}\n")

    return report


async def run_comparison():
    """Run mock vs heuristic-only comparison (no Gemini needed)."""
    print("\n" + "🔄 " * 20)
    print("  COMPARISON: Mock (heuristic) vs Mock (AI judge)")
    print("🔄 " * 20 + "\n")

    # Heuristic-only
    print("═══ Round 1: Heuristic-only scoring ═══")
    r1 = await run_benchmark(mode="mock", use_ai_judge=False, max_trends=4, angles_per_trend=3)

    # AI judge
    print("\n═══ Round 2: Gemini AI Judge scoring ═══")
    r2 = await run_benchmark(mode="mock", use_ai_judge=True, max_trends=4, angles_per_trend=3)

    # Comparison
    print("\n" + "="*60)
    print("  COMPARISON RESULTS")
    print("="*60)
    print(f"  {'Dimension':<25} {'Heuristic':>10} {'AI Judge':>10} {'Delta':>10}")
    print(f"  {'-'*55}")

    dims = [
        ("Creative Novelty", r1.avg_creative_novelty, r2.avg_creative_novelty),
        ("Psych Trigger Depth", r1.avg_psych_trigger_depth, r2.avg_psych_trigger_depth),
        ("Viral Mechanics", r1.avg_viral_mechanics, r2.avg_viral_mechanics),
        ("Brand Alignment", r1.avg_brand_alignment, r2.avg_brand_alignment),
        ("Cultural Relevance", r1.avg_cultural_relevance, r2.avg_cultural_relevance),
        ("Hook Power", r1.avg_hook_power, r2.avg_hook_power),
    ]

    for name, h, ai in dims:
        delta = ai - h
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        print(f"  {name:<25} {h:>10.1f} {ai:>10.1f} {arrow:>2}{abs(delta):>7.1f}")

    print(f"\n  {'TOTAL':<25} {r1.avg_total:>10.1f} {r2.avg_total:>10.1f}")
    print(f"  {'GRADE':<25} {r1.overall_grade.value:>10} {r2.overall_grade.value:>10}\n")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Marketing Agent Quality Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py --mode mock              Mock data + AI judge
  python run_benchmark.py --mode mock --no-judge    Mock data + heuristic only (no API keys needed)
  python run_benchmark.py --mode live               Live Tavily + AI judge
  python run_benchmark.py --compare                 Compare heuristic vs AI judge
        """,
    )
    parser.add_argument("--mode", choices=["mock", "live"], default="mock",
                        help="Data mode: mock (built-in) or live (Tavily API)")
    parser.add_argument("--no-judge", action="store_true",
                        help="Skip AI judge, use heuristic scoring only")
    parser.add_argument("--compare", action="store_true",
                        help="Run comparison: heuristic vs AI judge")
    parser.add_argument("--trends", type=int, default=8,
                        help="Max trends to scan (default: 8)")
    parser.add_argument("--angles", type=int, default=3,
                        help="Angles per trend (default: 3)")

    args = parser.parse_args()

    if args.compare:
        asyncio.run(run_comparison())
    else:
        asyncio.run(run_benchmark(
            mode=args.mode,
            use_ai_judge=not args.no_judge,
            max_trends=args.trends,
            angles_per_trend=args.angles,
        ))


if __name__ == "__main__":
    main()

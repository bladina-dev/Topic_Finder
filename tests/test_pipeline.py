"""Tests for pipeline.py — Phase 6: deduplicate_and_score."""

from __future__ import annotations

import pytest

from src.models import Trend, TrendSource, TopicOrigin
from src.pipeline import deduplicate_and_score


def _make_trend(title: str, origin: TopicOrigin, jack: float) -> Trend:
    return Trend(title=title, source=TrendSource.GULF_NEWS, origin=origin, jack_potential=jack)


# ---------------------------------------------------------------------------
# Cross-layer boost
# ---------------------------------------------------------------------------

def test_dedup_boost_for_multi_origin():
    """A topic appearing in both TREND and INFLUENCER layers gets +0.1 boost."""
    trends = [
        _make_trend("Saudi AI Summit", TopicOrigin.TREND, 0.7),
        _make_trend("Saudi AI Summit", TopicOrigin.INFLUENCER, 0.65),
    ]
    result = deduplicate_and_score(trends)

    assert len(result) == 1
    assert abs(result[0].jack_potential - 0.8) < 1e-9


def test_dedup_boost_capped_at_one():
    """Boost never exceeds 1.0."""
    trends = [
        _make_trend("NEOM City", TopicOrigin.TREND, 0.95),
        _make_trend("NEOM City", TopicOrigin.INFLUENCER, 0.90),
    ]
    result = deduplicate_and_score(trends)

    assert len(result) == 1
    assert result[0].jack_potential == 1.0


def test_dedup_no_boost_single_origin():
    """A topic with only TREND origin gets no boost."""
    trends = [
        _make_trend("Riyadh Tech Week", TopicOrigin.TREND, 0.75),
        _make_trend("Riyadh Tech Week", TopicOrigin.TREND, 0.70),
    ]
    result = deduplicate_and_score(trends)

    assert len(result) == 1
    assert abs(result[0].jack_potential - 0.75) < 1e-9


# ---------------------------------------------------------------------------
# Dedup keeps highest jack_potential
# ---------------------------------------------------------------------------

def test_dedup_keeps_highest_jack_potential():
    """Among duplicates, the trend with highest jack_potential is kept."""
    trends = [
        _make_trend("Vision 2030 Update", TopicOrigin.TREND, 0.6),
        _make_trend("Vision 2030 Update", TopicOrigin.TREND, 0.85),
        _make_trend("Vision 2030 Update", TopicOrigin.TREND, 0.72),
    ]
    result = deduplicate_and_score(trends)

    assert len(result) == 1
    assert abs(result[0].jack_potential - 0.85) < 1e-9


# ---------------------------------------------------------------------------
# Three-layer boost
# ---------------------------------------------------------------------------

def test_dedup_boost_three_distinct_origins():
    """Topic in TREND + INFLUENCER + SEED_KEYWORD still gets exactly +0.1 boost."""
    trends = [
        _make_trend("Saudi Fintech", TopicOrigin.TREND, 0.6),
        _make_trend("Saudi Fintech", TopicOrigin.INFLUENCER, 0.55),
        _make_trend("Saudi Fintech", TopicOrigin.SEED_KEYWORD, 0.5),
    ]
    result = deduplicate_and_score(trends)

    assert len(result) == 1
    assert abs(result[0].jack_potential - 0.7) < 1e-9


# ---------------------------------------------------------------------------
# Sort order
# ---------------------------------------------------------------------------

def test_dedup_result_sorted_by_jack_potential_descending():
    """Output is sorted highest jack_potential first."""
    trends = [
        _make_trend("Topic A", TopicOrigin.TREND, 0.5),
        _make_trend("Topic B", TopicOrigin.TREND, 0.9),
        _make_trend("Topic C", TopicOrigin.TREND, 0.7),
    ]
    result = deduplicate_and_score(trends)

    scores = [t.jack_potential for t in result]
    assert scores == sorted(scores, reverse=True)

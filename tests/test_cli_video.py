"""Integration tests for the 'video' CLI command."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from src.cli import app
from src.models import AgentOutput, ContentAngle, Trend, TrendSource, TrendWithAngles

runner = CliRunner()

_VIDEO_STUB = {
    "id": "fahad-ep-test-ai",
    "title": "Test video",
    "pillar": "ai",
    "scenes": [{"type": "hook"}, {"type": "cta"}],
}


def _make_agent_output() -> tuple[AgentOutput, ContentAngle, ContentAngle]:
    """Minimal AgentOutput with 1 trend and 2 angles."""
    trend = Trend(title="AI jobs Saudi", source=TrendSource.GOOGLE_TRENDS)
    angle1 = ContentAngle(
        headline="First angle", hook="Hook one", brand_alignment_score=0.5
    )
    angle2 = ContentAngle(
        headline="Second angle", hook="Hook two", brand_alignment_score=0.8
    )
    output = AgentOutput(
        trend_count=1,
        angle_count=2,
        results=[TrendWithAngles(trend=trend, angles=[angle1, angle2])],
    )
    return output, angle1, angle2


def test_video_mock_creates_json_file(tmp_path):
    """--mock flag: pipeline runs, JSON file is written to output dir."""
    output, _, _ = _make_agent_output()
    mock_pipeline = AsyncMock(return_value=output)
    mock_converter = AsyncMock(return_value=_VIDEO_STUB)

    with (
        patch("src.pipeline.run_pipeline", mock_pipeline),
        patch("src.video_converter.angle_to_video_data", mock_converter),
    ):
        result = runner.invoke(app, ["video", "--mock", "--output", str(tmp_path)])

    assert result.exit_code == 0
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert "scenes" in data


def test_video_pick_selects_second_angle(tmp_path):
    """--pick 2 passes the second angle (index 1) to angle_to_video_data."""
    output, _, angle2 = _make_agent_output()
    mock_pipeline = AsyncMock(return_value=output)
    mock_converter = AsyncMock(return_value=_VIDEO_STUB)

    with (
        patch("src.pipeline.run_pipeline", mock_pipeline),
        patch("src.video_converter.angle_to_video_data", mock_converter),
    ):
        result = runner.invoke(
            app, ["video", "--mock", "--pick", "2", "--output", str(tmp_path)]
        )

    assert result.exit_code == 0
    called_angle = mock_converter.call_args[0][0]
    assert called_angle.headline == angle2.headline


def test_video_no_angles_exits_with_error():
    """Empty pipeline output triggers exit code 1 with 'No angles' message."""
    empty_output = AgentOutput(trend_count=0, angle_count=0, results=[])
    mock_pipeline = AsyncMock(return_value=empty_output)

    with patch("src.pipeline.run_pipeline", mock_pipeline):
        result = runner.invoke(app, ["video", "--mock"])

    assert result.exit_code == 1
    assert "No angles" in result.output

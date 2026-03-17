"""Tests for src/video_assembler.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.video_assembler import assemble_video


def test_assemble_video_raises_when_ffmpeg_not_found():
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="ffmpeg not found"):
            assemble_video("video.mp4", None, None, "output.mp4")


def test_assemble_video_correct_ffmpeg_command(tmp_path):
    video_path = str(tmp_path / "video.mp4")
    voiceover_path = str(tmp_path / "voice.mp3")
    output_path = str(tmp_path / "final.mp4")

    mock_result = MagicMock(returncode=0)

    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = assemble_video(video_path, voiceover_path, None, output_path)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "ffmpeg"
    assert video_path in cmd
    assert voiceover_path in cmd
    assert output_path in cmd
    assert result == output_path

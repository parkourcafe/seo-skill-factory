from __future__ import annotations

import unittest

from seo_skill_factory.config import AppConfig
from seo_skill_factory.gemini import (
    _fetch_transcript_segments,
    _format_timestamp,
    _format_transcript,
    build_analyzer,
    build_video_prompt,
)
from seo_skill_factory.models import VideoMetadata


def _video() -> VideoMetadata:
    return VideoMetadata(
        video_id="vid123",
        title="Relevance Engineering explained",
        description="A talk about query fan-out.",
        published_at="2026-01-15T00:00:00Z",
        duration="PT20M",
        duration_seconds=1200,
        url="https://www.youtube.com/watch?v=vid123",
        caption_available=True,
    )


class FakeClassmethodApi:
    @classmethod
    def get_transcript(cls, video_id, languages):  # noqa: ARG003
        return [
            {"text": "hello world", "start": 0.0, "duration": 2.0},
            {"text": "second line", "start": 65.4, "duration": 2.0},
        ]


class FakeSnippet:
    def __init__(self, text, start):
        self.text = text
        self.start = start


class FakeInstanceApi:
    def fetch(self, video_id, languages):  # noqa: ARG002
        return [FakeSnippet("instance one", 5), FakeSnippet("instance two", 130)]


class TranscriptTests(unittest.TestCase):
    def test_format_timestamp(self) -> None:
        self.assertEqual(_format_timestamp(0), "0:00")
        self.assertEqual(_format_timestamp(5), "0:05")
        self.assertEqual(_format_timestamp(65), "1:05")
        self.assertEqual(_format_timestamp(3661.9), "61:01")

    def test_format_timestamp_handles_bad_values(self) -> None:
        self.assertEqual(_format_timestamp(None), "0:00")
        self.assertEqual(_format_timestamp("nope"), "0:00")
        self.assertEqual(_format_timestamp(-3), "0:00")

    def test_format_transcript_prefixes_timestamps_and_skips_empty(self) -> None:
        segments = [
            {"text": "first", "start": 0},
            {"text": "   ", "start": 10},
            {"text": "later", "start": 90},
        ]
        self.assertEqual(_format_transcript(segments), "[0:00] first\n[1:30] later")

    def test_fetch_segments_supports_classmethod_api(self) -> None:
        segments = _fetch_transcript_segments(FakeClassmethodApi, "vid123", ["en"])
        self.assertEqual([s["text"] for s in segments], ["hello world", "second line"])
        self.assertEqual(_format_transcript(segments), "[0:00] hello world\n[1:05] second line")

    def test_fetch_segments_supports_instance_api(self) -> None:
        segments = _fetch_transcript_segments(FakeInstanceApi, "vid123", ["en"])
        self.assertEqual([s["text"] for s in segments], ["instance one", "instance two"])
        self.assertEqual(_format_transcript(segments), "[0:05] instance one\n[2:10] instance two")

    def test_prompt_without_transcript_uses_video_intro(self) -> None:
        prompt = build_video_prompt(_video(), AppConfig())
        self.assertIn("Analyze this YouTube video as source material", prompt)
        self.assertNotIn("Transcript (each line", prompt)

    def test_prompt_with_transcript_embeds_text_and_switches_intro(self) -> None:
        prompt = build_video_prompt(_video(), AppConfig(), transcript="[0:00] hello world")
        self.assertIn("Analyze this YouTube video transcript as source material", prompt)
        self.assertIn("Transcript (each line", prompt)
        self.assertIn("[0:00] hello world", prompt)

    def test_build_analyzer_rejects_unknown_source(self) -> None:
        with self.assertRaises(ValueError):
            build_analyzer(AppConfig(), source="audio")


if __name__ == "__main__":
    unittest.main()

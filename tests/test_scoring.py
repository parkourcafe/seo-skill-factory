from __future__ import annotations

import unittest

from seo_skill_factory.models import VideoMetadata
from seo_skill_factory.scoring import filter_videos, score_video
from seo_skill_factory.youtube import parse_iso8601_duration, parse_playlist_id


class ScoringTests(unittest.TestCase):
    def test_scores_relevance_and_ai_search_topics(self) -> None:
        video = VideoMetadata(
            video_id="abc",
            title="AI Search Relevance Engineering with query fan-out",
            description="Case study on embeddings, RAG, measurement, and Technical SEO.",
            published_at="2026-01-15T00:00:00Z",
            duration="PT20M",
            duration_seconds=1200,
            url="https://www.youtube.com/watch?v=abc",
            caption_available=True,
        )

        scored = score_video(video)

        self.assertEqual(scored.score, 13)
        self.assertTrue(any("AI Search" in reason for reason in scored.score_reasons))

    def test_penalizes_old_non_foundational_video(self) -> None:
        video = VideoMetadata(
            video_id="old",
            title="Random SEO update",
            description="News only.",
            published_at="2021-01-15T00:00:00Z",
            duration="PT10M",
            duration_seconds=600,
            url="https://www.youtube.com/watch?v=old",
            caption_available=True,
        )

        self.assertEqual(score_video(video).score, -2)

    def test_filtering_respects_duration_captions_and_keywords(self) -> None:
        videos = [
            VideoMetadata("a", "AI Search audit", "", "2025-01-01T00:00:00Z", "PT10M", 600, "u", True),
            VideoMetadata("b", "AI Search short", "", "2025-01-01T00:00:00Z", "PT1M", 60, "u", True),
            VideoMetadata("c", "AI Search no captions", "", "2025-01-01T00:00:00Z", "PT10M", 600, "u", False),
        ]

        result = filter_videos(
            videos,
            year_min=2023,
            year_max=2026,
            include_keywords=["AI Search"],
            exclude_keywords=[],
            min_duration_seconds=300,
            max_duration_seconds=1200,
            require_captions=True,
        )

        self.assertEqual([video.video_id for video in result], ["a"])

    def test_duration_parser(self) -> None:
        self.assertEqual(parse_iso8601_duration("PT1H2M3S"), 3723)
        self.assertEqual(parse_iso8601_duration("PT45M"), 2700)

    def test_playlist_url_parser(self) -> None:
        self.assertEqual(parse_playlist_id("https://www.youtube.com/playlist?list=PL123"), "PL123")


if __name__ == "__main__":
    unittest.main()


from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from seo_skill_factory.config import AppConfig, ProjectConfig
from seo_skill_factory.synthesis import synthesize


class SynthesisTests(unittest.TestCase):
    def test_synthesizes_working_skill_with_status_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "per_video_json"
            input_dir.mkdir()
            (input_dir / "abc.json").write_text(
                json.dumps(
                    {
                        "video_id": "abc",
                        "title": "AI Search Relevance Engineering",
                        "published_at": "2026-01-01T00:00:00Z",
                        "url": "https://www.youtube.com/watch?v=abc",
                        "main_topics": ["AI Search"],
                        "principles": ["[VERIFIED] Measure AI visibility from citations and source overlap."],
                        "rules_and_heuristics": ["Map query fan-out before drafting content."],
                        "frameworks": ["[INTERPRETED] Relevance engineering framework"],
                        "workflows": ["[INTERPRETED] Build retrieval-friendly passages for query variants."],
                        "checklists": ["Confirm citation eligibility."],
                        "examples": ["Demo showed source overlap."],
                        "anti_patterns": ["Do not chase generic rankings without visibility evidence."],
                        "tools_mentioned": ["Search Console"],
                        "evidence": ["Case data and demo"],
                        "possible_outdated_tactics": [],
                        "quotes_or_timestamps": [],
                    }
                ),
                encoding="utf-8",
            )
            config = AppConfig(
                project=ProjectConfig(
                    output_dir=root / "outputs",
                    author_name="Mike King",
                    niche="SEO and AI Search",
                    output_language="en",
                )
            )

            outputs = synthesize(input_dir, config)
            skill = outputs["skill"].read_text(encoding="utf-8")

            self.assertIn("## Role", skill)
            self.assertIn("## AI Search Workflow", skill)
            self.assertIn("[VERIFIED] Measure AI visibility", skill)
            self.assertIn("[INTERPRETED] Map query fan-out", skill)


if __name__ == "__main__":
    unittest.main()


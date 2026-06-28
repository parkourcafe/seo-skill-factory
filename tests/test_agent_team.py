from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from seo_skill_factory.agent_team import build_agent_team
from seo_skill_factory.config import AgentTeamConfig, AppConfig, ProjectConfig


class AgentTeamTests(unittest.TestCase):
    def test_builds_agent_team_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            spec_path = root / "spec.md"
            spec_path.write_text("# Spec\n\n## Agent Team\n\nRules.", encoding="utf-8")
            config = AppConfig(
                project=ProjectConfig(output_dir=root / "outputs", author_name="Source Author", niche="SEO"),
                agent_team=AgentTeamConfig(
                    source_spec=str(spec_path),
                    business_name="KORA Food Hall",
                    domain="korafoodhall.com",
                    case_context="Ubud pilot case.",
                    languages=["en", "ru", "id"],
                ),
            )

            outputs = build_agent_team(config)

            self.assertIn("team_skill", outputs)
            self.assertTrue(outputs["team_skill"].exists())
            self.assertTrue(outputs["agent_relevance_engineer"].exists())
            self.assertTrue(outputs["schema_technical_audit_output"].exists())
            self.assertTrue(outputs["manifest"].exists())

            team_skill = outputs["team_skill"].read_text(encoding="utf-8")
            self.assertIn("Controlled SEO/GEO Agent Team Skill", team_skill)
            self.assertIn("Human Approver", team_skill)
            self.assertNotIn("agent Mike King", team_skill)

            schema = json.loads(outputs["schema_content_brief_output"].read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

            manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))
            self.assertIn("relevance_engineer", manifest["roles"])
            self.assertEqual(manifest["business_name"], "KORA Food Hall")


if __name__ == "__main__":
    unittest.main()


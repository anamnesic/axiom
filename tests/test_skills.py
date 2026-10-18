"""Automated validation suite for AXIOM Agent Skills Library."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

from axiom.setup_agent import run_doctor


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"


class TestSkillsLibrary(unittest.TestCase):
    """Test suite validating all Agent Skills in skills/."""

    def test_skills_directory_exists(self) -> None:
        self.assertTrue(SKILLS_DIR.exists())
        self.assertTrue(SKILLS_DIR.is_dir())

    def test_all_skills_have_valid_frontmatter(self) -> None:
        skill_files = list(SKILLS_DIR.glob("**/SKILL.md"))
        self.assertGreaterEqual(len(skill_files), 15)

        for skill_path in skill_files:
            rel_path = skill_path.relative_to(ROOT)
            text = skill_path.read_text(encoding="utf-8")
            self.assertTrue(
                text.startswith("---"),
                f"Skill file {rel_path} must begin with YAML frontmatter delimiter '---'",
            )
            parts = text.split("---", 2)
            self.assertGreaterEqual(
                len(parts),
                3,
                f"Skill file {rel_path} must contain closed YAML frontmatter '---'",
            )
            frontmatter = parts[1]
            lines = [line.strip() for line in frontmatter.splitlines() if line.strip()]
            has_name = any(line.startswith("name:") for line in lines)
            has_desc = any(line.startswith("description:") for line in lines)
            self.assertTrue(has_name, f"Skill file {rel_path} is missing 'name:' in frontmatter")
            self.assertTrue(has_desc, f"Skill file {rel_path} is missing 'description:' in frontmatter")

    def test_taxonomy_pillars_present(self) -> None:
        pillars = ["formal", "research", "computational", "verification", "scientific"]
        for p in pillars:
            pillar_dir = SKILLS_DIR / p
            self.assertTrue(
                pillar_dir.exists() and pillar_dir.is_dir(),
                f"Taxonomy pillar directory '{p}' must exist under skills/",
            )
            skill_files = list(pillar_dir.glob("**/SKILL.md"))
            self.assertGreaterEqual(
                len(skill_files),
                2,
                f"Pillar '{p}' must contain at least 2 specialized skills",
            )

    def test_doctor_reports_skills(self) -> None:
        report = run_doctor()
        self.assertIn("skills_count", report)
        self.assertGreaterEqual(report["skills_count"], 15)
        names = [s["name"] for s in report.get("skills", [])]
        self.assertIn("mathematics", names)
        self.assertIn("toolchain-management", names)
        self.assertIn("axiom-lean4-proofs", names)
        self.assertIn("axiom-math-research", names)
        self.assertIn("axiom-fluidsim-pde", names)
        self.assertIn("axiom-property-based-testing", names)
        self.assertIn("axiom-reproducibility-statement", names)


if __name__ == "__main__":
    unittest.main()

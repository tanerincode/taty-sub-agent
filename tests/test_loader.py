from pathlib import Path
from src.skills.loader import _parse_skill_file, load_skills_from_dir


VALID_SKILL = """\
---
name: test-agent
description: A test agent for unit tests
---
You are a test agent. Your job is to write tests.
"""


def test_parse_valid_skill(tmp_path):
    f = tmp_path / "test-agent.md"
    f.write_text(VALID_SKILL)
    skill = _parse_skill_file(f)
    assert skill is not None
    assert skill.name == "test-agent"
    assert skill.description == "A test agent for unit tests"
    assert "write tests" in skill.content


def test_parse_missing_description(tmp_path):
    f = tmp_path / "bad.md"
    f.write_text("---\nname: bad\n---\nsome content")
    skill = _parse_skill_file(f)
    assert skill is None


def test_load_skills_from_dir(tmp_path):
    (tmp_path / "skill1.md").write_text(VALID_SKILL)
    (tmp_path / "skill2.md").write_text(VALID_SKILL.replace("test-agent", "skill2"))
    skills = load_skills_from_dir(str(tmp_path))
    assert len(skills) == 2


def test_load_skills_empty_dir(tmp_path):
    skills = load_skills_from_dir(str(tmp_path))
    assert skills == []

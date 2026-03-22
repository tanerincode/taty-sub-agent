"""
Skill loader: reads .md skill files from disk and stores them into Synatyx.

Skill file format:
---
name: nodejs-developer
description: Senior Node.js developer for building APIs, services, and tooling
---
<full system prompt / role definition>
"""
import re
from pathlib import Path
from typing import Optional
from src.core.models import Skill
from src.core.config import settings


def _parse_skill_file(path: Path) -> Optional[Skill]:
    text = path.read_text(encoding="utf-8")

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return None

    frontmatter_raw, content = match.group(1), match.group(2).strip()

    meta: dict = {}
    for line in frontmatter_raw.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()

    name = meta.get("name") or path.stem
    description = meta.get("description", "")
    if not description:
        return None

    return Skill(name=name, description=description, content=content)


def load_skills_from_dir(skills_dir: Optional[str] = None) -> list[Skill]:
    base = Path(skills_dir or settings.skills_dir)
    if not base.exists():
        return []
    skills = []
    for path in sorted(base.glob("*.md")):
        skill = _parse_skill_file(path)
        if skill:
            skills.append(skill)
    return skills

"""
Seed all skill files from the skills/ directory into Synatyx.
Run once after adding new skill files.

Usage:
    python scripts/seed_skills.py
"""
import asyncio
import httpx
import json
from src.loader import load_skills_from_dir
from src.config import settings


SYNATYX_BASE = "http://localhost:8000"  # adjust if different


async def seed():
    skills = load_skills_from_dir()
    if not skills:
        print("No skills found in skills/ directory.")
        return

    async with httpx.AsyncClient(base_url=SYNATYX_BASE) as client:
        for skill in skills:
            payload = {
                "name": skill.name,
                "description": skill.description,
                "content": skill.content,
                "user_id": settings.synatyx_user_id,
                "project": settings.synatyx_project,
            }
            try:
                resp = await client.post("/context/skill/store", json=payload)
                resp.raise_for_status()
                print(f"  stored: {skill.name}")
            except Exception as e:
                print(f"  failed: {skill.name} — {e}")


if __name__ == "__main__":
    asyncio.run(seed())

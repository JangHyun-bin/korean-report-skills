# -*- coding: utf-8 -*-
"""테스트 공통 경로·픽스처."""
import pathlib
import sys

# 스킬 폴더는 그대로 ~/.claude/skills/ 로 복사된다. 검사가 .pyc 를 남기지 않게 한다.
sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugins" / "korean-report" / "skills"
DOC = SKILLS / "korean-report-doc"
STYLE = SKILLS / "korean-report-style"
ASSETS = DOC / "assets"
CSS = ASSETS / "css"

sys.path.insert(0, str(ASSETS))


def read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def css_bundle() -> str:
    return "\n".join(read(CSS / f) for f in ("base.css", "paper.css", "deck.css"))


def all_markdown() -> list[pathlib.Path]:
    return sorted(
        p for p in ROOT.rglob("*.md")
        if "node_modules" not in p.parts and "dist" not in p.parts and ".git" not in p.parts
    )

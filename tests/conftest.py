# -*- coding: utf-8 -*-
"""테스트 공통 경로·픽스처."""
import pathlib
import subprocess
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
    """
    저장소가 관리하는 마크다운만 돌려준다.

    파일 계통을 직접 훑고 제외 목록을 손으로 유지하면 반드시 어긋난다 —
    작업용 디렉터리 하나가 늘 때마다 검사가 엉뚱한 파일을 걸고 넘어졌다.
    무엇이 저장소의 것인지는 git 이 이미 알고 있으므로 git 에게 묻는다.
    추적 중인 파일에 더해 아직 add 하지 않은 파일도 포함하되,
    .gitignore 가 제외한 것은 빼낸다.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.md"],
        cwd=ROOT, capture_output=True, check=True, text=True, encoding="utf-8",
    ).stdout
    return sorted(ROOT / rel for rel in out.split("\0") if rel)

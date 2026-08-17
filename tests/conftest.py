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
STYLE_ASSETS = STYLE / "assets"

sys.path.insert(0, str(ASSETS))
sys.path.insert(0, str(STYLE_ASSETS))


def read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def css_bundle() -> str:
    return "\n".join(read(CSS / f) for f in ("base.css", "paper.css", "deck.css"))


def all_markdown() -> list[pathlib.Path]:
    """
    저장소 또는 npm 배포물에 포함된 Markdown만 돌려준다.

    파일 계통을 직접 훑고 제외 목록을 손으로 유지하면 반드시 어긋난다 —
    작업용 디렉터리 하나가 늘 때마다 검사가 엉뚱한 파일을 걸고 넘어졌다.
    Git checkout에서는 Git이 관리하는 목록을 우선 사용한다.
    추적 중인 파일에 더해 아직 add 하지 않은 파일도 포함하되,
    .gitignore가 제외한 것은 빼낸다. `.git`이 없는 npm tarball에서는
    배포 경로를 직접 순회하고 생성 디렉터리를 제외한다.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.md"],
            cwd=ROOT, capture_output=True, check=False, text=True, encoding="utf-8",
        )
    except FileNotFoundError:
        result = None
    if result is not None and result.returncode == 0:
        return sorted(ROOT / rel for rel in result.stdout.split("\0") if rel)

    generated = {".git", ".venv", ".pytest_cache", "__pycache__", "dist", "node_modules"}
    return sorted(path for path in ROOT.rglob("*.md") if not generated.intersection(path.parts))

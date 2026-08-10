# -*- coding: utf-8 -*-
"""
저장소 자신의 산문이 자기 규약을 지키는지 검사한다.

`CONTRIBUTING` 과 `korean-report-style` §6 은 검사 범위에 「본문 산문 — 규칙을
서술하는 문장 자신이 규칙을 위반하는 경우가 있다」를 넣어 두었다.
그래 놓고 저장소 자신의 산문은 아무도 검사하지 않았다. 실제로 README 절 제목이
`## 무엇이 달라지나` 였고, 바로 아래 표에서 그 형태를 나쁜 예로 들고 있었다.

**규칙 목록을 따로 만들지 않는다.** `substitutions.md` 의 「쓰지 않는다」 열을 읽어
그대로 검사에 쓴다. 표를 고치면 검사도 함께 바뀐다.

검사 대상은 **규약이 적용되는 장르**뿐이다 — 스킬 문서와 결정 기록.
README · INSTALL · CONTRIBUTING · Pages 는 처음 온 사람에게 문제를 알아보게 하는
글이므로 대상이 아니다. 그 사실은 README 에 명시되어 있다.
"""
import re

import pytest
from conftest import ROOT, STYLE, read

# 규약이 적용되는 장르
TARGETS = sorted(
    list((ROOT / "skills").rglob("*.md")) + list((ROOT / "docs" / "decisions").rglob("*.md"))
)

# 인용·예시 자리. 나쁜 형태를 보여주려면 그 형태를 적어야 한다.
QUOTED = re.compile(r"`[^`]*`|「[^」]*」|\"[^\"]*\"|'[^']*'|“[^”]*”")
EXEMPT = "style-exempt"


def substitution_lefts() -> list[str]:
    """치환표의 「쓰지 않는다」 열. 이것이 곧 검사 규칙이다."""
    out, in_table = [], False
    for ln in read(STYLE / "references" / "substitutions.md").splitlines():
        if not ln.startswith("|"):
            in_table = False
            continue
        if "쓰지 않는다" in ln or "찾기" in ln or "| 광의 " in ln:
            in_table = True
            continue
        if in_table and not re.match(r"^\|\s*-", ln):
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if cells and cells[0]:
                out.append(re.sub(r"[`*]", "", cells[0]).split("(")[0].strip())
    return [w for w in out if len(w) >= 2]


def prose_lines(path):
    """
    산문만 돌려준다. 다음은 규칙을 **가르치는** 자리이므로 제외한다.
      · 코드 블록 · 인용문 · 표 행 (전부 규칙 예시다)
      · 백틱 · 「」 · 따옴표 안
      · style-exempt 주석이 달린 줄
    """
    fence = False
    for i, ln in enumerate(read(path).splitlines(), 1):
        s = ln.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or s.startswith(">") or s.startswith("|") or EXEMPT in s:
            continue
        yield i, QUOTED.sub("", ln)


def test_own_prose_avoids_its_own_substitution_table():
    """치환표의 「쓰지 않는다」 표현을 저장소 산문이 쓰고 있지 않은지."""
    lefts = substitution_lefts()
    assert len(lefts) > 50, "치환표를 읽지 못하였다"

    found = []
    for p in TARGETS:
        for i, ln in prose_lines(p):
            for w in lefts:
                if w in ln:
                    found.append(f"{p.relative_to(ROOT)}:{i} [{w}] {ln.strip()[:60]}")
    assert not found, (
        "규약을 서술하는 문서가 자기 규약을 어긴다:\n  " + "\n  ".join(found) +
        "\n\n인용이 꼭 필요하면 백틱·「」로 감싸거나 줄 끝에 <!-- style-exempt --> 를 단다."
    )


# 서술형·의문형 종결. 명사가 이렇게 끝나는 일은 드물다 —
# 「개요」·「추가」·「숫자」가 걸리지 않도록 종결형만 좁게 잡는다.
BAD_HEADING = re.compile(r"(?:다|까)$|[?!]$|(?:은|는|한|인)가$")


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: p.name)
def test_section_headings_are_noun_phrases(path):
    """§1.1 — 서술형 제목은 논평처럼 읽히고 문서 개정 시 낡는다."""
    bad = []
    fence = False
    for i, ln in enumerate(read(path).splitlines(), 1):
        s = ln.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s.startswith("#") or EXEMPT in s:
            continue
        title = re.sub(r"^#+\s*", "", s)
        title = re.sub(r"^[\d.]+\s*", "", title).strip().rstrip(".")
        if not re.search(r"[가-힣]", title):      # 영문 표제는 대상이 아니다
            continue
        if BAD_HEADING.search(title):
            bad.append(f"{path.relative_to(ROOT)}:{i}  {title}")
    assert not bad, "서술형·의문형 절 제목:\n  " + "\n  ".join(bad)

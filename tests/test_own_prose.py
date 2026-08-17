# -*- coding: utf-8 -*-
"""
저장소 자신의 산문이 자기 규약을 지키는지 검사한다.

`CONTRIBUTING` 과 `korean-report-style` §6 은 검사 범위에 「본문 산문 — 규칙을
서술하는 문장 자신이 규칙을 위반하는 경우가 있다」를 넣어 두었다.
그래 놓고 저장소 자신의 산문은 아무도 검사하지 않았다. 실제로 README 절 제목이
`## 무엇이 달라지나` 였고, 바로 아래 표에서 그 형태를 나쁜 예로 들고 있었다.

**검사 논리를 여기 두지 않는다.** 스킬이 사용자에게 배포하는 검사기
(`korean-report-style/assets/lint.py`) 를 그대로 불러 쓴다. 사용자가 받는 것과
저장소가 자신에게 적용하는 것이 같아야 한다 — 둘로 갈라지면 배포본 쪽이 먼저 낡는다.

검사 대상은 규약을 설명하거나 제품 동작을 약속하는 문서다. 스킬 문서와 설계 문서뿐 아니라
README와 INSTALL도 같은 검사기를 통과해야 한다. 공개 안내 문서를 제외하면 제품이 사용자에게
요구하는 문체와 저장소가 실제로 사용하는 문체가 다시 분리된다.
"""
import lint
import pytest
from conftest import ROOT, read

# 규약이 적용되는 장르
TARGETS = sorted(
    list((ROOT / "plugins").rglob("*.md"))
    + list((ROOT / "docs" / "design").rglob("*.md"))
    + [ROOT / "README.md", ROOT / "INSTALL.md"]
)

RULES = lint.load_rules()


def test_the_shipped_linter_reads_the_whole_table():
    """규칙을 못 읽고도 조용히 통과하면 아래 검사가 전부 무의미해진다."""
    assert len(RULES) > 100, f"치환표에서 규칙을 {len(RULES)}개밖에 읽지 못하였다"
    assert any(r["tier"] == "고침" for r in RULES), "§1 어미가 고침 갈래로 읽히지 않았다"
    assert any(r["tier"] == "검토" for r in RULES), "§2~§8 이 검토 갈래로 읽히지 않았다"


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: p.name)
def test_own_prose_follows_its_own_conventions(path):
    """치환표의 「쓰지 않는다」 표현과 서술형 제목을 저장소 산문이 쓰고 있지 않은지."""
    found = lint.lint(read(path), str(path.relative_to(ROOT)), RULES)
    assert not found, (
        "규약을 서술하는 문서가 자기 규약을 어긴다:\n  "
        + "\n  ".join(f"{f.path}:{f.line}:{f.col} [{f.tier}] {f.found}" for f in found)
        + "\n\n인용이 꼭 필요하면 백틱·「」로 감싸거나 줄 끝에 <!-- style-exempt --> 를 단다."
    )

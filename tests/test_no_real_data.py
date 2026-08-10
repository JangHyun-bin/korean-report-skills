# -*- coding: utf-8 -*-
"""
실제 사업 데이터가 저장소에 다시 들어오지 못하게 막는다.

한 번 지우는 것보다 이쪽이 중요하다. 공개 저장소에서 진짜 위험은
나중에 누군가 편의상 실제 사례를 예시로 넣는 것이고, 검사가 없으면 반드시 재발한다.
공개된 뒤에는 이력 재작성이 필요하고 옛 커밋 객체는 SHA 로 남는다.

예시는 전부 가상 사례 「A사 — 인라인 계측 체계 확립과 수율 개선」에서 나온다.
"""
import hashlib
import re

import pytest
from conftest import ROOT, STYLE, read

# 검사 대상 — 배포되는 것과 예시. dist/ · node_modules/ 는 산출물이라 제외한다.
SCANNED_SUFFIXES = (".md", ".py", ".js", ".css", ".html", ".sh", ".toml", ".json", ".yml")
EXCLUDED_DIRS = {"node_modules", "dist", ".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
# 이 파일 자신은 금지어를 나열하므로 검사에서 뺀다.
SELF = "test_no_real_data.py"


def scanned_files(skip_history: bool = False):
    """
    skip_history — 변경 이력과 결정 기록을 제외한다.
    이 둘은 「무엇을 지웠는가」를 적어야 하므로 지운 표현이 등장하는 것이 정상이다.
    다만 **실명 검사는 예외를 두지 않는다.** 이력에도 회사·개인명은 남기지 않는다.
    """
    history = {"CHANGELOG.md"}
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.suffix not in SCANNED_SUFFIXES:
            continue
        parts = set(p.parts)
        # 숨김 디렉터리(.review 같은 임시 추출 경로 포함)는 배포 대상이 아니다
        if EXCLUDED_DIRS & parts or any(x.startswith(".") for x in p.parts[:-1]):
            continue
        if p.name == SELF:
            continue
        if skip_history and (p.name in history or "decisions" in p.parts):
            continue
        yield p


def hits(pattern: str, flags=0, skip_history: bool = False):
    """패턴에 걸리는 (파일, 줄번호, 줄) 목록."""
    out = []
    rx = re.compile(pattern, flags)
    for p in scanned_files(skip_history):
        for i, ln in enumerate(read(p).splitlines(), 1):
            if rx.search(ln):
                out.append(f"{p.relative_to(ROOT)}:{i}  {ln.strip()[:90]}")
    return out


# ── 1. 조직·개인 고유명사 ───────────────────────────────────
# 금지어를 평문으로 적으면 **목록 자체가 노출**이 된다. 해시로만 보관한다.
# 새 항목은 sha256(소문자 정규화한 낱말)을 계산해 추가한다.
FORBIDDEN_NAME_HASHES = {
    "5958c762ceb5c65696aad6cdd48f5f5d1153505cb542f80e3e7c62846b3a37d5",
    "d663959c61b240103bd6e42e66432972827afc275eec56ebf1125431c9a7d6ba",
    "90e9ca113c231a5aafe6f9b63f732861adeb5188463764d2a0d1270e4b10123f",
    "87c8fc8354c9b717d789a8f368f13ade5844381e59782affae853aea263da909",
    "ad0d5e9ea49c64d351dab8126a7e55afc01db831017713a7b3f522cdd46a6431",
}
TOKEN_RE = re.compile(r"[가-힣A-Za-z][가-힣A-Za-z0-9]{1,}")

# 저작권 표기에는 실명이 들어가는 것이 정상이다. 그 둘만 빼고 전부 검사한다.
# 루트 문서(README·CHANGELOG 등)를 빼면 거기로 실명이 새어 들어온다.
NAME_SCAN_EXEMPT = {"LICENSE", "NOTICE"}


def _name_scanned_files():
    for p in scanned_files():
        if p.name in NAME_SCAN_EXEMPT:
            continue
        yield p, p.relative_to(ROOT)


def test_no_real_organization_or_person():
    """
    실재 조직·개인명이 예시에 들어가지 않는지.
    이름을 평문으로 나열하지 않으려고 낱말 해시로 대조한다.
    """
    found = []
    for p, rel in _name_scanned_files():
        for i, ln in enumerate(read(p).splitlines(), 1):
            for tok in TOKEN_RE.findall(ln):
                if hashlib.sha256(tok.lower().encode()).hexdigest() in FORBIDDEN_NAME_HASHES:
                    found.append(f"{rel}:{i}")
    assert not found, (
        "실재 조직·개인명이 있다. 가상 표기(A사 · B사 · 홍길동)를 쓴다.\n  "
        + "\n  ".join(sorted(set(found)))
    )


def test_no_company_form_markers_in_examples():
    """
    특정 이름을 몰라도 잡히도록 **형태**로도 검사한다.
    예시에 실재 법인 표기가 들어오면 여기서 걸린다.
    """
    # 표기 기호 자체가 아니라 **뒤에 이름이 따라오는 경우**만 잡는다.
    # 규칙을 설명하려고 기호를 인용하는 문장까지 걸리면 검사가 못 쓰게 된다.
    rx = re.compile(
        r"(?:㈜|\(주\))\s*[가-힣A-Za-z]"
        r"|주식회사\s+[가-힣A-Za-z]"
        r"|[가-힣A-Za-z]\s*(?:Co\.|Ltd\.|Inc\.)"
    )
    found = []
    for p, rel in _name_scanned_files():
        for i, ln in enumerate(read(p).splitlines(), 1):
            if rx.search(ln):
                found.append(f"{rel}:{i}  {ln.strip()[:80]}")
    assert not found, (
        "예시에 법인 표기가 있다. 가상 표기(A사 · B사)를 쓴다.\n  " + "\n  ".join(found)
    )


# ── 2. 이전 도메인 잔재 ─────────────────────────────────────
# `드리프트` 는 반도체에서도 tool drift 로 쓰므로 허용한다.
@pytest.mark.parametrize("term", [
    # 이전 도메인(실내측위) 표현
    "측위", "파티클 필터", "서베이", "실증", "인도 대상",
    "보폭", "androidTest", "포즈 타임스탬프", "게이팅", "리샘플링", "인라이어",
    # 내부 API·필드명. 실명은 아니지만 공개 저장소의 예시로는 부적절하다.
    # 예시 식별자가 필요하면 가상 시나리오 안에서 만든다(waferId · InspectionStarted).
    "venueId", "NavigationStarted", "QAB", "minSdk",
    # 이전 내부 문서·용어
    "사업 정본", "정본 프레임",
])
def test_no_previous_domain_residue(term):
    found = hits(re.escape(term), skip_history=True)
    assert not found, (
        f"이전 도메인(실내측위) 표현 '{term}' 이 남아 있다. "
        f"가상 반도체 사례로 통일한다.\n  " + "\n  ".join(found)
    )


def test_drift_is_still_allowed():
    """`드리프트` 는 두 도메인 공통이라 §9 에 남아 있어야 한다. 과잉 삭제 방지."""
    subs = read(STYLE / "references" / "substitutions.md")
    assert "드리프트" in subs, "`드리프트` 가 §9 에서 사라졌다 — 반도체에서도 쓰는 용어다"


# ── 3. 스킬 문서의 구체 날짜 ────────────────────────────────
def test_skill_docs_carry_no_concrete_dates():
    """
    스킬 문서(규약)에는 특정 날짜를 넣지 않는다. 실제 사업 일정으로 읽히고 낡는다.
    예시 문서(examples/)는 도해에 날짜가 필요하므로 대상이 아니다.
    """
    rx = re.compile(r"(?<![\d.])(?:20\d{2}-)?[01]\d-[0-3]\d(?![\d.])")
    found = []
    for p in (ROOT / "plugins").rglob("*.md"):
        in_fence = False
        for i, ln in enumerate(read(p).splitlines(), 1):
            if ln.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            # API 사용 예시는 실제 날짜가 필요하다. 산문만 검사한다.
            if not in_fence and rx.search(ln):
                found.append(f"{p.relative_to(ROOT)}:{i}  {ln.strip()[:90]}")
    assert not found, (
        "스킬 문서에 구체 날짜가 있다. 「착수 시점」·「직전 회차」처럼 상대 표현을 쓴다.\n  "
        + "\n  ".join(found)
    )


# ── 4. 치환표의 정밀 수치 ───────────────────────────────────
def test_substitutions_carry_no_precise_measurements():
    """
    소수점 백분율은 실측처럼 읽힌다. 가상 사례에는 반올림한 수치만 쓴다.
    `71%` 는 허용하고 소수점이 붙은 값은 불가하다.
    """
    subs = STYLE / "references" / "substitutions.md"
    found = [f"{i}: {ln.strip()[:90]}"
             for i, ln in enumerate(read(subs).splitlines(), 1)
             if re.search(r"\d+\.\d+\s*%", ln)]
    assert not found, (
        "치환표에 소수점 백분율이 있다. 실측으로 오인되므로 반올림한다.\n  "
        + "\n  ".join(found)
    )


# ── 5. 가상 사례 표기 ───────────────────────────────────────
def test_example_documents_declare_they_are_fictional():
    """예시 문서가 가상임을 밝히는지. 예시 수치가 실적으로 읽히면 안 된다."""
    src = read(ROOT / "examples" / "build_example.py")
    assert src.count("(가상 사례)") >= 2, \
        "paper·deck 양쪽 표지에 `(가상 사례)` 표기가 있어야 한다"
    assert "실재하는 기업·공정·수치가 아니" in src, \
        "본문에 가상임을 밝히는 문장이 있어야 한다"


@pytest.mark.parametrize("rel", [
    "examples/before_after.md",
    "examples/build_before_after.py",
])
def test_readme_example_assets_declare_they_are_fictional(rel):
    """README 전후 대비 예시도 가상임을 밝혀야 한다. 첫 화면이라 오인 비용이 크다."""
    body = read(ROOT / rel)
    assert "가상 사례" in body, f"{rel} 에 가상임을 밝히는 문장이 없다"
    assert "실재하는 기업" in body, f"{rel} 에 실재하지 않음을 밝히는 문장이 없다"


def test_readme_shows_rendered_output():
    """
    문서 제작 도구인데 결과물이 안 보이면 손해가 크다.
    스크린샷 경로가 README 에 있고 파일이 실재하는지 확인한다.
    """
    readme = read(ROOT / "README.md")
    shots = re.findall(r'src="(docs/assets/[^"]+\.png)"', readme)
    assert shots, "README 에 결과물 스크린샷이 없다"
    missing = [s for s in shots if not (ROOT / s).exists()]
    assert not missing, f"README 가 없는 이미지를 가리킨다: {missing}"


def test_style_skill_declares_its_examples_are_fictional():
    for f in ("SKILL.md", "references/substitutions.md"):
        body = read(STYLE / f)
        assert "가상 사례" in body, f"{f} 에 예시가 가상임을 밝히는 문장이 없다"

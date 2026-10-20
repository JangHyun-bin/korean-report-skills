# -*- coding: utf-8 -*-
"""
번호 · 참조 정합성 검사기(`korean-report-style/assets/structure.py`) 자체의 검사.

이 검사기는 다른 문서를 가리키는 참조를 잡는 순간 쓸모가 없어진다. 실제 편집 세션에서
걸렸던 두 형태 — 백틱 경로 뒤의 절 번호, 「열람 범위」 줄의 논문 절 번호 — 를 고정하고,
같은 규칙이 이 문서 안의 끊긴 참조까지 놓치지 않는지도 함께 고정한다.

예시는 가상 사례 「A사 — 인라인 계측 체계 확립과 수율 개선」 이다.
"""
import json
import subprocess
import sys

import pytest
import structure
from conftest import ROOT, STYLE_ASSETS

TOOL = STYLE_ASSETS / "structure.py"

BASE = """\
# A사 — 인라인 계측 체계 확립과 수율 개선

## 요약

## 1. 배경

### 1.1 현황

### 1.2 목표

## 2. 방법

### 2.1 계측

## 문헌 열람 범위와 한계
"""


def run(text):
    found, _stats = structure.check(text, "시험.md")
    return found


def rules(text):
    return [(f.rule_id, f.line) for f in run(text)]


def line_of(text, needle):
    return next(i for i, ln in enumerate(text.splitlines(), 1) if needle in ln)


def cli(*args, stdin=None):
    return subprocess.run(
        [sys.executable, str(TOOL), *args], input=stdin,
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )


# ── 배포 형태 ────────────────────────────────────────────────

def test_checker_ships_inside_the_skill():
    """저장소 scripts/ 에 두면 스킬을 설치한 사람에게 가지 않는다."""
    assert TOOL.exists(), "structure.py 가 스킬 안에 없다 — 설치본에 실리지 않는다"


def test_command_exit_codes():
    broken = cli("-", stdin=BASE + "\n계측 기준은 §3 에 있다.\n")
    assert broken.returncode == 1, broken.stdout
    assert "KRS-S-REF" in broken.stdout

    clean = cli("-", stdin=BASE + "\n계측 기준은 §2.1 에 있다.\n")
    assert clean.returncode == 0, clean.stdout
    assert "위반 없음" in clean.stdout

    assert cli("없는파일.md").returncode == 2


def test_clean_base_document_has_no_findings_and_counts_what_it_checked():
    """통과가 「아무것도 보지 않음」이 아닌지 — 검사한 항목 수를 함께 확인한다."""
    found, stats = structure.check(BASE + "\n기준은 §1.2 와 2절에 있다.\n", "시험.md")
    assert found == []
    assert stats["번호 붙은 절"] == 5
    assert stats["참조"] == 2


# ── KRS-S-HEAD 절 번호 ───────────────────────────────────────

def test_heading_gap_is_reported_once():
    text = "## 1. 배경\n\n## 2. 방법\n\n## 4. 결과\n\n## 5. 결론\n"
    assert rules(text) == [("KRS-S-HEAD", 5)]


def test_duplicate_heading_number():
    text = "## 1. 배경\n\n## 2. 방법\n\n## 2. 결과\n"
    assert rules(text) == [("KRS-S-HEAD", 5)]


@pytest.mark.parametrize("first, ok", [(0, True), (1, True), (2, False)])
def test_numbering_starts_at_zero_or_one(first, ok):
    text = f"## {first}. 개요\n\n## {first + 1}. 배경\n"
    assert (rules(text) == []) is ok


def test_unnumbered_headings_are_allowed_anywhere():
    text = "## 요약\n\n## 1. 배경\n\n## 참고\n\n## 2. 방법\n\n## 문헌 열람 범위와 한계\n"
    assert rules(text) == []


def test_subsection_gap():
    text = "## 1. 배경\n\n### 1.1 현황\n\n### 1.3 목표\n"
    assert rules(text) == [("KRS-S-HEAD", 5)]


def test_subsection_under_the_wrong_parent():
    """절을 옮기고 번호를 고치지 않은 형태다."""
    text = "## 1. 배경\n\n### 1.1 현황\n\n## 2. 방법\n\n### 1.2 계측\n"
    assert rules(text) == [("KRS-S-HEAD", 7)]


def test_subsection_numbering_restarts_under_each_parent():
    text = ("## 1. 배경\n### 1.1 현황\n### 1.2 목표\n"
            "## 2. 방법\n### 2.1 계측\n### 2.2 판정\n")
    assert rules(text) == []


def test_single_number_subsections_restart_per_parent():
    text = "## 1. 배경\n### 1. 현황\n### 2. 목표\n## 2. 방법\n### 1. 계측\n"
    assert rules(text) == []


# ── KRS-S-REF 절 참조 ───────────────────────────────────────

def test_broken_section_reference():
    text = BASE + "\n계측 기준은 §3 에 있다.\n"
    assert rules(text) == [("KRS-S-REF", line_of(text, "§3"))]


@pytest.mark.parametrize("ref, ok", [
    ("§2.1", True), ("§ 2.1", True), ("2.1절", True), ("2절에서", True),
    ("§2.2", False), ("3.1절", False), ("§1.2.1", False),
])
def test_section_reference_forms(ref, ok):
    text = BASE + f"\n기준은 {ref} 를 따른다.\n"
    assert (rules(text) == []) is ok, rules(text)


def test_section_reference_resolves_through_a_subsection():
    """`## 1.` 이 번호 없이 적혀도 `### 1.1` 이 있으면 `§1` 은 가리킬 곳이 있다."""
    text = "## 배경\n\n### 1.1 현황\n\n기준은 §1 이다.\n"
    assert rules(text) == []


def test_clause_word_with_unrelated_meaning_is_not_a_reference():
    """`절차` · `절반` · `절감` 은 절 참조가 아니다."""
    text = BASE + "\n검사 3절차 · 2절반 · 10절감은 참조가 아니다.\n"
    assert rules(text) == []


def test_file_without_numbered_headings_does_not_check_section_references():
    """번호 붙은 절이 없는 파일의 `§3` 은 다른 문서의 절이다."""
    assert rules("# 회의록\n\n고객 합의서 §3 을 확인한다.\n") == []


@pytest.mark.parametrize("line", [
    # 실제 세션에서 오탐이 났던 두 형태의 가상 대응
    "설계 근거는 `docs/specs/a-inline-metrology-design.md` §1.2 를 따른다.",
    "**열람 범위:** §3 웨이퍼 정렬, §5.2 오버레이 보정, Appendix G",
    "**Parts read:** §4 wafer alignment, §6.1 overlay correction",
    # 같은 규칙의 다른 표기
    "이 절은 design.md §7.1 을 따른다.",
    "절차는 [운영 기준](ops/inline.md) §4 에 있다.",
    "자세한 설명은 https://example.com/spec §8 에 있다.",
    "RFC 9110 §15.5 와 ISO 26262-6 §7 은 참고만 한다.",
    "선행문헌 1(US 12,345,678)의 §3 은 다른 정렬 방식을 쓴다.",
    "| `specs/b.md` | §2.2 |",
    "- `a/b.md` 의 §3",
    # 언급 · 코드 · 주석 · 예외 표식
    "본문의 「§5.1」 과 `§6.2` 는 예시다.",
    "<!-- §9 는 주석이다 -->",
    "고객 합의서 §9 를 확인한다. <!-- structure-exempt -->",
])
def test_external_references_are_not_flagged(line):
    text = BASE + "\n" + line + "\n"
    assert rules(text) == [], rules(text)


def test_path_on_the_previous_line_of_the_same_sentence():
    """문단은 줄바꿈으로 감싼다. 경로가 윗줄에 있어도 같은 문장이다."""
    text = BASE + "\n설계 근거는 계측 설계서\n`docs/specs/a-inline.md` 의\n§3.2 를 따른다.\n"
    assert rules(text) == []


def test_code_blocks_are_not_checked():
    text = BASE + "\n```text\n§11 · 제9항 · 그림 9\n```\n"
    assert rules(text) == []


def test_external_rule_is_scoped_to_the_sentence():
    """경로가 앞 문장에 있으면 이 문장의 참조는 이 문서의 것이다. 규칙이 넓어지면 여기서 걸린다."""
    text = BASE + "\n설계 근거는 `docs/a.md` 에 있다. 본 문서 §9 는 없다.\n"
    assert rules(text) == [("KRS-S-REF", line_of(text, "§9"))]


def test_citation_cue_must_precede_the_reference():
    text = BASE + "\n§9 는 없다. 열람 범위는 따로 적는다.\n"
    assert rules(text) == [("KRS-S-REF", line_of(text, "§9"))]


def test_paragraph_boundary_stops_the_sentence():
    text = BASE + "\n근거는 `docs/a.md` 에 있으며\n\n§9 는 없는 절이다.\n"
    assert rules(text) == [("KRS-S-REF", line_of(text, "§9"))]


# ── KRS-S-CLAIM 청구항 ───────────────────────────────────────

CLAIMS = """\
**[청구항 1]** 웨이퍼를 인라인 계측하는 방법.

**[청구항 2]** 제1항에 있어서, 오버레이를 보정하는 방법.

**[청구항 3]** 제1항 또는 제2항에 있어서, 수율을 판정하는 방법.
"""


def test_claims_without_gaps_pass():
    assert rules(CLAIMS) == []


def test_claim_gap():
    text = CLAIMS.replace("[청구항 3]", "[청구항 4]")
    assert rules(text) == [("KRS-S-CLAIM", 5)]


def test_claims_start_at_one():
    text = CLAIMS.replace("[청구항 1]", "[청구항 0]")
    assert ("KRS-S-CLAIM", 1) in rules(text)


@pytest.mark.parametrize("ref, ok", [
    ("제3항", True), ("청구항 3", True), ("제1항 내지 제3항", True), ("청구항 1 내지 3", True),
    ("제4항", False), ("청구항 5", False), ("제1항 내지 제16항", False), ("제0항", False),
])
def test_claim_reference_range(ref, ok):
    text = CLAIMS + f"\n본 발명은 {ref}에 따른다.\n"
    assert (rules(text) == []) is ok, rules(text)


def test_statute_paragraph_is_not_a_claim():
    """「특허법 제42조 제4항」 의 항은 청구항이 아니다."""
    assert rules(CLAIMS + "\n특허법 제42조 제4항을 따른다.\n") == []


def test_prior_art_claims_are_not_ours():
    text = CLAIMS + "\n선행문헌 1의 청구항 9 와 US 12,345,678 의 청구항 12 는 다른 구성이다.\n"
    assert rules(text) == []


def test_file_without_claims_does_not_check_claim_references():
    """청구범위를 별도 파일로 두는 명세서가 흔하다."""
    assert rules("# 상세한 설명\n\n제7항의 구성은 다음과 같다.\n") == []


def test_bracket_forms_and_english_claims():
    assert rules("【청구항 1】 방법.\n\n【청구항 2】 제1항에 있어서.\n") == []
    english = "**[Claim 1]** A method.\n\n**[Claim 2]** The method of claim 1.\n"
    assert rules(english) == []
    assert rules(english + "\nThe method of claim 3.\n") == [("KRS-S-CLAIM", 5)]


# ── KRS-S-FIG 그림 · 도 · 표 ────────────────────────────────

def test_figure_caption_gap():
    text = ('<p class="figcap">그림 1 · 계측 흐름</p>\n\n'
            '<p class="figcap">그림 3 · 수율 추이</p>\n')
    assert rules(text) == [("KRS-S-FIG", 3)]


def test_drawing_headings_and_range_reference():
    text = "## 도 1 — 계측 흐름\n\n## 도 2 — 보정 흐름\n\n도 1–2 를 본다.\n"
    assert rules(text) == []
    broken = text + "\n도 1–5 를 본다.\n"
    assert rules(broken) == [("KRS-S-FIG", 7)]


def test_references_are_not_checked_when_the_file_defines_no_captions():
    """도면을 별도 파일로 두는 경우다."""
    assert rules("# 상세한 설명\n\n도 3 과 그림 7 은 계측 흐름이다.\n") == []


def test_prose_starting_with_a_figure_number_is_not_a_caption():
    text = ('<p class="figcap">그림 1 · 계측 흐름</p>\n\n'
            "그림 1은 계측 흐름을 보인다.\n")
    assert rules(text) == []


def test_counters_are_not_figure_references():
    text = '<p class="figcap">표 1 · 수율</p>\n\n표 2개와 그림 3장을 더한다.\n'
    assert rules(text) == []


def test_figures_and_tables_are_separate_series():
    text = ('<p class="figcap">그림 1 · 계측 흐름</p>\n\n'
            '<p class="figcap">표 1 · 수율</p>\n\n표 1 과 그림 1 을 본다. 표 2 는 없다.\n')
    assert rules(text) == [("KRS-S-FIG", 5)]


def test_english_captions():
    text = "**Figure 1.** Metrology flow\n\nSee Figure 1 and Figure 2.\n"
    assert rules(text) == [("KRS-S-FIG", 3)]


# ── 출력 형식과 입력 형식 ────────────────────────────────────

def test_json_output():
    out = cli("--json", "-", stdin=BASE + "\n§3 을 본다.\n")
    payload = json.loads(out.stdout)
    assert out.returncode == 1
    assert payload["summary"]["total"] == 1
    finding = payload["findings"][0]
    assert finding["rule_id"] == "KRS-S-REF"
    assert finding["tier"] == "구조"
    assert set(finding) >= {"path", "line", "column", "found", "suggest", "section"}
    assert payload["checked"]["-"]["번호 붙은 절"] == 5


def test_github_and_sarif_output():
    gh = cli("--format", "github", "-", stdin=BASE + "\n§3 을 본다.\n")
    assert gh.stdout.startswith("::warning file=-,line=")
    assert "title=KRS-S-REF" in gh.stdout

    sarif = json.loads(cli("--format", "sarif", "-", stdin=BASE + "\n§3 을 본다.\n").stdout)
    assert sarif["$schema"].endswith("sarif-2.1.0.json")
    assert sarif["runs"][0]["results"][0]["ruleId"] == "KRS-S-REF"


def test_crlf_and_bom_input(tmp_path):
    """윈도에서 저장한 파일 — BOM 이 첫 줄의 제목을 가리면 번호 검사가 통째로 빠진다."""
    path = tmp_path / "보고서.md"
    text = "## 1. 배경\r\n\r\n## 2. 방법\r\n\r\n## 4. 결과\r\n"
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    out = cli(str(path), "--json")
    payload = json.loads(out.stdout)
    # BOM 이 남으면 첫 제목이 사라져 `## 2.` 가 첫 번호로 읽히고 한 건이 더 나온다
    assert [(f["rule_id"], f["line"]) for f in payload["findings"]] == [("KRS-S-HEAD", 5)]


def test_front_matter_is_skipped():
    text = "---\ntitle: '## 3. 제목처럼 보이는 값'\n---\n\n## 1. 배경\n"
    assert rules(text) == []

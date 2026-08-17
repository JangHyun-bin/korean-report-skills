# -*- coding: utf-8 -*-
"""
사용자에게 배포되는 문체 검사기(`korean-report-style/assets/lint.py`) 자체의 검사.

검사기는 **틀리게 잡는 쪽이 못 잡는 쪽보다 나쁘다.** 나쁜 형태를 가르치려면
그 형태를 적어야 하는데, 검사기가 그것까지 걸면 규약 문서를 쓸 수 없게 되고
사람은 검사기를 꺼 버린다. 그래서 건너뛰어야 할 자리를 하나씩 고정한다.
"""
import json
import subprocess
import sys

import lint
import pytest
from conftest import ROOT, STYLE_ASSETS

LINT = STYLE_ASSETS / "lint.py"
RULES = lint.load_rules()
HEURISTIC_RULES = lint.load_rules(include_heuristics=True)


def run(text, name="시험.md", html=False, heuristic=False):
    rules = HEURISTIC_RULES if heuristic else RULES
    return lint.lint(text, name, rules, html)


# ── 배포 형태 ────────────────────────────────────────────────

def test_linter_ships_inside_the_skill():
    """
    검사기가 저장소 `scripts/` 에 있으면 스킬을 설치한 사람에게 가지 않는다.
    스킬 폴더 안에 있어야 `.skill` 과 플러그인 설치에 함께 실린다.
    """
    assert LINT.exists(), "lint.py 가 스킬 안에 없다 — 설치본에 실리지 않는다"
    assert (STYLE_ASSETS.parent / "references" / "substitutions.md").exists()


def test_linter_finds_its_table_from_its_own_location():
    """설치 경로가 어디든 자기 옆의 치환표를 찾아야 한다."""
    assert lint.TABLE.parent.parent == STYLE_ASSETS.parent
    assert len(RULES) > 100


def test_linter_runs_as_a_command():
    """모델과 사람이 실제로 부르는 경로. import 로만 되면 소용이 없다."""
    out = subprocess.run(
        [sys.executable, str(LINT), "-"], input="검출률이 반토막이 된다.\n",
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    assert out.returncode == 1, f"위반이 있는데 종료 코드가 {out.returncode} 다"
    assert "반토막이 된다" in out.stdout
    assert "절반 수준으로 낮아진다" in out.stdout, "제안이 출력되지 않는다"


def test_clean_text_exits_zero():
    out = subprocess.run(
        [sys.executable, str(LINT), "-"], input="검출률이 절반 수준으로 낮아졌다.\n",
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    assert out.returncode == 0, out.stdout


# ── 잡아야 하는 것 ────────────────────────────────────────────

def test_catches_substitution_and_reports_position():
    found = run("가나다 반토막이 된다.")
    assert len(found) == 1
    assert (found[0].line, found[0].col) == (1, 5), "열 번호가 어긋난다"
    assert found[0].tier == "검토"
    assert found[0].suggest == "절반 수준으로 낮아진다"


def test_catches_mechanical_ending_as_fix_tier():
    found = run("측정을 완료했다.")
    assert [f.tier for f in found] == ["고침"]


def test_catches_declarative_heading():
    """서술형 제목은 제목 규칙에 걸린다."""
    assert [f.tier for f in run("## 검출 필터는 정상 동작하였다\n")] == ["제목"]


def test_heading_can_hit_both_rules():
    """치환표 §2 에 그대로 있는 제목은 제목 규칙과 치환 규칙에 함께 걸린다."""
    assert [f.tier for f in run("## 필터가 제 역할을 하였다\n")] == ["제목", "검토"]


def test_catches_interrogative_heading_that_ends_in_na():
    """
    이 검사가 만들어진 계기가 `## 무엇이 달라지나` 였는데, 종결형만 보던
    규칙은 그것을 놓쳤다. 「나」로 끝나는 명사가 있어 어미를 넓힐 수 없으므로
    의문사 시작을 본다.
    """
    assert [f.tier for f in run("## 무엇이 달라지나\n")] == ["제목"]
    assert [f.tier for f in run("## 어떻게 쓰나\n")] == ["제목"]


@pytest.mark.parametrize("title", ["개요", "추가 계측 대상", "일정 시사점", "하나의 기준"])
def test_noun_phrase_headings_pass(title):
    assert not run(f"## {title}\n"), f"명사구 제목을 걸었다: {title}"


@pytest.mark.parametrize("title", [
    "Episode 하나를 저장하는 과정",
    "외부 사이트 변경에 대응하는 방법",
    "50% overlap이 보장하는 것",
    "성능을 분해해서 측정하기",
    "새 ComfyUI 환경을 준비할 때",
    "정리나 refactor 전에 확인할 것",
])
def test_catches_clausal_and_nominalized_headings(title):
    found = run(f"## {title}\n")
    assert any(f.rule_id == "KRS-1.1-HEADING" for f in found), title


@pytest.mark.parametrize("title", ["처리 방법", "저장 과정", "운영 시", "확인 사항", "성능 측정"])
def test_concise_noun_phrase_headings_pass(title):
    assert not run(f"## {title}\n"), f"이미 명사구인 제목을 걸었다: {title}"


def test_prose_requirement_is_not_weakened_to_pass_lint():
    text = "동일한 input geometry에서는 동일한 결과가 산출되어야 한다.\n"
    assert not run(text), "본문 요구사항의 '되어야 한다'를 제목 규칙으로 걸었다"


def test_heading_requirement_still_uses_heading_scoped_rule():
    found = run("## 결과가 산출되어야 한다\n")
    assert any(f.found == "되어야 한다" for f in found)


# ── 건너뛰어야 하는 것 ─────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "```\n반토막이 된다\n```\n",
    "> 반토막이 된다\n",
    "`반토막이 된다` 는 금지된 표현이다.\n",
    "「반토막이 된다」 처럼 쓰지 않는다.\n",
    '"반토막이 된다" 로 적으면 안 된다.\n',
    "반토막이 된다  <!-- style-exempt -->\n",
])
def test_teaching_positions_are_skipped(text):
    assert not run(text), f"가르치는 자리를 걸었다: {text!r}"


@pytest.mark.parametrize("table", [
    "항목 | 상태\n--- | ---\n검출률 | 반토막이 된다\n",
    "| 항목 | 상태 |\n| --- | --- |\n| 검출률 | 반토막이 된다 |\n",
])
def test_normal_markdown_tables_are_checked(table):
    found = run(table)
    assert len(found) == 1
    assert found[0].found == "반토막이 된다"


@pytest.mark.parametrize("table", [
    "쓰지 않는다 | 쓴다\n--- | ---\n반토막이 된다 | 절반 수준으로 낮아진다\n",
    "광의 | 협의\n--- | ---\n반토막이 된다 | 절반 수준으로 낮아진다\n",
    "용어 | 흔한 오역\n--- | ---\n정상 용어 | 반토막이 된다\n",
])
def test_known_teaching_tables_are_skipped(table):
    assert not run(table)


def test_explicit_teaching_table_marker_skips_next_table():
    table = (
        "<!-- style-teaching -->\n"
        "기존 | 개선\n"
        "--- | ---\n"
        "반토막이 된다 | 절반 수준으로 낮아진다\n"
    )
    assert not run(table)


def test_inline_code_in_normal_table_is_skipped():
    table = "항목 | 상태\n--- | ---\n예시 | `반토막이 된다`\n"
    assert not run(table)


def test_fence_reopens_after_closing():
    """닫힌 코드 블록 뒤의 산문은 다시 검사 대상이다."""
    assert run("```\n반토막이 된다\n```\n반토막이 된다\n")


# ── HTML ────────────────────────────────────────────────────

def test_html_reads_body_text_and_skips_markup():
    html = ('<style>.x{content:"반토막이 된다"}</style>\n'
            "<p>검출률이 반토막이 된다.</p>\n"
            '<pre><code>x = "반토막이 된다"</code></pre>\n')
    found = run(html, "시험.html", html=True)
    assert [f.line for f in found] == [2], "태그 안이나 pre 안을 걸었다"


def test_html_does_not_check_headings():
    """typesetting을 거친 제목은 도해의 주장일 수 있다 — 마크다운 원고에서만 본다."""
    assert not run("<h2>필터는 제 역할을 하였다</h2>\n", "시험.html", html=True)


# ── 고치기 ───────────────────────────────────────────────────

def test_fix_touches_prose_and_normal_table_endings():
    src = ('본문에서 확인했다.\n'
           '```\nx = "확인했다"\n```\n'
           '> 인용에서 확인했다\n'
           '위치 | 결과\n--- | ---\n본문 표 | 확인했다\n'
           '`코드 조각에서 확인했다`\n')
    out, n = lint.fix(src, RULES)
    assert n == 2, f"산문과 일반 표 두 곳을 고쳐야 하는데 {n}곳을 고쳤다"
    assert "본문에서 확인하였다." in out
    assert "본문 표 | 확인하였다" in out
    assert out.count("확인했다") == 3, "코드·인용·백틱 안을 건드렸다"


def test_fix_leaves_teaching_table_unchanged():
    src = "<!-- style-teaching -->\n기존 | 개선\n--- | ---\n확인했다 | 확인하였다\n"
    out, n = lint.fix(src, RULES)
    assert n == 0 and out == src


def test_fix_expands_constrained_contractions():
    src = "통합돼 있다. 호출돼야 한다. 변경됐는가. 검출됐는지.\n설계돼\n"
    out, n = lint.fix(src, RULES)
    assert n == 5
    assert out == "통합되어 있다. 호출되어야 한다. 변경되었는가. 검출되었는지.\n설계되어\n"
    assert not run(out), "교정 결과인 본문 요구사항을 다시 오검출하였다"


def test_fix_does_not_expand_contractions_in_exempt_positions():
    src = (
        "```\n호출돼야 한다\n```\n"
        "> 변경됐는가\n"
        "`통합돼 있다`\n"
        "<!-- style-teaching -->\n기존 | 개선\n--- | ---\n검출됐는지 | 검출되었는지\n"
    )
    out, n = lint.fix(src, RULES)
    assert n == 0 and out == src


def test_html_fix_uses_visible_text_mask_on_mixed_line():
    src = "<p>본문에서 확인했다.</p><code>코드에서 확인했다.</code>\n"
    out, n = lint.fix(src, RULES, html=True)
    assert n == 1
    assert out == "<p>본문에서 확인하였다.</p><code>코드에서 확인했다.</code>\n"


def test_fix_leaves_judgement_rules_alone():
    """§2~§8 은 문맥을 봐야 한다. 자동으로 바꾸면 뜻이 달라진다."""
    out, n = lint.fix("검출률이 반토막이 된다.\n", RULES)
    assert n == 0 and "반토막이 된다" in out


def test_ambiguous_suggestions_are_not_auto_applied():
    """`넘긴다 → 전달한다 · 이관한다 · 위임한다` 처럼 갈래가 여럿이면 사람이 고른다."""
    assert not [r for r in RULES if r["fixable"] and " · " in r["suggest"]]


# ── 규칙 적재 ────────────────────────────────────────────────

def test_section_nine_is_not_a_rule_source():
    """§9 는 「바꾸지 않는 것」이다. 규칙으로 읽으면 정상 용어를 결함으로 부른다."""
    lefts = {r["found"] for r in RULES}
    for term in ("오버레이", "뉴슨스", "스큐", "빈닝", "드리프트", "리워크"):
        assert term not in lefts, f"§9 의 용어가 규칙으로 읽혔다: {term}"
    assert not run("오버레이 스큐가 드리프트하였다.")


def test_every_rule_carries_its_section():
    assert all(r["section"].startswith("§") for r in RULES)
    assert {r["tier"] for r in RULES} == {"고침", "검토"}


def test_every_rule_has_unique_id_scope_and_matcher():
    ids = [r["rule_id"] for r in HEURISTIC_RULES]
    assert len(ids) == len(set(ids))
    assert all(r["scopes"] <= lint.SCOPES and r["scopes"] for r in HEURISTIC_RULES)
    assert all(r["match"] in lint.MATCHERS for r in HEURISTIC_RULES)
    scoped = [r for r in RULES if r["found"] == "되어야 한다"]
    assert len(scoped) == 1 and scoped[0]["scopes"] == {"heading"}


def test_legacy_two_column_rule_table_defaults_to_all_literal(tmp_path):
    table = tmp_path / "substitutions.md"
    table.write_text(
        "## 1. 어미\n\n찾기 | 바꾸기\n--- | ---\n완료했다 | 완료하였다\n",
        encoding="utf-8",
    )
    rules = lint.load_rules(table=table)
    assert len(rules) == 1
    assert rules[0]["scopes"] == {"all"}
    assert rules[0]["match"] == "literal"
    assert rules[0]["rule_id"].startswith("KRS-1-")


def test_escaped_pipe_in_regex_table_cell_is_preserved():
    cells = lint.split_table_row(r"a | (?=있\|없) | regex")
    assert cells == ["a", "(?=있|없)", "regex"]


def test_regex_quantifier_is_not_stripped_as_markdown(tmp_path):
    table = tmp_path / "regex.md"
    table.write_text(
        "## 1. 어미\n\n찾기 | 바꾸기 | 검출 방식\n--- | --- | ---\n"
        "`a\\s*b` | c | regex\n",
        encoding="utf-8",
    )
    rules = lint.load_rules(table=table)
    assert rules[0]["found"] == r"a\s*b"
    assert [m[2] for m in lint._matches(rules[0], "ab a  b")] == ["ab", "a  b"]


# ── 한 칸에 활용형이 여럿인 행 ───────────────────────────────────

def test_multi_form_cells_become_separate_rules():
    """`올라간다 · 내려간다` 를 통째로 두면 어느 쪽도 걸리지 않는다."""
    lefts = {r["found"] for r in RULES}
    for term in ("올라간다", "내려간다", "적는다", "적었다", "나온다", "나와야", "늘어난다"):
        assert term in lefts, f"활용형이 규칙으로 갈라지지 않았다: {term}"
    assert run("검출률이 올라간다.") and run("근거를 적었다.")


@pytest.mark.parametrize("text", [
    "이 문제를 해결하기 위해 검토하였다.",
    "작업을 하기 전에 확인한다.",
    "측정을 반복하기로 결정하였다.",
])
def test_two_syllable_fragments_are_dropped(text):
    """
    `상기 · 하기 · 여히` 의 `하기` 는 나누면 「실행하기」·「하기 전에」에 전부 걸린다.
    형태소 분석 없이는 가를 수 없으므로 두 글자 조각은 버린다.
    """
    assert not run(text), f"흔한 어미를 규칙으로 잡았다: {text}"


def test_bare_verb_ending_is_not_a_rule():
    """
    치환표에 `는다` 가 홑 규칙으로 있으면 「있는다」·「만든다」가 전부 걸린다.
    실제로 §7.1 에 그런 행이 있었다 — `늘린다` 가 잘려 있었다.
    """
    assert "는다" not in {r["found"] for r in RULES}
    assert not run("규격을 확정하였다.")
    assert not run("기준을 유지하는 동안 편차가 없었다.")


# ── Software handoff heuristic ────────────────────────────────

SOFTWARE_CASES = {
    "KRS-SW-001": "graph가 살아 있다.",
    "KRS-SW-002": "prompt와 condition이 싸운다.",
    "KRS-SW-003": "depth가 prompt를 이긴다.",
    "KRS-SW-004": "identity가 무너진다.",
    "KRS-SW-005": "thumbnail이 깨진다.",
    "KRS-SW-006": "code가 이해한다.",
    "KRS-SW-007": "검증 없이 조용히 통과한다.",
}


def test_software_handoff_fixture_covers_every_heuristic():
    text = (ROOT / "tests" / "fixtures" / "style" / "software_handoff.md").read_text(
        encoding="utf-8",
    )
    ids = {f.rule_id for f in run(text, name="software_handoff.md", heuristic=True)}
    assert ids == set(SOFTWARE_CASES)


@pytest.mark.parametrize("rule_id,text", SOFTWARE_CASES.items())
def test_software_collocations_are_opt_in(rule_id, text):
    assert not run(text), "기본 검사에서 optional heuristic을 활성화하였다"
    found = run(text, heuristic=True)
    assert any(f.rule_id == rule_id and f.tier == "의심" for f in found)


@pytest.mark.parametrize("wrapper", [
    "`{}`\n",
    "> {}\n",
    "```\n{}\n```\n",
])
def test_software_heuristics_skip_exempt_positions(wrapper):
    assert not run(wrapper.format("graph가 살아 있다."), heuristic=True)


def test_software_heuristics_skip_teaching_tables():
    table = "기존 표현 | 보고서 표현\n--- | ---\ngraph가 살아 있다 | graph가 정상 동작한다\n"
    assert not run(table, heuristic=True)


# ── Machine-readable output ───────────────────────────────────

def test_finding_and_json_summary_include_rule_id():
    found = run("측정을 완료했다.\n검출률이 반토막이 된다.\n", name="sample.md")
    payload = lint.json_payload(found, fixed=0)
    assert all(item["rule_id"] for item in payload["findings"])
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["by_tier"] == {"검토": 1, "고침": 1}
    assert payload["summary"]["by_file"] == {"sample.md": 2}
    assert sum(payload["summary"]["by_rule"].values()) == 2


def test_legacy_json_cli_keeps_root_keys_and_adds_summary():
    out = subprocess.run(
        [sys.executable, str(LINT), "--json", "-"],
        input="검출률이 반토막이 된다.\n",
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    payload = json.loads(out.stdout)
    assert out.returncode == 1
    assert {"findings", "fixed", "summary"} <= payload.keys()
    assert payload["summary"]["total"] == 1


def test_github_annotation_output():
    out = subprocess.run(
        [sys.executable, str(LINT), "--format", "github", "-"],
        input="검출률이 반토막이 된다.\n",
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    assert out.returncode == 1
    assert out.stdout.startswith("::warning file=-,line=1,col=")
    assert "title=KRS-" in out.stdout


def test_sarif_output_has_required_structure():
    out = subprocess.run(
        [sys.executable, str(LINT), "--format", "sarif", "-"],
        input="검출률이 반토막이 된다.\n",
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    payload = json.loads(out.stdout)
    run_data = payload["runs"][0]
    assert out.returncode == 1
    assert payload["version"] == "2.1.0"
    assert payload["$schema"].endswith("sarif-2.1.0.json")
    assert run_data["tool"]["driver"]["rules"]
    location = run_data["results"][0]["locations"][0]["physicalLocation"]
    assert location["artifactLocation"]["uri"] == "-"
    assert location["region"]["startLine"] == 1
    assert location["region"]["startColumn"] > 0


def test_cli_heuristic_flag_enables_suspicion_tier():
    out = subprocess.run(
        [sys.executable, str(LINT), "--heuristic", "--format", "json", "-"],
        input="graph가 살아 있다.\n",
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    payload = json.loads(out.stdout)
    assert out.returncode == 1
    assert payload["findings"][0]["rule_id"] == "KRS-SW-001"
    assert payload["summary"]["by_tier"] == {"의심": 1}

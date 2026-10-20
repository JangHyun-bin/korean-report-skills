# -*- coding: utf-8 -*-
"""
국문 · 영문 대응 검사기(`korean-report-style/assets/parity.py`) 자체의 검사.

원문과 번역본을 편집할 때마다 두 파일의 수치 집합을 손으로 대조하여 누락과 오기를
실제로 찾았다. 그 절차를 기계로 옮긴 것이므로 **번역이 바꾸는 표기는 같게 읽고,
값이 바뀐 자리는 반드시 잡아야 한다.** 두 방향을 모두 고정한다.

예시는 가상 사례 「A사 — 인라인 계측 체계 확립과 수율 개선」 이다.
"""
import json
import subprocess
import sys

import parity
import pytest
from conftest import ROOT, STYLE_ASSETS

TOOL = STYLE_ASSETS / "parity.py"

KO = """\
# A사 — 인라인 계측 체계 확립과 수율 개선

## 1. 요약

웨이퍼당 계측 시간은 ~900초에서 ~590초로 단축되었다. 수율은 13.8% 향상되었다.
검사 범위는 50–145 nm 이며 2026년 10월 7일에 확정하였다. 장비는 3대다.
선행문헌 US 12,345,678 을 검토하였다. 계측 경로는 `runs/lot-12` 이다.

| 항목 | 값 |
|---|---|
| 오버레이 | 2.5 nm |

## 2. 청구항

**[청구항 1]** 웨이퍼를 인라인 계측하는 방법.

**[청구항 2]** 제1항에 있어서, 90초 이내에 판정하는 방법.
"""

EN = """\
# Company A — Inline metrology and yield improvement

## 1. Summary

Per-wafer metrology time fell from ~900 s to ~590 s. Yield improved by 13.8%.
The inspection range is 50~145 nm, fixed on October 7, 2026. Three tools are used.
Prior art US 12345678 was reviewed. The metrology path is `runs/lot-12`.

| Item | Value |
|---|---|
| Overlay | 2.5 nm |

## 2. Claims

**[Claim 1]** A method of inline wafer metrology.

**[Claim 2]** The method of claim 1, judging within 90 s.
"""


def compare(ko, en, as_set=False):
    return parity.compare(parity.Side("ko.md", ko), parity.Side("en.md", en), as_set)


def rules(ko, en, as_set=False):
    return [(f.rule_id, f.path, f.found) for f in compare(ko, en, as_set)]


def cli(*args):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )


def test_checker_ships_inside_the_skill_next_to_structure():
    """`structure.py` 의 가시 영역 규칙을 공유하므로 같은 폴더에 있어야 한다."""
    assert TOOL.exists(), "parity.py 가 스킬 안에 없다 — 설치본에 실리지 않는다"
    assert TOOL.parent == (STYLE_ASSETS / "structure.py").parent


# ── 같게 읽어야 하는 것 ──────────────────────────────────────

def test_faithful_translation_passes_and_compares_something():
    """「일치」가 「아무것도 세지 않음」이 아닌지 확인한다."""
    assert compare(KO, EN) == []
    counts = parity.Side("ko.md", KO).counts()
    assert counts["numbers"] >= 10
    assert counts["tables"] == 1
    assert counts["claims"] == 2
    assert counts["headings"] == {"h1": 1, "h2": 2}


@pytest.mark.parametrize("ko, en", [
    ("US 12,345,678", "US 12345678"),            # 천 단위 쉼표
    ("50–145 nm", "50~145 nm"),                  # 범위 기호
    ("50–145 nm", "50 to 145 nm"),
    ("2026년 10월 7일", "October 7, 2026"),       # 월 이름
    ("2026-10-07", "October 7, 2026"),           # 선행 0
    ("12월", "Dec"),
    ("−0.92", "-0.92"),                          # 음수 기호의 표기
    ("장비 3대", "three tools"),                  # 한 자리 수는 세지 않는다
    ("시료 LOT-123", "sample LOT-123"),
    ("１２개", "12 units"),                       # 전각 숫자
])
def test_notation_differences_are_equivalent(ko, en):
    assert rules(ko, en) == []


def test_fenced_code_and_html_comments_are_not_counted():
    ko = "값은 42 이다.\n\n```text\n1234 5678\n```\n\n<!-- 번역 메모 2026 -->\n"
    en = "The value is 42.\n"
    assert rules(ko, en) == []


def test_front_matter_is_not_counted():
    ko = "---\nlang: ko\nrevision: 17\n---\n\n값은 42 이다.\n"
    en = "---\nlang: en\n---\n\nThe value is 42.\n"
    assert rules(ko, en) == []


# ── 잡아야 하는 것 ───────────────────────────────────────────

def test_mistyped_decimal_is_reported_on_both_sides_with_lines():
    en = EN.replace("13.8%", "13.9%")
    found = compare(KO, en)
    assert [(f.rule_id, f.path, f.found, f.line) for f in found] == [
        ("KRS-P-NUM", "ko.md", "13.8", 5),
        ("KRS-P-NUM", "en.md", "13.9", 5),
    ]
    assert "en.md 에 없음" in found[0].suggest


def test_dropped_value():
    en = EN.replace(" within 90 s", "")
    assert rules(KO, en) == [("KRS-P-NUM", "ko.md", "90")]


@pytest.mark.parametrize("ko, en, token", [
    ("US 12,345,678", "US 12,345,679", "12345678"),
    ("50–145 nm", "50–154 nm", "145"),
    ("13.8%", "13.80%", "13.8"),                 # 자릿수도 값이다
    ("−0.92", "0.92", "-0.92"),                  # 부호가 빠진 경우
])
def test_changed_values_are_reported(ko, en, token):
    assert ("KRS-P-NUM", "ko.md", token) in rules(ko, en)


def test_inline_code_counts():
    """경로 · 식별자의 숫자도 두 벌이 같아야 한다."""
    en = EN.replace("`runs/lot-12`", "`runs/lot-13`")
    assert ("KRS-P-NUM", "ko.md", "12") in rules(KO, en)


def test_multiset_catches_a_dropped_repeat_and_set_mode_does_not():
    ko = "범위 상한은 145 이다. 재측정에서도 145 였다.\n"
    en = "The upper bound is 145. The remeasurement agreed.\n"
    found = compare(ko, en)
    assert [(f.rule_id, f.path, f.found) for f in found] == [("KRS-P-NUM", "ko.md", "145")]
    assert "2회" in found[0].suggest and "1회" in found[0].suggest
    assert compare(ko, en, as_set=True) == []


def test_heading_count_per_level():
    en = EN.replace("## 2. Claims", "Claims")
    found = compare(KO, en)
    assert [(f.rule_id, f.path, f.line) for f in found] == [("KRS-P-HEAD", "ko.md", 13)]


def test_heading_divergence_points_at_the_first_differing_number():
    ko = "## 1. 배경\n\n## 2. 방법\n\n## 3. 결과\n"
    en = "## 1. Background\n\n## 3. Results\n"
    found = [f for f in compare(ko, en) if f.rule_id == "KRS-P-HEAD"]
    assert [(f.path, f.line) for f in found] == [("ko.md", 3)]


def test_table_count():
    en = EN.replace("| Item | Value |\n|---|---|\n| Overlay | 2.5 nm |\n", "Overlay is 2.5 nm.\n")
    assert rules(KO, en) == [("KRS-P-TABLE", "ko.md", "표 ko.md 1개 · en.md 0개")]


def test_html_tables_count():
    assert rules("<table><tr><td>A</td></tr></table>\n", "Plain text.\n")[0][0] == "KRS-P-TABLE"


def test_claim_markers():
    en = EN.replace("**[Claim 2]** The method of claim 1, judging within 90 s.",
                    "Judging within 90 s.")
    assert rules(KO, en) == [("KRS-P-CLAIM", "ko.md", "청구항 2")]


# ── 명령 ─────────────────────────────────────────────────────

def test_command_pairs_and_exit_codes(tmp_path):
    ko, en, en_bad = tmp_path / "ko.md", tmp_path / "en.md", tmp_path / "en_bad.md"
    ko.write_text(KO, encoding="utf-8")
    en.write_text(EN, encoding="utf-8")
    en_bad.write_text(EN.replace("13.8%", "13.9%"), encoding="utf-8")

    ok = cli(str(ko), str(en))
    assert ok.returncode == 0, ok.stdout
    assert "일치" in ok.stdout

    bad = cli(str(ko), str(en), str(ko), str(en_bad), "--json")
    assert bad.returncode == 1
    payload = json.loads(bad.stdout)
    assert [p["findings"] for p in payload["pairs"]] == [0, 2]
    assert payload["pairs"][0]["counts"]["a"]["claims"] == 2
    assert payload["summary"]["by_rule"] == {"KRS-P-NUM": 2}

    assert cli(str(ko)).returncode == 2, "짝이 없는 인자를 받아들였다"
    assert cli(str(ko), str(tmp_path / "없음.md")).returncode == 2


def test_command_github_format(tmp_path):
    ko, en = tmp_path / "ko.md", tmp_path / "en.md"
    ko.write_text("값은 42 이다.\n", encoding="utf-8")
    en.write_text("The value is 24.\n", encoding="utf-8")
    out = cli(str(ko), str(en), "--format", "github")
    assert out.returncode == 1
    assert out.stdout.count("::warning file=") == 2
    assert "title=KRS-P-NUM" in out.stdout

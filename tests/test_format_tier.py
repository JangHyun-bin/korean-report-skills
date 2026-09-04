# -*- coding: utf-8 -*-
"""`서식` 갈래 — 마크업 결함 검사.

문체 findings 는 문장을 고치게 하고 서식 findings 는 마크업을 삭제하게 한다.
갈래를 나눈 이유가 그것이므로, 여기서는 **오탐이 없는지**를 먼저 본다.
저장소 문서가 `→` 를 500회 넘게 쓰고 `✓` `✗` 로 예시를 표시하므로
이모지 규칙이 본문 기호를 잡으면 검사기 자체가 꺼진다.

설계 근거는 `docs/design/2026-09-04-ai-slop-pattern-expansion.md` §5.1~§5.4.
"""
import lint
import pytest

RULES = lint.load_rules()


def find(text, rule_id=None):
    out = [f for f in lint.lint(text, "t.md", RULES) if f.tier == "서식"]
    return [f for f in out if f.rule_id == rule_id] if rule_id else out


# ── §10.1 이모지 ────────────────────────────────────────────────

@pytest.mark.parametrize("char", ["🚀", "✅", "📊", "💡", "⭐"])
def test_emoji_is_flagged(char):
    assert find(f"# 표본\n\n{char} 3분기에 출시한다.\n", "KRS-F-EMOJI")


@pytest.mark.parametrize("char", ["→", "←", "✓", "✗", "⚠", "❙", "·", "—"])
def test_text_symbols_pass(char):
    """본문 기호는 이모지가 아니다. 저장소 문서가 실제로 쓰는 문자들이다."""
    assert not find(f"# 표본\n\n기준은 {char} 로 표시한다.\n", "KRS-F-EMOJI")


def test_emoji_in_code_fence_passes():
    assert not find("# 표본\n\n```text\n🚀 출시\n```\n", "KRS-F-EMOJI")


# ── §10.2 굵은 라벨 목록 ────────────────────────────────────────

LABEL_ECHO = """# 표본

- **사용자 경험:** 사용자 경험을 개선하였다
- **성능:** 성능을 향상하였다
- **보안:** 보안을 강화하였다
"""

GLOSSARY = """# 표본

- **로트:** 같은 조건으로 처리한 웨이퍼 묶음
- **오버레이:** 층 사이 정렬 오차
- **뉴슨스:** 수율에 영향을 주지 않는 검출
"""

TWO_ITEMS = """# 표본

- **성능:** 성능을 향상하였다
- **보안:** 보안을 강화하였다
"""


def test_label_echo_is_flagged():
    assert find(LABEL_ECHO, "KRS-F-LABEL")


def test_glossary_passes():
    """용어 사전은 같은 형태지만 라벨이 본문을 되풀이하지 않는다."""
    assert not find(GLOSSARY, "KRS-F-LABEL")


def test_two_items_pass():
    """두 항목은 우연이다. 세 항목부터 틀로 본다."""
    assert not find(TWO_ITEMS, "KRS-F-LABEL")


# ── §10.3 제목 되풀이 ───────────────────────────────────────────

def test_heading_echo_is_flagged():
    assert find("## 성능\n\n성능은 중요하다.\n\n느린 화면에서 이탈한다.\n", "KRS-F-ECHO")


def test_heading_followed_by_content_passes():
    assert not find("## 성능\n\n느린 화면에서 사용자가 이탈한다.\n", "KRS-F-ECHO")


def test_long_first_sentence_passes():
    """제목 낱말로 시작해도 내용이 이어지면 되풀이가 아니다."""
    body = "성능은 적재 시간과 렌더 시간으로 나누어 측정하며 기준은 2초다."
    assert not find(f"## 성능\n\n{body}\n", "KRS-F-ECHO")


# ── §10 대화 잔재 (치환표) ──────────────────────────────────────

@pytest.mark.parametrize("phrase", [
    "도움이 되었기를 바랍니다",
    "더 필요하시면 말씀해 주세요",
    "좋은 질문입니다",
])
def test_chatbot_leftovers_are_flagged(phrase):
    hits = [f for f in lint.lint(f"# 표본\n\n{phrase}.\n", "t.md", RULES)
            if f.section.startswith("§10")]
    assert hits, phrase


# ── §10.4 굵게 남발 · §10.5 완충어 과잉 (밀도) ──────────────────
#
# 둘 다 임계값이 잠정값이라 `--heuristic` 에서만 본다. 기본 검사에 들어가면
# 근거 없이 숫자를 강제하게 된다. 여기서는 그 gate 자체를 먼저 검사한다.

DENSITY = lint.load_density()


def dense(text):
    return lint.lint(text, "t.md", RULES, heuristic=True)


def test_thresholds_come_from_the_reference_table():
    """임계값을 code 에 적으면 규칙이 두 곳에 생긴다."""
    assert DENSITY["limits"]["굵게 남발"] == 3
    assert DENSITY["limits"]["완충어 과잉"] == 2
    assert len(DENSITY["hedges"]) >= 10


BOLD_HEAVY = "# 표본\n\n**OKR**, **KPI**, **BMC** 를 결합한다.\n"
HEDGE_HEAVY = "# 표본\n\n이 정책이 일정 부분 영향을 미칠 가능성이 있다고 볼 여지도 있다.\n"


@pytest.mark.parametrize("text", [BOLD_HEAVY, HEDGE_HEAVY])
def test_density_rules_are_off_by_default(text):
    assert not [f for f in lint.lint(text, "t.md", RULES)
                if f.rule_id.startswith("KRS-D-")]


def test_bold_overuse_is_flagged():
    assert [f for f in dense(BOLD_HEAVY) if f.rule_id == "KRS-D-BOLD"]


def test_two_bolds_pass():
    """저장소 문단 515개 중 2개짜리가 6개다. 임계값 아래는 정상으로 둔다."""
    assert not [f for f in dense("# 표본\n\n**핵심**은 **하나**다.\n")
                if f.rule_id == "KRS-D-BOLD"]


def test_bold_in_list_items_passes():
    """목록은 항목마다 강조가 붙는 것이 정상이다."""
    text = "# 표본\n\n- **성능** 개선\n- **보안** 강화\n- **속도** 향상\n"
    assert not [f for f in dense(text) if f.rule_id == "KRS-D-BOLD"]


def test_stacked_hedges_are_flagged():
    assert [f for f in dense(HEDGE_HEAVY) if f.rule_id == "KRS-D-HEDGE"]


def test_single_hedge_passes():
    """완충어 하나는 정당하다. 근거가 실제로 약할 때 쓰는 장치다."""
    text = "# 표본\n\n이 정책은 결과에 영향을 줄 가능성이 있다.\n"
    assert not [f for f in dense(text) if f.rule_id == "KRS-D-HEDGE"]


# ── §11 군더더기 구문 ───────────────────────────────────────────

@pytest.mark.parametrize("before,after", [
    ("목표를 달성하기 위한 목적으로 배분한다.", "목표를 달성하려면 배분한다."),
    ("현재 시점에서는 확정하지 않는다.", "지금은 확정하지 않는다."),
    ("처리할 수 있는 능력을 보유한다.", "처리할 수 있다."),
])
def test_filler_is_fixed_in_place(before, after):
    """검증된 일대일 대응이므로 `--fix` 가 바로 고친다."""
    out, n = lint.fix(f"# 표본\n\n{before}\n", RULES)
    assert n and after in out, out

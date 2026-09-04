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

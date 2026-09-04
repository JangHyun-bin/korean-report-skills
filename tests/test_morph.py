# -*- coding: utf-8 -*-
"""형태소 검사가 실제로 도는지 검사한다.

이 검사가 없어서 두 결함이 조용히 살아 있었다.

1. `POLITE` 에 초성 ㅂ(U+1107) 을 적어 두었는데 분석기는 종성 ㅂ(U+11B8) 을 낸다.
   `습니다` 를 뺀 모든 합니다체가 빠져나갔고, 문체 혼용 규칙은 한 번도 걸리지 않았다.
2. `kiwipiepy` 가 CI 에 없어 형태 tier 전체가 빈 목록을 냈다. 그런데도 lint 는
   「문체 규약 위반 없음」 을 인쇄했다 — 돌리지 못한 검사와 통과한 검사가 구분되지 않았다.

그래서 여기서는 규칙의 정확도보다 **규칙이 살아 있는지** 를 먼저 본다.
"""
import morph
import pytest

pytestmark = pytest.mark.skipif(not morph.available(), reason="kiwipiepy 없음")

RULES_KEY = "expect"


@pytest.fixture(scope="module")
def rules():
    return morph.load_rules()


# ── §4 문체 혼용 ────────────────────────────────────────────────
#
# 기대 어체는 §4.1 표가 정한다. 표가 바뀌어도 검사가 흔들리지 않도록
# 파일 이름을 표에서 직접 읽어 쓴다.

PLAIN_FILE = "CHANGELOG.md"      # §4.1 이 평서체로 정한 파일
POLITE_FILE = "README.md"        # §4.1 이 합니다체로 정한 파일


def test_expectation_table_covers_both_registers(rules):
    expect = rules["expect"]
    assert expect.get(PLAIN_FILE) == "평서체"
    assert expect.get(POLITE_FILE) == "합니다체"


@pytest.mark.parametrize("sentence", [
    "결과는 초안처럼 보입니다.",      # ᆸ니다 — 자모 mismatch 로 놓치던 형태
    "스크린샷까지 만듭니다.",
    "교정기가 아닙니다.",
    "확인했습니다.",                  # 습니다 — 원래도 잡히던 형태
])
def test_polite_endings_are_detected(sentence, rules):
    lines = [(i + 1, sentence) for i in range(morph.MIN_MIXED)]
    major, minor = morph.sentence_style(lines, rules, PLAIN_FILE)
    assert major == "평서체" and minor, f"합니다체를 놓쳤다: {sentence}"


def test_plain_endings_are_detected_in_polite_file(rules):
    lines = [(i + 1, "문서를 생성한다.") for i in range(morph.MIN_MIXED)]
    major, minor = morph.sentence_style(lines, rules, POLITE_FILE)
    assert major == "합니다체" and minor, "평서체를 놓쳤다"


def test_plain_endings_pass_in_plain_file(rules):
    _major, minor = morph.sentence_style([(1, "문서를 생성한다.")], rules, PLAIN_FILE)
    assert not minor


def test_reported_form_is_a_readable_word(rules):
    lines = [(i + 1, "결과는 초안처럼 보입니다.") for i in range(3)]
    _major, minor = morph.sentence_style(lines, rules, PLAIN_FILE)
    assert minor[0][2].startswith("보입니다"), "자모 조각이 아니라 단어를 내야 한다"


def test_wrapped_line_tail_is_not_a_sentence_ending(rules):
    """줄바꿈으로 잘린 토막을 종결 어미로 읽으면 멀쩡한 문서가 혼용으로 잡힌다."""
    lines = [(1, "파일 복사 방식은 Codex에서도 사용할 수 있습니다. 복사본은 `marketplace`와"),
             (2, "같은 경로에 놓입니다.")]
    _major, minor = morph.sentence_style(lines, rules, POLITE_FILE)
    assert not minor, f"줄 끝 토막을 평서체로 세었다: {minor}"


# ── §5 형용사 활용 ──────────────────────────────────────────────

@pytest.mark.parametrize("sentence,found,suggest", [
    ("KaTeX가 필요한다.", "한다", "하다"),
    ("복사가 필요하지 않는다.", "않는다", "않다"),
    ("결과가 동일한다.", "한다", "하다"),
    ("설정이 가능한다.", "한다", "하다"),
])
def test_adjective_with_verb_ending_is_flagged(sentence, found, suggest, rules):
    hits = [(f, s) for _col, f, s, _why in morph.scan(sentence, rules)]
    assert (found, suggest) in hits, f"{sentence} → {hits}"


@pytest.mark.parametrize("sentence", [
    "KaTeX가 필요하다.",
    "압박으로 적지 않는다.",   # 적-은 기록하다의 동사다. 동형어를 잡으면 안 된다
    "복사가 필요하지 않다.",
    "자동으로 수정하지 않는다.",   # 동사 — 는다 가 맞다
    "문서를 생성한다.",
])
def test_correct_conjugation_passes(sentence, rules):
    assert not morph.scan(sentence, rules), sentence

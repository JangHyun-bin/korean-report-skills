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


# ── §1 광의 어간 — 활용형 · 조사 오분석 · 크기 서술 ─────────────────
#
# 실제 사용에서 드러난 세 결함을 고정한다.
# 1. 인용 · inline code 를 가린 뒤 홀로 남은 조사 `는` 을 분석기가 `늘-` 로 읽어 오탐하였다.
# 2. `막으면` · `끊긴다` · `낸다` 같은 광의 어간이 기본 실행에서 보고되지 않았다.
# 3. 불규칙 활용(`VV-I`)은 품사 비교에서 빠져 `긋-` 이 조용히 통과하였다.

import lint  # noqa: E402

LINT_RULES = lint.load_rules()


def stems(text, all_stems=False):
    found = lint.lint(text, "시험.md", LINT_RULES, all_stems=all_stems)
    return {f.found for f in found if f.rule_id in ("KRS-M-STEM", "KRS-M-SIZE")}


@pytest.mark.parametrize("text", [
    "인용은 원문 그대로 옮겼다. \"…\"는 생략을 표시한다.",
    "표기 없는 `Ex`는 실질적으로 공개되었음을 뜻한다.",
    "0은 \"이상치를 출력하지 않았다\"는 뜻이며 대조군은 없다.",
])
def test_particle_left_by_masking_is_not_a_stem(text):
    # `늘-` 은 주의 어간이라 `--all` 에서만 보고된다. 오탐도 그 모드에서 드러났다.
    assert "늘-" not in stems(text, all_stems=True)


@pytest.mark.parametrize("text, stem", [
    ("로트 투입 지시를 막으면 계측이 지연된다.", "막-"),
    ("장비 연결이 끊긴다.", "끊기-"),
    ("모델이 결과를 낸다.", "내-"),
    ("편차가 임계값을 넘으면 경고한다.", "넘-"),
    ("검사가 끝나면 보고한다.", "끝나-"),
    ("수율이 나오면 공유한다.", "나오-"),
    ("경계를 그어 구역을 정한다.", "긋-"),
])
def test_core_stem_is_reported_by_default(text, stem):
    assert stem in stems(text)


@pytest.mark.parametrize("text, stem", [
    ("보고서는 평서체로 쓴다.", "쓰-"),
    ("장비가 신호를 받는다.", "받-"),
    ("오버레이 표를 바꾼다.", "바꾸-"),
])
def test_caution_stem_needs_all(text, stem):
    assert stem not in stems(text)
    assert stem in stems(text, all_stems=True)


@pytest.mark.parametrize("text", [
    "재작업 비용이 크다.",
    "오차가 계측 거리에 비례하여 커진다.",
    "검사 영향이 작다.",
])
def test_size_without_comparison_is_reported(text):
    assert stems(text) & {"크-", "커지-", "작-"}


@pytest.mark.parametrize("text", [
    "편차가 임계값보다 크면 재측정한다.",
    "거리가 반경보다 작으면 보류한다.",
    "세 공정 중 오버레이 편차가 가장 크다.",
    "작은 값의 막대가 보이지 않는다.",
])
def test_size_with_comparison_or_adnominal_passes(text):
    assert not stems(text) & {"크-", "커지-", "작-"}


def test_size_stem_inside_a_loanword_is_not_reported():
    # kiwipiepy 0.24 는 「다크」 를 `다` + `크-` 로 쪼갠다. 어절 중간의 어간은 서술이 아니다.
    assert not stems("색을 박으면 다크 타일에서 바꿀 수 없다.") & {"크-"}

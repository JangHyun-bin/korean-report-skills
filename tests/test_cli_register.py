# -*- coding: utf-8 -*-
"""사용자에게 출력하는 문자열도 안내문이다.

`§4.1 파일별 기대 어체` 는 「바깥 사람에게 말을 거는 안내문은 합니다체」로 선을 그었으나
`.md` 파일만 덮었다. 설치기가 터미널에 내는 문장은 검사 밖에 있었고 평서체로 남아 있었다 —
「완료. 세션을 새로 시작하면 적용된다.」 설치기는 문서보다 먼저 사용자를 만난다.

합니다체 판정은 `니다` 로 한다. 자모를 나열하면 `됩니다` 를 놓친다. 형태소 검사가 초성
ㅂ(U+1107) 을 적어 두어 합니다체를 통째로 놓쳤던 것과 같은 함정이다.
"""
import re

import pytest
from conftest import ROOT, read

TARGETS = [ROOT / "bin" / "install.js", ROOT / "scripts" / "install.sh"]

QUOTES = (chr(39), chr(34), chr(96))
LITERALS = [re.compile(q + "([^" + q + "]*)" + q) for q in QUOTES]
INTERPOLATION = re.compile(r"\$\{[^}]*\}")
SPLIT = re.compile(r"(?<=다\.)\s+|(?<=요\.)\s+|\n")
PLAIN_END = re.compile(r"[가-힣](?:다|다\.)$")
POLITE_END = re.compile(r"(?:니다|세요|십시오)\.?$")

# 상태 표지와 명사구는 문장이 아니다
LABELS = {"설치됨", "제거됨", "실패", "완료", "사용법:", "예:"}


def sentences(path):
    """문자열 리터럴에서 한국어 종결 문장만 뽑는다."""
    text = read(path)
    for pattern in LITERALS:
        for body in pattern.findall(text):
            body = INTERPOLATION.sub("", body)
            for part in SPLIT.split(body):
                part = part.strip().strip("\\n").strip()
                if not part or part in LABELS:
                    continue
                if not re.search(r"[가-힣]", part):
                    continue
                yield part


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: p.name)
def test_user_facing_output_is_polite(path):
    """터미널 안내문은 합니다체다. §4.1 의 선을 문자열에도 적용한다."""
    bad = [s for s in sentences(path)
           if PLAIN_END.search(s) and not POLITE_END.search(s)]
    assert not bad, (
        "설치기 출력이 평서체다. 사용자에게 말을 거는 문장은 합니다체로 쓴다:\n  "
        + "\n  ".join(bad)
    )


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: p.name)
def test_the_check_actually_reads_sentences(path):
    """문장을 하나도 뽑지 못하면 통과해도 의미가 없다."""
    found = [s for s in sentences(path) if POLITE_END.search(s)]
    assert found, f"{path.name} 에서 한국어 안내 문장을 뽑지 못하였다"


def test_plain_output_would_be_caught():
    """검사가 실제로 무는지 본다. 이 문장이 통과하면 검사가 꺼진 것이다."""
    assert PLAIN_END.search("적용된다.") and not POLITE_END.search("적용된다.")
    assert POLITE_END.search("적용됩니다.")

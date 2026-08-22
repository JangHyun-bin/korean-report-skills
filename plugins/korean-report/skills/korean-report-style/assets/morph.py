# -*- coding: utf-8 -*-
"""형태소 기반 검사.

치환표는 문자열을 담는데 한국어는 교착어라 어간 하나에 활용형이 수십 개 붙는다.
`다룬다` 를 표에 적어도 `다루었다` · `다루며` 는 빠져나간다. 실측에서 같은 위반을
활용형만 바꾼 14문장 중 7문장이 통과하였다.

그래서 닫힌 부류는 형태소로 판정한다 — 어간 · 단위 명사 · 종결 어미.
열린 부류(의인화 표현 · 구어체 환언)는 여전히 판정법의 몫이며,
여기서는 후보를 좁혀 사람에게 넘긴다.

규칙은 `references/morphology.md` 에서 읽는다. 규칙을 두 곳에 적지 않는다.
"""
from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
TABLE = HERE.parent / "references" / "morphology.md"

_kiwi = None


def available() -> bool:
    try:
        import kiwipiepy  # noqa: F401
        return True
    except ImportError:
        return False


def _analyzer():
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi
        _kiwi = Kiwi()
    return _kiwi


# ── 규칙 적재 ──────────────────────────────────────────────────────

def _rows(block: str):
    """마크다운 표에서 (첫 열, 둘째 열) 을 뽑는다. 구분선과 머리는 건너뛴다."""
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("어간", "단위", "어체"):
            continue
        yield cells[0], cells[1]


def load_rules(table: pathlib.Path = TABLE) -> dict:
    text = table.read_text(encoding="utf-8")
    sec = {}
    cur = None
    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(.*)$", line)
        if m:
            cur = m.group(1).strip()
            sec[cur] = []
        elif cur:
            sec[cur].append(line)
    grab = lambda k: "\n".join(next(v for h, v in sec.items() if h.startswith(k)))

    fence = re.search(r"```(.*?)```", grab("3.1"), re.S)
    animate_fence = re.search(r"```(.*?)```", grab("2.1"), re.S)
    unit_rows = list(_unit_rows(grab("3.2")))
    return {
        "core": dict(_rows(grab("1.1"))),
        "soft": dict(_rows(grab("1.2"))),
        "animate": dict(_rows(grab("2. 동사"))),
        "animate_nouns": set(animate_fence.group(1).split()) if animate_fence else set(),
        "allow": set(fence.group(1).split()) if fence else set(),
        "unit": {c[0]: c[1] for c in unit_rows},
        "unit_alt": {c[0]: c[2] for c in unit_rows},
        "expect": dict(_rows(grab("4.1"))),
    }


def _unit_rows(block: str):
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[0] != "단위":
            yield cells


# ── 검사 ───────────────────────────────────────────────────────────

SUBJECT_JOSA = {"이", "가", "은", "는", "께서"}
NUMERIC = {"SN", "NR", "MM"}
POLITE = ("습니다", "ᄇ니다", "ㅂ니다")
MIN_MIXED = 3   # 소수 쪽이 이보다 적으면 인용으로 보고 넘어간다


def scan(line: str, rules: dict, all_stems: bool = False):
    """한 줄을 검사하여 (열, 발견, 대안, 사유) 를 낸다."""
    k = _analyzer()
    toks = k.tokenize(line)
    out = []

    for i, t in enumerate(toks):
        # ① 광의 고유어 어간
        if t.tag in ("VV", "VA"):
            for bucket, tier in (("core", True), ("soft", all_stems)):
                if tier and t.form in rules[bucket]:
                    out.append((t.start, t.form + "-", rules[bucket][t.form], "7.1 광의 어간|STEM"))
                    break

        # ② 유정물 동사 — 주어를 함께 낸다
        if t.tag == "VV" and t.form in rules["animate"]:
            subj = None
            for j in range(i - 1, max(-1, i - 6), -1):
                if toks[j].tag in ("JKS", "JX") and toks[j].form in SUBJECT_JOSA:
                    if j and toks[j - 1].tag in ("NNG", "NNP"):
                        subj = toks[j - 1].form
                    break
            if subj and subj not in rules["animate_nouns"]:
                out.append((t.start, f"{subj} + {t.form}-",
                            rules["animate"][t.form], "4 의인화 후보|ANIMATE"))

        # ③ 단위 명사 — 수 뒤에 오는 것만 본다
        if t.tag in ("NNB", "NNG") and i and toks[i - 1].tag in NUMERIC:
            if t.form in rules["unit"]:
                obj, j = None, i - 2
                while j >= 0 and toks[j].tag in ("NNG", "NNP"):
                    obj = toks[j].form + (obj or "")
                    j -= 1
                alt = rules["unit_alt"].get(t.form, "")
                found = f"{obj} {toks[i - 1].form}{t.form}" if obj \
                    else (toks[i - 1].form + t.form)
                out.append((t.start, found, alt, "3 단위 명사|UNIT"))
    return out


def sentence_style(text_lines, rules, filename: str = "") -> tuple[str, list]:
    """종결 어미로 어체를 판정한다.

    기대 어체가 정해진 파일(§4.1)은 기대와 다른 어체를 전부 낸다.
    나머지는 소수 쪽을 낸다 — 다수 쪽이 그 문서의 어체다.
    """
    k = _analyzer()
    plain, polite = [], []
    for no, line in text_lines:
        for t in k.tokenize(line):
            if t.tag != "EF":
                continue
            (polite if t.form.endswith(POLITE) else plain).append((no, t.start, t.form))
    import os
    expect = rules.get("expect", {}).get(os.path.basename(filename), "")
    if expect:
        wrong = polite if expect == "평서체" else plain
        if not wrong:
            return "", []
        no, col, form = wrong[0]
        label = f"{form} 외 {len(wrong) - 1}곳" if len(wrong) > 1 else form
        return expect, [(no, col, label)]

    if not plain or not polite:
        return "", []
    minor = polite if len(polite) <= len(plain) else plain
    # 인용 한두 곳으로 어체가 섞였다고 보고하면 소음이 된다
    if len(minor) < MIN_MIXED:
        return "", []
    major = "평서체" if minor is polite else "합니다체"
    # 파일당 한 번만 낸다. 어체 혼용은 줄 단위 결함이 아니라 문서 단위 결함이다
    no, col, form = minor[0]
    label = f"{form} 외 {len(minor) - 1}곳" if len(minor) > 1 else form
    return major, [(no, col, label)]

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
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
TABLE = HERE.parent / "references" / "morphology.md"
SUBS = HERE.parent / "references" / "substitutions.md"

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
        "final": _final_stems(),
    }


def _base(tag: str) -> str:
    """`VV-R` `VV-I` 처럼 규칙·불규칙을 나누는 하위 tag 를 본 품사로 돌린다."""
    return tag.split("-", 1)[0]


def _final_stems(table: pathlib.Path = SUBS) -> dict:
    """치환표 §7.1 의 광의 어간을 「어간 + 종결 어미」 규칙로 돌려받는다.

    §7.1 은 `잡는다` 처럼 평서체 문자열로 적혀 있어 `잡습니다` 를 못 잡는다.
    그렇다고 같은 어간을 morphology.md 에 다시 적으면 규칙이 두 곳에 생긴다.
    그래서 표는 그대로 두고, 여기서 어간만 뽑아 쓴다.

    「어간 + 종결 어미」 두 토큰으로만 분석되는 항목만 받는다.
    `시작할 수 있다` 같은 구를 받으면 `있-` 이 어간으로 잡혀 온 문장을 고치라고 하게 된다.
    """
    if not table.exists():
        return {}
    text = table.read_text(encoding="utf-8")
    block = re.search(r"^###\s+7\.1\s.*?$(.*?)^###\s", text, re.S | re.M)
    if not block:
        return {}
    k = _analyzer()
    out = {}
    for broad, narrow in _rows(block.group(1)):
        if narrow.startswith("("):          # 「(명사구로)」 같은 안내는 규칙이 아니다
            continue
        if "·" in broad:
            # 여러 형태를 나열한 행은 저자가 그 형태만 지목한 것이다.
            # 어간으로 넓히면 「예외로 둔다」 「한 곳에만 둔다」 같은 정당한 용법까지 걸린다.
            continue
        toks = [t for t in k.tokenize(broad) if t.tag != "SF"]
        if len(toks) == 2 and _base(toks[0].tag) in ("VV", "VA") and toks[1].tag == "EF":
            out[(toks[0].form, _base(toks[0].tag))] = narrow
    return out


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
# 합니다체 종결 어미는 예외 없이 `니다` 로 끝난다. 자모를 나열하지 않는다 —
# kiwi 는 `보입니다` 의 EF 를 종성 ㅂ(U+11B8) 로 내는데, 초성 ㅂ(U+1107) 을 적어 두면
# `ㅅ습니다` 이 아닌 모든 합니다체가 그대로 빠져나간다.
POLITE = ("니다",)
NOMINAL_EF = {"ᆷ", "음"}   # 개조식 명사형 종결. 표·목록에서 정상 용법이다
MIN_MIXED = 3   # 소수 쪽이 이보다 적으면 인용으로 보고 넘어간다

# 동사에만 붙는 평서형 어미 → 형용사가 쓸 수 없는 짝
#
# `하/XSA` 로 한정한다. 고유어 형용사(VA)는 동형어가 많아 분석기가 틀리면
# 멀짓한 곳을 잡는다 — `압박으로 적지 않는다` 의 `적-`(기록하다/VV)을 `적-`(적다/VA)로
# 읽으면 멀지만 맞는 문장을 고치라고 하게 된다. 실제 오류는 `필요한다` `동일한다` 처럼
# 대부분 `~하다` 파생 형용사에서 나온다.
ADJ_TAGS = ("XSA",)
STEM_TAGS = ("XSA", "VA", "VV", "XSV")
VERB_ONLY_EF = {"ᆫ다": "다", "는다": "다"}
AUX_AFTER_ADJ = {"않", "못"}   # 보조 용언은 앞 어간의 품사를 따른다


def _compose(text: str) -> str:
    """분리된 자모를 글자로 묶는다 — 분석기가 내는 `하` + `ᆫ다` 는 `한다` 로 보여야 한다.

    터미널은 조합해서 그려 주므로 눈으로는 멀줦하다. 문자열 비교는 그렇지 않다.
    """
    return unicodedata.normalize("NFC", text)


def _governing_stem(toks, i):
    """종결 어미 앞의 어간을 찾는다.

    보조 용언(`않` `못`)은 품사를 스스로 정하지 않고 본용언을 따르므로
    `필요/NNG + 하/XSA + 지/EC + 않/VX` 처럼 건너뛰어 앞을 봐야 한다.
    """
    j = i - 1
    if j >= 0 and toks[j].tag == "VX" and toks[j].form in AUX_AFTER_ADJ:
        j -= 1
        while j >= 0 and toks[j].tag in ("EC", "JX"):
            j -= 1
    return toks[j] if j >= 0 and toks[j].tag in STEM_TAGS else None


def scan(line: str, rules: dict, all_stems: bool = False):
    """한 줄을 검사하여 (열, 발견, 대안, 사유) 를 낸다."""
    k = _analyzer()
    toks = k.tokenize(line)
    out = []
    seen = set()   # ① 이 이미 보고한 어간 자리. 같은 위반을 두 번 내면 소음이 된다

    for i, t in enumerate(toks):
        # ① 광의 고유어 어간
        if t.tag in ("VV", "VA"):
            for bucket, tier in (("core", True), ("soft", all_stems)):
                if tier and t.form in rules[bucket]:
                    out.append((t.start, t.form + "-", rules[bucket][t.form], "7.1 광의 어간|STEM"))
                    seen.add(t.start)
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

        # ④ 종결형 광의 어간 — 어체와 무관하게 잡는다
        if t.tag == "EF" and i and t.form not in NOMINAL_EF:
            stem = toks[i - 1]
            alt = rules.get("final", {}).get((stem.form, _base(stem.tag)))
            if alt and stem.start not in seen:
                out.append((stem.start, stem.form + "-", alt, "6 종결형 어간|FINAL"))

        # ⑤ 형용사 어간 + 동사 평서형 어미 — `필요한다` `필요하지 않는다`
        if t.tag == "EF" and t.form in VERB_ONLY_EF:
            stem = _governing_stem(toks, i)
            if stem and stem.tag in ADJ_TAGS:
                # 어미가 붙은 자리는 바로 앞 토큰이다 — 품사만 본용언에서 가져온다
                head = toks[i - 1].form
                out.append((toks[i - 1].start, _compose(head + t.form),
                            _compose(head + VERB_ONLY_EF[t.form]),
                            "5 형용사 활용|ADJEF"))
    return out


def _word_at(line: str, at: int) -> str:
    """자모 조각 대신 사람이 읽는 단어를 낸다 — `ᆸ니다` 가 아니라 `보입니다`."""
    lo = line.rfind(" ", 0, at) + 1
    hi = line.find(" ", at)
    return line[lo:hi if hi != -1 else len(line)].strip(" .,·()`") or line[at:at + 4]


def _paragraphs(text_lines):
    """연속된 줄을 한 문단으로 이어 붙인다.

    어체는 문장의 성질이지 줄의 성질이 아니다. 줄 단위로 분석하면
    줄바꿈으로 잘린 토막을 종결 어미로 오분석한다 — 「… 복사본은 `marketplace`와」
    의 끝 `와` 를 `오- + -어` 로 읽어 평서체 한 표를 더했다.

    (문단 문자열, [(시작 offset, 줄번호, 줄 시작 offset)]) 을 낸다.
    """
    out = []
    buf, spans, prev = [], [], None
    def flush():
        if buf:
            out.append((" ".join(buf), list(spans)))
        buf.clear()
        spans.clear()
    for no, line in text_lines:
        # 제목은 명사구다(§1.1). 어체를 가지지 않으므로 집계에서 뺀다 —
        # 「기여 안내」 를 「안 + 내다」 로 읽어 평서체 한 표를 더하는 일이 생긴다.
        if line.lstrip().startswith("#"):
            flush()
            prev = None
            continue
        if prev is not None and no != prev + 1:
            flush()
        spans.append((sum(len(b) + 1 for b in buf), no))
        buf.append(line)
        prev = no
    flush()
    return out


def _locate(spans, at: int):
    """문단 안 offset 을 (줄번호, 열) 로 되돌린다."""
    no, base = spans[0][1], spans[0][0]
    for start, line_no in spans:
        if start > at:
            break
        no, base = line_no, start
    return no, at - base


def sentence_style(text_lines, rules, filename: str = "") -> tuple[str, list]:
    """종결 어미로 어체를 판정한다.

    기대 어체가 정해진 파일(§4.1)은 기대와 다른 어체를 전부 낸다.
    나머지는 소수 쪽을 낸다 — 다수 쪽이 그 문서의 어체다.
    """
    k = _analyzer()
    plain, polite = [], []
    for text, spans in _paragraphs(text_lines):
        toks = k.tokenize(text)
        for i, t in enumerate(toks):
            if t.tag != "EF":
                continue
            # `합니다체` 는 어체의 이름이지 그 어체로 쓴 문장이 아니다
            if i + 1 < len(toks) and toks[i + 1].form == "체":
                continue
            no, col = _locate(spans, t.start)
            bucket = polite if t.form.endswith(POLITE) else plain
            bucket.append((no, col, _word_at(text, t.start)))
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

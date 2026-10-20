# -*- coding: utf-8 -*-
"""
parity.py — 국문 · 영문 두 벌의 대응 검사기.

    python parity.py 보고서.ko.md 보고서.en.md
    python parity.py a.ko.md a.en.md b.ko.md b.en.md --json
    python parity.py 보고서.ko.md 보고서.en.md --set
    python parity.py 보고서.ko.md 보고서.en.md --format github

인자는 두 개씩 짝을 이룬다. 순서는 어느 쪽이 먼저여도 된다.
번역은 문장을 바꾸지만 수치와 구조는 바꾸지 않는다. 짝마다 넷을 대조한다.

    KRS-P-NUM     두 자리 이상 수치의 다중집합 — 같은 값이 몇 번 등장하는지까지 본다
    KRS-P-HEAD    수준(# · ## · …)별 제목 수
    KRS-P-TABLE   표 수 — Markdown 표와 <table>
    KRS-P-CLAIM   [청구항 N] · [Claim N] 표지의 번호 집합

수치 규칙
    · 숫자가 둘 이상인 수만 센다. 13.8 · 0.5 · 145 · 2026 은 세고 3 은 세지 않는다
    · 천 단위 쉼표를 지운다. 11,551,430 과 11551430 은 같은 수다
    · 정수부의 선행 0 을 지운다. 07 과 7 은 같은 수이므로 한 자리 수로 빠진다
    · 범위 50–145 · 50~145 는 두 수로 센다
    · 음수 부호는 앞이 글자 · 숫자 · 닫는 괄호가 아닐 때만 붙인다. FAM-123 의 123 은 양수다
    · 영문 월 이름 Oct · October · Nov · November · Dec · December 는 10 · 11 · 12 로 센다.
      「10월 7일」 과 「October 7」 이 대응한다
    · inline code 와 링크 주소는 센다 — 경로 · 식별자의 숫자도 두 벌이 같아야 한다
    · 코드 블록 · HTML 주석 · HTML 태그 · front matter 는 세지 않는다. 번역 메모는 주석에 둔다

다중집합을 기본으로 하는 이유 — 한쪽에서 반복된 값 하나가 빠지면 집합 비교는 놓친다.
번역이 같은 값을 의도적으로 한 번 더 적는 문서라면 --set 으로 값의 존재만 비교한다.

세지 않는 것 — 단위어로 적은 수(1만 · 3억 · million), 철자로 적은 수(twelve),
12시간제와 24시간제의 차이. 이런 자리는 한쪽에만 등장하는 수로 보고된다.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import unicodedata
from collections import Counter

sys.dont_write_bytecode = True       # 스킬 폴더에 __pycache__ 를 남기지 않는다
import structure as S  # noqa: E402  — 같은 폴더의 가시 영역 · 출력 규칙을 공유한다

TIER = "대응"
FORMATS = ("text", "json", "github", "sarif")
SEP = "—"

NUM = re.compile(r"(?:(?<![\w)\]])[-−](?=\d))?\d+(?:[.,]\d+)*")
THOUSANDS = re.compile(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
MONTH = re.compile(r"\b(Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b")
MONTHS = {"Oct": "10", "Nov": "11", "Dec": "12"}
TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
HTML_TABLE = re.compile(r"<table\b", re.I)


# 영문 인용 바로 뒤 괄호는 그 인용의 번역이다. 번역본에만 붙으므로 수치를 두 번 세게 된다 —
# 「"screen 306" (화면 306)」 의 306 이 한쪽에서만 2회가 된다. 한글이 든 괄호만 번역으로 보고
# 가린다 — 영문 괄호(「"Floor assignment" (2018)」)는 양쪽에 있는 data 다.
GLOSS = re.compile(r'(?P<q>"[^"]*[A-Za-z][^"]*"|“[^”]*[A-Za-z][^”]*”)(?P<g>\s*\([^()]*[가-힣][^()]*\))')


def _drop_gloss(line: str) -> str:
    """괄호 안 수치가 전부 바로 앞 인용에 있을 때만 번역으로 보고 가린다.

    「"localization instructions"(US12626419B2 제1항)」 의 괄호는 번역이 아니라 출처다.
    인용에 없는 수치가 괄호에 있으면 그 괄호는 독립된 정보이므로 센다.
    """
    def repl(m):
        quoted = Counter(tok for _c, tok in numbers(m.group("q")))
        glossed = Counter(tok for _c, tok in numbers(m.group("g")))
        if glossed - quoted:
            return m.group(0)
        return m.group("q") + " " * len(m.group("g"))
    return GLOSS.sub(repl, line)


def _normalize(part: str) -> str:
    return re.sub(r"^0+(?=\d)", "", part)


def numbers(line: str):
    """(열, 정규화한 수). 두 자리 이상만 낸다."""
    for m in MONTH.finditer(line):
        yield m.start(), MONTHS[m.group(1)[:3]]
    for m in NUM.finditer(line):
        raw = unicodedata.normalize("NFKC", m.group(0)).replace("−", "-")
        sign = "-" if raw.startswith("-") else ""
        body = raw[len(sign):]
        parts = [body.replace(",", "")] if THOUSANDS.match(body) else body.split(",")
        at = m.start() + len(sign)
        for k, part in enumerate(parts):
            token = _normalize(part)
            if sum(c.isdigit() for c in token) >= 2:
                yield (m.start() if k == 0 else at), (sign if k == 0 else "") + token
            at += len(part) + 1


class Side:
    """한 파일에서 대조할 항목을 모은다."""

    def __init__(self, name: str, text: str):
        self.name = name
        self.numbers: dict[str, list[tuple[int, int]]] = {}
        self.headings: dict[int, list[tuple[int, int, tuple[str, ...]]]] = {}
        self.tables: list[int] = []
        self.claims: dict[int, tuple[int, int, str]] = {}
        self.claim_count = 0

        rows = list(S.scan_lines(text))
        prev_pipe = False
        for no, _raw, line in rows:
            seen = S.HTML_TAG.sub(S.blank, line)       # inline code 는 가리지 않는다
            for col, token in numbers(_drop_gloss(seen)):
                self.numbers.setdefault(token, []).append((no, col + 1))

            h = S.heading(seen)
            if h:
                level, title, col = h
                digits = tuple(re.findall(r"\d+", title))
                self.headings.setdefault(level, []).append((no, col + 1, digits))

            if TABLE_SEPARATOR.match(seen) and prev_pipe:
                self.tables.append(no - 1)
            self.tables += [no] * len(HTML_TABLE.findall(line))
            prev_pipe = "|" in seen

            m = S.CLAIM_DEF.match(S.visible(line))
            if m:
                self.claim_count += 1
                self.claims.setdefault(int(m.group(2)), (no, m.start(1) + 1, m.group(1)))

    def counts(self) -> dict:
        return {
            "numbers": sum(len(v) for v in self.numbers.values()),
            "headings": {f"h{lv}": len(v) for lv, v in sorted(self.headings.items())},
            "tables": len(self.tables),
            "claims": self.claim_count,
        }


def _number_findings(a: Side, b: Side, as_set: bool) -> list[S.Finding]:
    out = []
    for token in sorted(set(a.numbers) | set(b.numbers)):
        na, nb = len(a.numbers.get(token, [])), len(b.numbers.get(token, []))
        if as_set:
            na, nb = min(na, 1), min(nb, 1)
        if na == nb:
            continue
        more, less, n_more, n_less = (a, b, na, nb) if na > nb else (b, a, nb, na)
        spots = more.numbers[token]
        line, col = spots[n_less] if n_less < len(spots) else spots[0]   # 첫 초과 출현
        where = f" ({more.name} 줄 {', '.join(str(ln) for ln, _c in spots[:6])})" if len(spots) > 1 else ""
        if n_less == 0:
            found, suggest = token, f"{less.name} 에 없음{where}"
        else:
            found, suggest = token, f"{more.name} {n_more}회 · {less.name} {n_less}회{where}"
        out.append(S.Finding(more.name, line, col, TIER, "수치 대응", found, suggest,
                             f"{a.name} ↔ {b.name}", "KRS-P-NUM"))
    return out


def _heading_findings(a: Side, b: Side) -> list[S.Finding]:
    """수준별 제목 수. 어긋난 자리는 번호 · 수치가 처음 달라지는 제목으로 짚는다."""
    out = []
    for level in sorted(set(a.headings) | set(b.headings)):
        ha, hb = a.headings.get(level, []), b.headings.get(level, [])
        if len(ha) == len(hb):
            continue
        more, less, hm, hl = (a, b, ha, hb) if len(ha) > len(hb) else (b, a, hb, ha)
        at = next((i for i, (x, y) in enumerate(zip(hm, hl, strict=False)) if x[2] != y[2]), len(hl))
        line, col, _digits = hm[at]
        mark = "#" * level
        out.append(S.Finding(more.name, line, col, TIER, "제목 수",
                             f"{mark} 제목 {more.name} {len(hm)}개 · {less.name} {len(hl)}개",
                             "대응하지 않는 제목 확인 — 이 줄부터 대조", f"{a.name} ↔ {b.name}",
                             "KRS-P-HEAD"))
    return out


def _table_findings(a: Side, b: Side) -> list[S.Finding]:
    if len(a.tables) == len(b.tables):
        return []
    more, less = (a, b) if len(a.tables) > len(b.tables) else (b, a)
    line = more.tables[len(less.tables)]
    return [S.Finding(more.name, line, 1, TIER, "표 수",
                      f"표 {more.name} {len(more.tables)}개 · {less.name} {len(less.tables)}개",
                      "대응하지 않는 표 확인", f"{a.name} ↔ {b.name}", "KRS-P-TABLE")]


def _claim_findings(a: Side, b: Side) -> list[S.Finding]:
    out = []
    for this, other in ((a, b), (b, a)):
        for n in sorted(set(this.claims) - set(other.claims)):
            line, col, label = this.claims[n]
            out.append(S.Finding(this.name, line, col, TIER, "청구항 대응", f"{label} {n}",
                                 f"{other.name} 에 없음", f"{a.name} ↔ {b.name}", "KRS-P-CLAIM"))
    if not out and a.claim_count != b.claim_count:
        more, less = (a, b) if a.claim_count > b.claim_count else (b, a)
        line, col, _label = next(iter(more.claims.values()))
        found = f"청구항 표지 {more.name} {more.claim_count}개 · {less.name} {less.claim_count}개"
        out.append(S.Finding(more.name, line, col, TIER, "청구항 대응", found,
                             "중복된 청구항 번호 확인", f"{a.name} ↔ {b.name}", "KRS-P-CLAIM"))
    return out


def compare(a: Side, b: Side, as_set: bool = False) -> list[S.Finding]:
    out = (_number_findings(a, b, as_set) + _heading_findings(a, b)
           + _table_findings(a, b) + _claim_findings(a, b))
    out.sort(key=lambda f: (f.path != a.name, f.line, f.col, f.rule_id))
    return out


def _load(name: str) -> Side | None:
    path = pathlib.Path(name)
    if not path.is_file():
        print(f"파일이 없다: {path}", file=sys.stderr)
        return None
    return Side(name, S.read_text(path))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="국문 · 영문 두 벌의 수치 · 구조 대응 검사")
    ap.add_argument("paths", nargs="+", help="짝을 이루는 두 파일. 여러 짝을 이어 적는다")
    ap.add_argument("--set", action="store_true", dest="as_set",
                    help="수치를 다중집합이 아니라 집합으로 비교한다")
    ap.add_argument("--json", action="store_true", help="--format json 의 alias")
    ap.add_argument("--format", choices=FORMATS, default="text", help="출력 형식")
    args = ap.parse_args(argv)
    if args.json and args.format not in ("text", "json"):
        ap.error("--json 과 다른 --format 을 함께 사용할 수 없다")
    if len(args.paths) % 2:
        ap.error("파일은 짝으로 적는다 — ko.md en.md [ko2.md en2.md …]")
    output_format = "json" if args.json else args.format

    pairs, found = [], []
    for i in range(0, len(args.paths), 2):
        a, b = _load(args.paths[i]), _load(args.paths[i + 1])
        if a is None or b is None:
            return 2
        got = compare(a, b, args.as_set)
        pairs.append((a, b, got))
        found += got

    if output_format == "json":
        payload = {
            "pairs": [{"a": a.name, "b": b.name, "counts": {"a": a.counts(), "b": b.counts()},
                       "findings": len(got)} for a, b, got in pairs],
            "findings": [f.as_dict() for f in found],
            "summary": S.summarize(found),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif output_format == "github":
        S.report_github(found, SEP)
    elif output_format == "sarif":
        print(json.dumps(S.sarif_payload(found, "korean-report-parity", SEP), ensure_ascii=False, indent=2))
    else:
        for a, b, got in pairs:
            c = a.counts()
            heads = sum(c["headings"].values())
            print(f"{a.name} ↔ {b.name}")
            for f in got:
                print("  " + S.format_line(f, SEP))
            if not got:
                print(f"  일치 — 수치 {c['numbers']} · 제목 {heads} · 표 {c['tables']}"
                      f" · 청구항 {c['claims']}")
        if found:
            print(f"\n{TIER} {len(found)}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())

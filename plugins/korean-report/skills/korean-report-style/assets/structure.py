# -*- coding: utf-8 -*-
"""
structure.py — 편집 후 번호와 참조의 정합성 검사기. SKILL.md §4 의 기계 판정 부분이다.

    python structure.py 보고서.md
    python structure.py 보고서.md 명세서.md --json
    python structure.py 보고서.md --format github
    python structure.py 보고서.md --format sarif

Markdown 한 파일 안에서 네 가지를 본다.

    KRS-S-HEAD   절 번호 연속 — `## 1.` … `## N.` 과 그 아래 `### N.M`
    KRS-S-REF    `§N` · `§N.M` · `N절` · `N.M절` 이 같은 파일의 절을 가리키는가
    KRS-S-CLAIM  `[청구항 N]` · `[Claim N]` 의 연속과 `제N항` · `청구항 N` · `claim N` 의 실재
    KRS-S-FIG    그림 · 도 · 표 · Figure · Table 번호의 연속과 참조의 실재

번호 규칙
    · 번호 없는 제목(`## 요약`)은 어디에 있어도 된다
    · 같은 수준 제목의 번호는 상위 제목이 바뀔 때마다 0 또는 1 부터 다시 센다
    · `### N.M` 의 N 은 바로 위 번호 제목과 같아야 한다
    · 청구항과 그림 · 표는 1 부터 연속한다. 장 번호를 붙인 `그림 2-1` 형식은 보지 않는다

참조 규칙
    · 그 종류의 정의가 파일에 하나도 없으면 참조를 보지 않는다. 번호 붙은 절이 없는 파일의 `§3`,
      캡션이 없는 파일의 `도 3` 은 별도 문서(도면 · 청구범위)를 가리키는 것으로 본다
    · `§1` 은 `## 1.` 이 없어도 `### 1.1` 이 있으면 실재한다

다른 문서를 가리키는 참조는 잡지 않는다. 규칙은 셋이다.

    1. 같은 문장 앞쪽에 백틱 경로 · 문서 파일 이름 · 링크 · URL 이 있으면 그 문서의 참조다.
       문장은 문단 안에서 위 줄로 이어 읽는다
    2. 같은 줄 앞쪽에 인용 표지(CITED)나 문서 식별자(DOC_ID)가 있으면 인용 문헌의 참조다
    3. `<!-- structure-exempt -->` 를 단 줄은 정의와 참조 모두 검사에서 뺀다

코드 블록 · inline code · HTML 주석 · front matter 는 보지 않는다. 「」 안의 참조는
언급이지 사용이 아니므로 보지 않는다. lint.py 가 인용을 다루는 방식과 같다.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

TIER = "구조"
EXEMPT = "structure-exempt"
FORMATS = ("text", "json", "github", "sarif")
SECTION_NUMBERING = "§4 번호 재정렬"
SECTION_REFERENCE = "§4 참조 갱신"


class Finding:
    """lint.py 의 Finding 과 같은 필드다. 출력 형식을 두 검사기가 공유한다."""

    __slots__ = ("path", "line", "col", "tier", "section", "found", "suggest", "text", "rule_id")

    def __init__(self, path, line, col, tier, section, found, suggest, text, rule_id):
        self.path, self.line, self.col = path, line, col
        self.tier, self.section = tier, section
        self.found, self.suggest, self.text = found, suggest, text
        self.rule_id = rule_id

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "path": self.path,
            "line": self.line,
            "column": self.col,
            "tier": self.tier,
            "section": self.section,
            "found": self.found,
            "suggest": self.suggest,
            "text": self.text,
        }


# ── Markdown 가시 영역 ─────────────────────────────────────────

FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)(?!`)(.*?[^`])\1(?!`)")
HTML_COMMENT = re.compile(r"<!--.*?-->")
HTML_TAG = re.compile(r"</?[A-Za-z][^<>]*>")       # `<그림 3>` 같은 괄호 표기는 태그가 아니다
QUOTE = re.compile(r"「[^」]*」")
ATX = re.compile(r"^\s{0,3}(#{1,6})(?:\s+(.*?))?(?:\s+#+)?\s*$")


def blank(m: re.Match) -> str:
    return " " * len(m.group(0))


def read_text(path: pathlib.Path) -> str:
    """BOM 이 붙은 파일도 첫 줄의 `---` · `#` 이 그대로 읽히게 한다."""
    return path.read_text(encoding="utf-8-sig")


def scan_lines(text: str):
    """(줄 번호, 원문, 주석을 가린 줄). front matter · 코드 블록 · HTML 주석을 뺀다.

    가린 자리는 같은 폭의 공백이므로 열 번호가 원문과 같다.
    """
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        close = next((i for i in range(1, len(lines)) if lines[i].strip() in ("---", "...")), None)
        if close is not None:
            start = close + 1

    fence = ""
    in_comment = False
    for i in range(start, len(lines)):
        raw = lines[i]
        if fence:
            m = FENCE.match(raw)
            if (m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence)
                    and not raw.strip()[len(m.group(1)):].strip()):
                fence = ""
            continue
        if not in_comment and (m := FENCE.match(raw)):
            fence = m.group(1)
            continue

        line = raw
        if in_comment:
            end = line.find("-->")
            if end == -1:
                continue
            line = " " * (end + 3) + line[end + 3:]
            in_comment = False
        line = HTML_COMMENT.sub(blank, line)
        opened = line.find("<!--")
        if opened != -1:
            line = line[:opened] + " " * (len(line) - opened)
            in_comment = True
        yield i + 1, raw, line


def visible(line: str) -> str:
    """inline code 와 HTML 태그를 같은 폭의 공백으로 가린다."""
    return HTML_TAG.sub(blank, INLINE_CODE.sub(blank, line))


def heading(line: str):
    """(수준, 제목, 제목 시작 열) 또는 None."""
    m = ATX.match(line)
    if not m:
        return None
    return len(m.group(1)), (m.group(2) or ""), (m.start(2) if m.group(2) else m.end(1))


# ── 정의와 참조의 형태 ─────────────────────────────────────────

NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)(?:\.(?!\d)|\s|$)")
TITLE_LEAD = " \t*_"

CLAIM_DEF = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*|__)?\s*[\[【]\s*(청구항|claim)\s*(\d+)\s*[\]】]", re.I,
)
CLAIM_REF_KO = re.compile(
    r"제\s?(\d+)\s?항(?!목)(?:\s*(?:내지|~|–|-|또는|및)\s*제?\s?(\d+)\s?항)?"
    r"|청구항\s?(\d+)(?:\s*(?:내지|~|–|-|또는|및)\s*(?:청구항\s?)?(\d+))?"
)
CLAIM_REF_EN = re.compile(
    r"\bclaims?\s+(\d+)(?:\s*(?:to|through|or|and|–|-|~)\s*(\d+))?", re.I,
)
STATUTE = re.compile(r"제\s?\d+\s?조(?:의\s?\d+)?\s*$")   # 「특허법 제42조 제2항」 의 항은 청구항이 아니다

CAPTION_LEAD = " \t#*_[(<〈【"
CAPTION = re.compile(
    r"^(그림|도|표|figure|fig\.|table)\s?(\d+)(?!\d)"
    r"(?=\s*(?:$|[·—:|)\]>〉】*_]|[.\-–](?!\s*\d)))",
    re.I,
)
FIG_REF_KO = re.compile(
    r"(?<![가-힣A-Za-z\d])(그림|도|표)\s?(\d+)(?!\d)(?!\s?(?:개|건|종|곳|장|가지|회))"
    r"(?:\s*(?:[–~-]|내지)\s*(?:(?:그림|도|표)\s?)?(\d+))?"
)
FIG_REF_EN = re.compile(
    r"(?<![A-Za-z])(figures?|figs?\.|tables?)\s?(\d+)(?:\s*(?:[–~-]|to|through)\s*(\d+))?", re.I,
)
SECTION_REF = re.compile(r"§\s?(\d+(?:\.\d+)*)")
CLAUSE_REF = re.compile(
    r"(?<![\d.])(\d+(?:\.\d+)*)\s?절"
    r"(?=$|[^가-힣]|의|에|과|와|은|는|을|를|로|으로|이|가|도|만|까지|부터|및)"
)


def _series(label: str) -> str:
    low = label.lower()
    if low.startswith("fig"):
        return "Figure"
    if low.startswith("table"):
        return "Table"
    if low == "claim":
        return "Claim"
    return label


# ── 외부 참조 판정 ────────────────────────────────────────────

# 인용 문헌을 소개하는 표지. 같은 줄 앞쪽에 있으면 그 뒤의 번호는 인용 문헌의 것이다
CITED = ("열람 범위", "Parts read", "선행문헌", "인용문헌", "prior art")
DOC_ID = re.compile(
    r"\b(?:RFC|ISO|IEC|IEEE|ANSI|ASTM|SEMI|JEDEC|KS|JIS|ITU-T)\s?(?:[A-Z]\s?)?\d"   # 표준
    r"|\barXiv:\s?\d{4}\.\d{4,5}"
    r"|\bdoi:\s?10\.\d{4,}/|\b10\.\d{4,}/\S"                                        # DOI
    r"|\b(?:US|KR|EP|JP|CN|WO|DE|GB)\s?\d[\d,./-]{5,}"                             # 특허 번호
)
DOC_FILE = re.compile(
    r"[\w.\-/]+\.(?:md|markdown|html?|pdf|docx?|hwpx?|pptx?|xlsx?|txt|tex|rst|adoc)\b", re.I,
)
LINK = re.compile(r"\]\([^)]*\)|https?://|<a\s[^>]*href", re.I)
SENT_END = re.compile(r"[.!?。](?=\s|$)")
BLOCK_START = re.compile(r"^\s*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\|)")
MAX_BACK = 4          # 문장을 위 줄로 이어 읽는 한도


def _looks_like_path(code: str) -> bool:
    return "/" in code or "\\" in code or bool(re.search(r"\.[A-Za-z][A-Za-z0-9]{0,4}$", code))


def _sentence_before(rows, idx: int, col: int) -> str:
    """참조 앞쪽의 같은 문장. 줄바꿈으로 감싼 문단은 위 줄까지 이어 읽는다."""
    parts = [rows[idx][1][:col]]
    j = idx
    while not SENT_END.search(parts[0]) and j > 0 and len(parts) <= MAX_BACK:
        if BLOCK_START.match(rows[j][1]):
            break
        prev_no, prev_raw, _ = rows[j - 1]
        if prev_no != rows[j][0] - 1 or not prev_raw.strip() or ATX.match(prev_raw):
            break
        j -= 1
        parts.insert(0, prev_raw)
    text = " ".join(parts)
    ends = list(SENT_END.finditer(text))
    return text[ends[-1].end():] if ends else text


def external(rows, idx: int, col: int) -> bool:
    """이 위치의 참조가 다른 문서를 가리키는가. 규칙은 모듈 설명의 1 · 2 다."""
    head = rows[idx][1][:col]
    if any(cue in head for cue in CITED) or DOC_ID.search(head):
        return True
    sentence = _sentence_before(rows, idx, col)
    if LINK.search(sentence) or DOC_FILE.search(sentence):
        return True
    return any(_looks_like_path(m.group(2)) for m in INLINE_CODE.finditer(sentence))


# ── 검사 ──────────────────────────────────────────────────────

def _fmt(nums) -> str:
    return ".".join(str(n) for n in nums)


def _heading_findings(name, heads) -> list[Finding]:
    """같은 수준의 번호는 상위 제목 아래에서 연속하고, N.M 의 N 은 상위 번호와 같다."""
    out = []
    stack: list[tuple[int, tuple | None]] = []
    last: dict[int, tuple] = {}
    for no, col, level, nums, title in heads:
        for deeper in [lv for lv in last if lv > level]:
            del last[deeper]
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = next((n for _lv, n in reversed(stack) if n), None)

        if nums:
            prev = last.get(level)
            found = suggest = None
            if len(nums) > 1 and parent and len(parent) == len(nums) - 1 and parent != nums[:-1]:
                found = f"절 {_fmt(nums)} — 상위 절 {_fmt(parent)}"
                suggest = f"번호 재정렬 — 앞자리는 {_fmt(parent)}"
            elif prev and len(prev) == len(nums) and prev[:-1] == nums[:-1]:
                if nums[-1] != prev[-1] + 1:
                    expected = (*nums[:-1], prev[-1] + 1)
                    found = f"절 {_fmt(nums)} — 앞 절 {_fmt(prev)} 다음"
                    suggest = f"번호 재정렬 — 기대값 {_fmt(expected)}"
            elif nums[-1] not in (0, 1):
                found = f"첫 절 번호 {_fmt(nums)}"
                suggest = "번호 재정렬 — 첫 번호는 0 또는 1"
            if found:
                out.append(Finding(name, no, col + 1, TIER, SECTION_NUMBERING, found, suggest,
                                   title.strip()[:80], "KRS-S-HEAD"))
            last[level] = nums
        stack.append((level, nums))
    return out


def _sequence_findings(name, defs, rule_id) -> list[Finding]:
    """series 마다 1 부터 연속하는가. defs = [(series, n, line, col, text)]."""
    out = []
    prev: dict[str, int] = {}
    for series, n, no, col, text in defs:
        before = prev.get(series)
        if before is None and n != 1:
            out.append(Finding(name, no, col + 1, TIER, SECTION_NUMBERING,
                               f"첫 {series} 번호 {n}", "번호 재정렬 — 첫 번호는 1", text, rule_id))
        elif before is not None and n != before + 1:
            out.append(Finding(name, no, col + 1, TIER, SECTION_NUMBERING,
                               f"{series} {n} — 앞 번호 {before} 다음",
                               f"번호 재정렬 — 기대값 {before + 1}", text, rule_id))
        prev[series] = n
    return out


def _overlaps(spans, start, end) -> bool:
    return any(a < end and start < b for a, b in spans)


def _listing(defined: set[int]) -> str:
    """연속이면 `1–4`, 빈 번호가 있으면 `1 · 3 · 4`."""
    nums = sorted(defined)
    if nums == list(range(nums[0], nums[-1] + 1)) and len(nums) > 2:
        return f"{nums[0]}–{nums[-1]}"
    return " · ".join(map(str, nums))


def _resolves(ref, defined) -> bool:
    """절 번호는 접두어로도 실재한다 — `§1` 은 `### 1.1` 만 있어도 가리킬 곳이 있다."""
    if isinstance(ref, tuple):
        return any(h[:len(ref)] == ref for h in defined)
    return ref in defined


def check(text: str, name: str = "-") -> tuple[list[Finding], dict]:
    """(findings, 검사한 항목 수). 검사한 것이 0 이면 통과도 의미가 없으므로 수를 함께 낸다."""
    rows = [r for r in scan_lines(text) if EXEMPT not in r[1]]
    vis = [visible(line) for _no, _raw, line in rows]

    heads, claim_defs, fig_defs = [], [], []
    def_spans: dict[int, list[tuple[int, int]]] = {}
    for idx, (no, _raw, _line) in enumerate(rows):
        line = vis[idx]
        h = heading(line)
        if h:
            level, title, col = h
            stripped = title.lstrip(TITLE_LEAD)
            m = NUMBERED.match(stripped)
            nums = tuple(int(x) for x in m.group(1).split(".")) if m else None
            heads.append((no, col + len(title) - len(stripped), level, nums, title))

        m = CLAIM_DEF.match(line)
        if m:
            claim_defs.append((_series(m.group(1)), int(m.group(2)), no, m.start(1), line.strip()[:80]))
            def_spans.setdefault(idx, []).append((m.start(1), m.end(2)))
            continue

        lead = len(line) - len(line.lstrip(CAPTION_LEAD))
        m = CAPTION.match(line[lead:])
        if m:
            fig_defs.append((_series(m.group(1)), int(m.group(2)), no, lead, line.strip()[:80]))
            def_spans.setdefault(idx, []).append((lead + m.start(1), lead + m.end(2)))

    out = _heading_findings(name, heads)
    out += _sequence_findings(name, claim_defs, "KRS-S-CLAIM")
    out += _sequence_findings(name, fig_defs, "KRS-S-FIG")

    sections = {h[3] for h in heads if h[3]}
    claims: dict[str, set[int]] = {}
    for series, n, *_ in claim_defs:
        claims.setdefault(series, set()).add(n)
    figures: dict[str, set[int]] = {}
    for series, n, *_ in fig_defs:
        figures.setdefault(series, set()).add(n)

    stats = Counter()
    for idx, (no, raw, _line) in enumerate(rows):
        line = QUOTE.sub(blank, vis[idx])
        spans = def_spans.get(idx, [])
        refs = []      # (rule_id, 시작 열, 일치 문자열, series, 번호 목록, 정의 집합 또는 None)

        for rx in (SECTION_REF, CLAUSE_REF):
            for m in rx.finditer(line):
                refs.append(("KRS-S-REF", m.start(), m.group(0), "절",
                             [tuple(int(x) for x in m.group(1).split("."))], sections or None))

        for rx, series in ((CLAIM_REF_KO, "청구항"), (CLAIM_REF_EN, "Claim")):
            for m in rx.finditer(line):
                if series == "청구항" and m.group(0).startswith("제") and STATUTE.search(line[:m.start()]):
                    continue
                nums = [int(g) for g in m.groups() if g is not None]
                refs.append(("KRS-S-CLAIM", m.start(), m.group(0), series, nums, claims.get(series)))

        for rx in (FIG_REF_KO, FIG_REF_EN):
            for m in rx.finditer(line):
                series = _series(m.group(1))
                nums = [int(g) for g in m.groups()[1:] if g is not None]
                refs.append(("KRS-S-FIG", m.start(), m.group(0), series, nums, figures.get(series)))

        for rule_id, start, matched, series, nums, defined in refs:
            if _overlaps(spans, start, start + len(matched)):
                continue
            if not defined:
                stats["정의 없는 종류의 참조"] += 1
                continue
            if external(rows, idx, start):
                stats["외부 참조"] += 1
                continue
            stats["참조"] += 1
            missing = [n for n in nums if not _resolves(n, defined)]
            if not missing:
                continue
            if rule_id == "KRS-S-REF":
                found = f"{matched.strip()} — 해당 절 없음"
                suggest = "참조 갱신 — 다른 문서의 절이면 같은 문장 앞에 경로나 링크를 둔다"
            else:
                what = "" if len(nums) == 1 else f"{series} {' · '.join(map(str, missing))} "
                found = f"{matched.strip()} — {what}정의 없음"
                suggest = f"참조 갱신 — 정의된 번호는 {series} {_listing(defined)}"
            out.append(Finding(name, no, start + 1, TIER, SECTION_REFERENCE, found, suggest,
                               raw.strip()[:80], rule_id))

    stats["번호 붙은 절"] = sum(1 for h in heads if h[3])
    stats["청구항"] = len(claim_defs)
    stats["그림·표"] = len(fig_defs)
    out.sort(key=lambda f: (f.line, f.col, f.rule_id))
    return out, dict(stats)


# ── 출력 ──────────────────────────────────────────────────────

def summarize(found: list[Finding]) -> dict:
    return {
        "total": len(found),
        "by_tier": dict(sorted(Counter(f.tier for f in found).items())),
        "by_file": dict(sorted(Counter(f.path for f in found).items())),
        "by_rule": dict(sorted(Counter(f.rule_id for f in found).items())),
    }


def format_line(f: Finding, sep: str = "→") -> str:
    return f"{f.path}:{f.line}:{f.col}  [{f.tier}] {f.found} {sep} {f.suggest}    ({f.section} · {f.rule_id})"


def _github_escape(value: str, prop: bool = False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if prop:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def report_github(found: list[Finding], sep: str = "→") -> None:
    for f in found:
        message = f"[{f.tier}] {f.found} {sep} {f.suggest}"
        print(
            f"::warning file={_github_escape(f.path, True)},line={f.line},col={f.col},"
            f"title={_github_escape(f.rule_id, True)}::{_github_escape(message)}"
        )


def sarif_payload(found: list[Finding], tool: str, sep: str = "→") -> dict:
    unique = {}
    for f in found:
        unique.setdefault(f.rule_id, f)
    rules = [
        {"id": rule_id, "shortDescription": {"text": f.section}, "help": {"text": f.suggest}}
        for rule_id, f in sorted(unique.items())
    ]
    results = [
        {
            "ruleId": f.rule_id,
            "level": "warning",
            "message": {"text": f"[{f.tier}] {f.found} {sep} {f.suggest}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.path.replace("\\", "/")},
                    "region": {"startLine": f.line, "startColumn": f.col},
                },
            }],
        }
        for f in found
    ]
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": tool, "rules": rules}}, "results": results}],
    }


def _stats_line(stats: dict) -> str:
    keys = ("번호 붙은 절", "청구항", "그림·표", "참조")
    shown = " · ".join(f"{k} {stats.get(k, 0)}" for k in keys)
    return (f"검사 — {shown} · 외부로 판정한 참조 {stats.get('외부 참조', 0)}"
            f" · 정의가 없어 보지 않은 참조 {stats.get('정의 없는 종류의 참조', 0)}")


# ── CLI ───────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="번호 · 참조 정합성 검사 (SKILL.md §4)")
    ap.add_argument("paths", nargs="+", help="검사할 Markdown 파일. - 는 표준 입력")
    ap.add_argument("--json", action="store_true", help="--format json 의 alias")
    ap.add_argument("--format", choices=FORMATS, default="text", help="출력 형식")
    args = ap.parse_args(argv)
    if args.json and args.format not in ("text", "json"):
        ap.error("--json 과 다른 --format 을 함께 사용할 수 없다")
    output_format = "json" if args.json else args.format

    found: list[Finding] = []
    checked: dict[str, dict] = {}
    for name in args.paths:
        if name == "-":
            text = sys.stdin.read()
        else:
            path = pathlib.Path(name)
            if not path.is_file():
                print(f"파일이 없다: {path}", file=sys.stderr)
                return 2
            text = read_text(path)
        got, stats = check(text, name)
        found += got
        checked[name] = stats

    if output_format == "json":
        payload = {"findings": [f.as_dict() for f in found], "checked": checked,
                   "summary": summarize(found)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif output_format == "github":
        report_github(found)
    elif output_format == "sarif":
        print(json.dumps(sarif_payload(found, "korean-report-structure"), ensure_ascii=False, indent=2))
    else:
        for f in found:
            print(format_line(f))
        for name, stats in checked.items():
            print(f"{name}  {_stats_line(stats)}")
        if found:
            print(f"\n{TIER} {len(found)}")
            print("다른 문서를 가리키는 참조는 같은 문장 앞에 경로나 링크를 두거나 "
                  "줄 끝에 <!-- structure-exempt --> 를 단다.")
        else:
            print("번호 · 참조 정합성 위반 없음")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())

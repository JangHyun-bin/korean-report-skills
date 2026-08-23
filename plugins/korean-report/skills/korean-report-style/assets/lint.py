# -*- coding: utf-8 -*-
"""
lint.py — 한국어 보고 문서의 문체 규약 검사기.

    python lint.py 보고서.md
    python lint.py dist/보고서.html --json
    python lint.py 초안.md --fix
    python lint.py 보고서.md --heuristic
    python lint.py 보고서.md --format github
    python lint.py 보고서.md --format sarif

치환 규칙은 `references/substitutions.md`, 문맥 의존 heuristic은
`references/software-handoff.md`에서 읽는다. 규칙을 코드에 중복하지 않는다.

기본 검사는 네 갈래로 보고한다.

    고침   기계적으로 교정할 수 있는 어미
    검토   문맥을 보고 선택하는 치환 규칙
    제목   서술형·의문형·관형절형 제목
    의심   --heuristic에서만 활성화되는 collocation

Markdown의 일반 표는 검사한다. 나쁜 예를 가르치는 teaching table, 코드 블록,
인용문, inline code와 `style-exempt` 줄은 제외한다. HTML은 태그를 지우고
`pre`·`code`·`script`·`style` block을 제외한 visible text를 검사한다.
"""
from __future__ import annotations

import argparse
import hashlib
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

HERE = pathlib.Path(__file__).resolve().parent
STYLE = HERE.parent
TABLE = STYLE / "references" / "substitutions.md"
HEURISTICS = STYLE / "references" / "software-handoff.md"

try:
    import morph  # 형태소 검사. kiwipiepy 가 없으면 건너뛴다
except ImportError:
    morph = None

EXEMPT = "style-exempt"
TEACHING = "style-teaching"

QUOTED = re.compile(r"`[^`]*`|「[^」]*」|\"[^\"]*\"|'[^']*'|“[^”]*”")
TAG = re.compile(r"<[^>]*>")
HTML_SKIP_BLOCK = re.compile(
    r"<(pre|code|script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S,
)

BAD_HEADING = re.compile(r"(?:다|까)$|[?!]$|(?:은|는|한|인)가$")
QUESTION_OPENER = re.compile(r"^(?:무엇|무슨|왜|어떻게|어째서|언제|누가|누구|어디|얼마|어느|어떤)")
CLAUSAL_HEADING = re.compile(
    r"(?:하는|되는|시키는|받는|주는|보장하는)\s+(?:방법|과정|이유|것)$"
    r"|(?:할|될|해야\s+할)\s+(?:때|것)$"
    r"|[가-힣]하기$"
)

RULE_LEFT_HEADERS = ("쓰지 않는다", "찾기", "광의", "검출 패턴")
RULE_SUGGEST_HEADERS = ("쓴다", "바꾸기", "협의", "제안")
TEACHING_HEADERS = {
    ("쓰지 않는다", "쓴다"),
    ("찾기", "바꾸기"),
    ("광의", "협의"),
    ("용어", "흔한 오역"),
    ("기존 표현", "보고서 표현"),
    ("어간", "대안"),
    ("단위", "원래 세는 대상"),
    ("어체", "종결 어미"),
}

FIX_SECTION = 1
MIN_LEN = 2
MIN_SPLIT_LEN = 3
SCOPES = frozenset(("all", "prose", "heading", "table", "html"))
MATCHERS = frozenset(("literal", "regex"))
TIERS = ("고침", "검토", "제목", "의심", "형태")
FORMATS = ("text", "json", "github", "sarif")


class Finding:
    __slots__ = (
        "path", "line", "col", "tier", "section", "found", "suggest", "text",
        "rule_id", "pattern",
    )

    def __init__(
        self, path, line, col, tier, section, found, suggest, text,
        rule_id="", pattern="",
    ):
        self.path, self.line, self.col = path, line, col
        self.tier, self.section = tier, section
        self.found, self.suggest, self.text = found, suggest, text
        self.rule_id, self.pattern = rule_id, pattern or found

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


# ── Markdown table parsing ─────────────────────────────────────

def split_table_row(line: str) -> list[str]:
    """Escaped pipe와 inline code의 pipe를 보존하면서 Markdown table row를 나눈다."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith(r"\|"):
        s = s[:-1]

    cells, buf = [], []
    in_code = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
        elif ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            buf.append("|")
            i += 1
        elif ch == "|" and not in_code:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def _clean_cell(cell: str) -> str:
    value = cell.strip()
    for opener in ("**", "`", "*"):
        if value.startswith(opener) and value.endswith(opener):
            value = value[len(opener):-len(opener)].strip()
            break
    return value


def _is_separator_row(line: str) -> bool:
    cells = split_table_row(line)
    return len(cells) >= 2 and all(re.fullmatch(r":?-{3,}:?", c.strip()) for c in cells)


def _is_table_header(lines: list[str], i: int) -> bool:
    return (
        i + 1 < len(lines)
        and len(split_table_row(lines[i])) >= 2
        and _is_separator_row(lines[i + 1])
    )


def _is_table_row(line: str) -> bool:
    return len(split_table_row(line)) >= 2 and "|" in line


def _is_teaching_header(cells: list[str]) -> bool:
    cleaned = tuple(_clean_cell(c) for c in cells)
    return any(cleaned[:2] == pair for pair in TEACHING_HEADERS)


# ── Rule loading ───────────────────────────────────────────────

def split_left(left: str) -> list[str]:
    if " · " not in left:
        return [left] if len(left) >= MIN_LEN else []
    return [p for p in (s.strip() for s in left.split(" · ")) if len(p) >= MIN_SPLIT_LEN]


def _generated_rule_id(section: int, pattern: str) -> str:
    digest = hashlib.sha1(pattern.encode("utf-8")).hexdigest()[:8].upper()
    return f"KRS-{section}-{digest}"


def _header_index(headers: list[str], choices: tuple[str, ...]) -> int | None:
    return next((headers.index(x) for x in choices if x in headers), None)


def _load_rule_file(path: pathlib.Path, tier_override: str | None = None) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"규칙 문서를 찾지 못하였다: {path}")

    rules, headers, section, title = [], None, 0, ""
    for ln in path.read_text(encoding="utf-8").splitlines():
        head = re.match(r"^#{2,3}\s+(\d+)(?:\.\d+)?\.?\s+(.*)$", ln.strip())
        if head:
            num = int(head.group(1))
            if not ln.strip().startswith("###") or num != section:
                section, title = num, head.group(2).strip()
            headers = None
            continue

        if not _is_table_row(ln):
            headers = None
            continue

        cells = split_table_row(ln)
        cleaned = [_clean_cell(c) for c in cells]
        if _is_separator_row(ln):
            continue

        left_i = _header_index(cleaned, RULE_LEFT_HEADERS)
        suggest_i = _header_index(cleaned, RULE_SUGGEST_HEADERS)
        if left_i is not None and suggest_i is not None:
            headers = cleaned
            continue
        if headers is None:
            continue

        left_i = _header_index(headers, RULE_LEFT_HEADERS)
        suggest_i = _header_index(headers, RULE_SUGGEST_HEADERS)
        if left_i is None or suggest_i is None or left_i >= len(cells):
            continue

        match_i = headers.index("검출 방식") if "검출 방식" in headers else None
        scope_i = headers.index("검사 범위") if "검사 범위" in headers else None
        id_i = headers.index("규칙 ID") if "규칙 ID" in headers else None

        match = _clean_cell(cells[match_i]) if match_i is not None and match_i < len(cells) else "literal"
        scope_text = _clean_cell(cells[scope_i]) if scope_i is not None and scope_i < len(cells) else "all"
        explicit_id = _clean_cell(cells[id_i]) if id_i is not None and id_i < len(cells) else ""
        if match not in MATCHERS:
            raise SystemExit(f"지원하지 않는 검출 방식 {match!r}: {path}")
        scopes = frozenset(x.strip() for x in scope_text.split(",") if x.strip()) or frozenset(("all",))
        invalid = scopes - SCOPES
        if invalid:
            raise SystemExit(f"지원하지 않는 검사 범위 {sorted(invalid)}: {path}")

        raw_left = _clean_cell(cells[left_i])
        suggest = _clean_cell(cells[suggest_i]) if suggest_i < len(cells) else ""
        if match == "literal":
            raw_left = raw_left.split("(")[0].strip()
            patterns = split_left(raw_left)
        else:
            patterns = [raw_left] if raw_left else []

        for pattern in patterns:
            try:
                if match == "regex":
                    re.compile(pattern)
            except re.error as exc:
                raise SystemExit(f"잘못된 regex {pattern!r}: {path}: {exc}") from exc

            tier = tier_override or ("고침" if section == FIX_SECTION else "검토")
            rule_id = explicit_id or _generated_rule_id(section, pattern)
            rules.append({
                "rule_id": rule_id,
                "found": pattern,
                "suggest": suggest,
                "section": f"§{section} {title}".strip(),
                "tier": tier,
                "scopes": scopes,
                "match": match,
                "fixable": (
                    tier == "고침" and bool(suggest) and " · " not in suggest
                ),
            })
    return rules


def load_rules(
    table: pathlib.Path = TABLE,
    include_heuristics: bool = False,
    heuristic_table: pathlib.Path = HEURISTICS,
) -> list[dict]:
    """Human-readable reference table을 단일 원천으로 rule 목록을 구성한다."""
    rules = _load_rule_file(table)
    if include_heuristics:
        rules += _load_rule_file(heuristic_table, tier_override="의심")

    ids = [r["rule_id"] for r in rules]
    duplicates = sorted(k for k, n in Counter(ids).items() if n > 1)
    if duplicates:
        raise SystemExit(f"중복된 rule_id: {duplicates}")
    return rules


# ── Visible text segmentation ─────────────────────────────────

def _blank(m: re.Match) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in m.group(0))


def markdown_segments(text: str):
    """(line, context, masked line) — prose·heading·일반 table만 반환한다."""
    lines = text.splitlines()
    fence = False
    in_table = False
    teaching_table = False
    pending_teaching = False
    i = 0

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if s.startswith("```"):
            fence = not fence
            i += 1
            continue
        if fence:
            i += 1
            continue
        if TEACHING in s:
            pending_teaching = True
            i += 1
            continue
        if EXEMPT in s:
            i += 1
            continue

        if in_table:
            if _is_table_row(raw):
                if not teaching_table and not _is_separator_row(raw):
                    yield i + 1, "table", QUOTED.sub(_blank, raw)
                i += 1
                continue
            in_table = False
            teaching_table = False

        if not s:
            i += 1
            continue
        if s.startswith(">"):
            pending_teaching = False
            i += 1
            continue
        if _is_table_header(lines, i):
            cells = split_table_row(raw)
            in_table = True
            teaching_table = pending_teaching or _is_teaching_header(cells)
            pending_teaching = False
            if not teaching_table:
                yield i + 1, "table", QUOTED.sub(_blank, raw)
            i += 1
            continue

        pending_teaching = False
        context = "heading" if s.startswith("#") else "prose"
        yield i + 1, context, QUOTED.sub(_blank, raw)
        i += 1


HTML_HEADING = re.compile(r"<h[1-6]", re.I)


def html_segments(text: str):
    masked = HTML_SKIP_BLOCK.sub(_blank, text)
    for i, raw in enumerate(masked.splitlines(), 1):
        if not raw.strip() or EXEMPT in raw:
            continue
        line = TAG.sub(_blank, raw)
        if line.strip():
            yield i, "html", QUOTED.sub(_blank, line)


HTML_H = re.compile(r"<(h[1-6])\b[^>]*>(.*?)</\1\s*>", re.I | re.S)


def html_headings(text: str):
    """typesetting 을 거친 제목을 요소 단위로 낸다.

    줄 단위로 훑으면 생성기가 개행 없이 이어 붙인 제목을 놓친다.
    도해는 SVG text 로 나가므로 h1~h6 은 언제나 문서 제목이다.
    """
    masked = HTML_SKIP_BLOCK.sub(_blank, text)
    for m in HTML_H.finditer(masked):
        if EXEMPT in m.group(0):
            continue
        title = TAG.sub(" ", m.group(2))
        yield masked.count("\n", 0, m.start()) + 1, title


def visible_segments(text: str, html: bool):
    return html_segments(text) if html else markdown_segments(text)


def heading_title(raw: str) -> str:
    title = re.sub(r"^#+\s*", "", raw.strip())
    title = re.sub(r"\s+", " ", title)          # 태그를 지운 자리의 공백을 접는다
    return re.sub(r"^[\d.]+\s*", "", title).strip().rstrip(".")


def _applies(rule: dict, context: str) -> bool:
    return "all" in rule["scopes"] or context in rule["scopes"]


def _matches(rule: dict, line: str):
    if rule["match"] == "literal":
        start = 0
        while (at := line.find(rule["found"], start)) != -1:
            yield at, at + len(rule["found"]), rule["found"]
            start = at + len(rule["found"])
    else:
        for match in re.finditer(rule["found"], line):
            yield match.start(), match.end(), match.group(0)


# ── Lint and fix ──────────────────────────────────────────────

def lint(text: str, name: str = "-", rules=None, html: bool = False,
         all_stems: bool = False) -> list[Finding]:
    rules = load_rules() if rules is None else rules
    out = []

    for i, context, line in visible_segments(text, html):
        for rule in rules:
            if not _applies(rule, context):
                continue
            for start, _end, matched in _matches(rule, line):
                out.append(Finding(
                    name, i, start + 1, rule["tier"], rule["section"],
                    matched, rule["suggest"], line.strip()[:80],
                    rule["rule_id"], rule["found"],
                ))

        if not html and context == "heading":
            out += _heading_finding(name, i, heading_title(line))

    if html:
        for i, raw_title in html_headings(text):
            out += _heading_finding(name, i, heading_title(raw_title))

    out += _morph_findings(text, name, html, all_stems)
    out = _dedupe(out)
    out.sort(key=lambda f: (f.line, f.col, f.rule_id))
    return out


def _heading_finding(name, line_no, title) -> list[Finding]:
    """§1.1 — 제목은 명사구다. 서술형 · 의문형 · 절 형태를 잡는다."""
    if not title or not re.search(r"[가-힣]", title):
        return []
    if not (BAD_HEADING.search(title) or QUESTION_OPENER.match(title)
            or CLAUSAL_HEADING.search(title)):
        return []
    return [Finding(
        name, line_no, 1, "제목", "§1.1 제목은 명사구", title,
        "명사구로 고친다", title[:80], "KRS-1.1-HEADING", title,
    )]


def _morph_findings(text, name, html, all_stems) -> list[Finding]:
    """형태소 검사. kiwipiepy 가 없으면 빈 목록을 낸다."""
    if morph is None or not morph.available():
        return []
    rules = morph.load_rules()
    lines = [(i, line) for i, _ctx, line in visible_segments(text, html)]
    out = []
    for i, line in lines:
        for col, matched, suggest, why in morph.scan(line, rules, all_stems):
            section, _, kind = why.partition("|")
            out.append(Finding(name, i, col + 1, "형태", "§" + section, matched,
                               suggest, line.strip()[:80], "KRS-M-" + kind, matched))
    major, minor = morph.sentence_style(lines, rules, name)
    for no, col, form in minor:
        out.append(Finding(name, no, col + 1, "형태", "§1.4 문체 혼용", form,
                           "문서 전체를 " + major + "로 통일한다",
                           "종결 어미 " + form, "KRS-M-STYLE", form))
    return out


def _dedupe(found: list[Finding]) -> list[Finding]:
    """형태소가 잡은 자리와 겹치는 문자열 검출을 버린다.

    같은 위반을 두 엔진이 각각 보고하면 소음이 되고, 소음이 되면 검사기가 꺼진다.
    겹칠 때는 형태소 쪽을 남긴다 — 활용형과 조사에 영향받지 않아 더 정확하다.
    """
    spans = {}
    for f in found:
        if f.tier == "형태":
            spans.setdefault(f.line, []).append((f.col, f.col + len(f.found)))
    if not spans:
        return found
    keep = []
    for f in found:
        if f.tier != "형태":
            lo, hi = f.col, f.col + len(f.found)
            if any(lo < b and a < hi for a, b in spans.get(f.line, ())):
                continue
        keep.append(f)
    return keep


def _replace_rule(raw: str, guard: str, rule: dict) -> tuple[str, str, int]:
    hits = 0
    start = 0
    while True:
        match = next(iter(_matches(rule, guard[start:])), None)
        if match is None:
            break
        rel_start, rel_end, _matched = match
        at, end = start + rel_start, start + rel_end
        raw = raw[:at] + rule["suggest"] + raw[end:]
        guard = guard[:at] + " " * len(rule["suggest"]) + guard[end:]
        hits += 1
        start = at + len(rule["suggest"])
    return raw, guard, hits


def fix(text: str, rules, html: bool = False) -> tuple[str, int]:
    """고침 tier만 visible context에서 교정한다."""
    contexts = {
        line: (context, guard)
        for line, context, guard in visible_segments(text, html)
    }
    lines = text.splitlines(keepends=True)
    hits = 0

    for n, raw in enumerate(lines):
        segment = contexts.get(n + 1)
        if segment is None:
            continue
        context, guard = segment
        for rule in rules:
            if not rule["fixable"] or not _applies(rule, context):
                continue
            raw, guard, count = _replace_rule(raw, guard, rule)
            hits += count
        lines[n] = raw
    return "".join(lines), hits


# ── Output ────────────────────────────────────────────────────

def summarize(found: list[Finding]) -> dict:
    return {
        "total": len(found),
        "by_tier": dict(sorted(Counter(f.tier for f in found).items())),
        "by_file": dict(sorted(Counter(f.path for f in found).items())),
        "by_rule": dict(sorted(Counter(f.rule_id for f in found).items())),
    }


def report(found: list[Finding]) -> None:
    if not found:
        print("문체 규약 위반 없음")
        return
    width = max(len(f.tier) for f in found)
    for f in found:
        arrow = f" → {f.suggest}" if f.suggest else ""
        print(
            f"{f.path}:{f.line}:{f.col}  [{f.tier:{width}}] "
            f"{f.found}{arrow}    ({f.section} · {f.rule_id})"
        )
    tally = summarize(found)["by_tier"]
    print("\n" + " · ".join(f"{tier} {tally[tier]}" for tier in TIERS if tier in tally))
    print("인용이 꼭 필요하면 백틱·「」로 감싸거나 줄 끝에 <!-- style-exempt --> 를 단다.")


def json_payload(found: list[Finding], fixed: int) -> dict:
    return {
        "findings": [f.as_dict() for f in found],
        "fixed": fixed,
        "summary": summarize(found),
    }


def _github_escape(value: str, prop: bool = False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if prop:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def report_github(found: list[Finding]) -> None:
    for f in found:
        command = "notice" if f.tier == "의심" else "warning"
        message = f"[{f.tier}] {f.found}"
        if f.suggest:
            message += f" → {f.suggest}"
        print(
            f"::{command} file={_github_escape(f.path, True)},line={f.line},col={f.col},"
            f"title={_github_escape(f.rule_id, True)}::{_github_escape(message)}"
        )


def sarif_payload(found: list[Finding]) -> dict:
    unique = {}
    for f in found:
        unique.setdefault(f.rule_id, f)
    rules = [
        {
            "id": rule_id,
            "shortDescription": {"text": f.section},
            "help": {"text": f.suggest or f.found},
        }
        for rule_id, f in sorted(unique.items())
    ]
    results = []
    for f in found:
        message = f"[{f.tier}] {f.found}"
        if f.suggest:
            message += f" → {f.suggest}"
        results.append({
            "ruleId": f.rule_id,
            "level": "note" if f.tier == "의심" else "warning",
            "message": {"text": message},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.path.replace("\\", "/")},
                    "region": {"startLine": f.line, "startColumn": f.col},
                },
            }],
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "korean-report-style", "rules": rules}},
            "results": results,
        }],
    }


# ── CLI ───────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="한국어 보고 문서 문체 규약 검사")
    ap.add_argument("paths", nargs="+", help="검사할 파일. - 는 표준 입력")
    ap.add_argument("--json", action="store_true", help="--format json의 하위 호환 alias")
    ap.add_argument("--format", choices=FORMATS, default="text", help="출력 형식")
    ap.add_argument("--heuristic", action="store_true", help="software collocation 의심 규칙 포함")
    ap.add_argument("--tier", choices=TIERS, action="append", help="이 갈래만 검사")
    ap.add_argument("--all", action="store_true", dest="all_stems",
                    help="형태소 검사에서 주의 어간까지 본다. 정당한 용법이 많아 기본은 제외한다")
    ap.add_argument("--fix", action="store_true", help="고침 tier를 파일에 직접 적용")
    args = ap.parse_args(argv)

    if args.json and args.format not in ("text", "json"):
        ap.error("--json과 다른 --format을 함께 사용할 수 없다")
    output_format = "json" if args.json else args.format
    include_heuristics = args.heuristic or bool(args.tier and "의심" in args.tier)
    rules = load_rules(include_heuristics=include_heuristics)
    found: list[Finding] = []
    fixed = 0
    fixed_paths = []

    for name in args.paths:
        if name == "-":
            text, path, html = sys.stdin.read(), "-", False
        else:
            path = pathlib.Path(name)
            if not path.exists():
                print(f"파일이 없다: {path}", file=sys.stderr)
                return 2
            text = path.read_text(encoding="utf-8")
            html = path.suffix.lower() in (".html", ".htm")

        if args.fix and name != "-":
            text, count = fix(text, rules, html)
            if count:
                path.write_text(text, encoding="utf-8")
                fixed += count
                fixed_paths.append((str(path), count))

        found += lint(text, str(path), rules, html, args.all_stems)

    if args.tier:
        found = [f for f in found if f.tier in args.tier]

    if output_format == "json":
        print(json.dumps(json_payload(found, fixed), ensure_ascii=False, indent=2))
    elif output_format == "github":
        report_github(found)
    elif output_format == "sarif":
        print(json.dumps(sarif_payload(found), ensure_ascii=False, indent=2))
    else:
        for path, count in fixed_paths:
            print(f"{path} — 어미 {count}곳을 고쳤다")
        report(found)

    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())

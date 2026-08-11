# -*- coding: utf-8 -*-
"""
lint.py — 한국어 보고 문서의 문체 규약 검사기.

    python lint.py 보고서.md
    python lint.py dist/보고서.html --json
    python lint.py 초안.md --fix            어미만 기계적으로 고친다
    cat 문단.txt | python lint.py -

**규칙 목록을 따로 두지 않는다.** `references/substitutions.md` 의 「쓰지 않는다」
열을 읽어 그대로 규칙으로 쓴다. 표를 고치면 검사도 함께 바뀐다. 규칙을 두 곳에
적으면 반드시 어긋나기 때문이다.

## 세 갈래로 나누어 보고한다

치환표 §1 은 「기계적 전역 치환이 가능하다」고 스스로 규정한다. 나머지 절은
문맥을 봐야 한다 — `넘긴다` 를 무조건 결함으로 부르면 검사기가 소음이 되고,
소음이 되면 꺼진다.

    고침   §1 어미. 판정에 문맥이 필요 없다. --fix 로 자동 치환된다
    검토   §2~§8. 사람이 문맥을 보고 정한다
    제목   서술형·의문형 절 제목 (SKILL.md §1.1)

§9 「바꾸지 않는 것」은 규칙이 아니라 오역 경고이므로 읽지 않는다.

## 걸리면 안 되는 자리

나쁜 형태를 **가르치려면** 그 형태를 적어야 한다. 그래서 건너뛴다.

    · 코드 블록(```)과 인용문(>) 과 표 행(|)
    · 백틱 · 「」 · 따옴표 안
    · 줄 끝에 <!-- style-exempt --> 가 달린 줄

HTML 은 태그를 지우고 본문만 본다. `<pre>` · `<code>` · `<script>` · `<style>`
안쪽은 통째로 건너뛴다.

종료 코드 — 걸린 것이 없으면 0, 있으면 1. `--tier` 로 좁힐 수 있다.
"""
import argparse
import json
import pathlib
import re
import sys

# stdin 도 함께 돌린다. 윈도 기본 stdin 은 cp949 라, `cat 원고.md | lint.py -` 가
# utf-8 입력을 깨뜨려 규칙에 하나도 걸리지 않고 「위반 없음」으로 통과한다.
# 못 잡는 것보다 틀리게 통과시키는 쪽이 나쁘다.
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:                       # 파이프로 묶인 객체
        pass

HERE = pathlib.Path(__file__).resolve().parent
TABLE = HERE.parent / "references" / "substitutions.md"

EXEMPT = "style-exempt"

# 인용·예시 자리. 길이를 보존해야 열 번호가 어긋나지 않는다.
QUOTED = re.compile(r"`[^`]*`|「[^」]*」|\"[^\"]*\"|'[^']*'|“[^”]*”")

# 서술형·의문형 종결. 「개요」·「추가」 같은 명사가 걸리지 않도록 종결형만 좁게 잡는다.
BAD_HEADING = re.compile(r"(?:다|까)$|[?!]$|(?:은|는|한|인)가$")

# 종결형만으로는 「무엇이 달라지나」가 새어 나간다 — 「나」로 끝나는 명사가 있어
# 어미를 넓힐 수 없다. 대신 시작어를 본다. 의문사로 시작하는 명사구는 없다.
QUESTION_OPENER = re.compile(r"^(?:무엇|무슨|왜|어떻게|어째서|언제|누가|누구|어디|얼마|어느|어떤)")

# 표 머리를 보고 규칙 표인지 가른다. §9 는 「용어 | 흔한 오역」이라 여기 걸리지 않는다.
RULE_HEADER = ("쓰지 않는다", "찾기", "| 광의 ")

FIX_SECTION = 1                                  # 기계적 치환이 허용된 절

TIERS = ("고침", "검토", "제목")


class Finding:
    __slots__ = ("path", "line", "col", "tier", "section", "found", "suggest", "text")

    def __init__(self, path, line, col, tier, section, found, suggest, text):
        self.path, self.line, self.col = path, line, col
        self.tier, self.section = tier, section
        self.found, self.suggest, self.text = found, suggest, text

    def as_dict(self) -> dict:
        return {
            "path": self.path, "line": self.line, "column": self.col,
            "tier": self.tier, "section": self.section,
            "found": self.found, "suggest": self.suggest, "text": self.text,
        }


# ── 규칙 읽기 ────────────────────────────────────────────────

def load_rules(table: pathlib.Path = TABLE) -> list[dict]:
    """치환표에서 규칙을 읽는다. 반환 순서는 파일 순서를 따른다."""
    if not table.exists():
        raise SystemExit(f"치환표를 찾지 못하였다: {table}")

    rules, in_table, section, title = [], False, 0, ""
    for ln in table.read_text(encoding="utf-8").splitlines():
        head = re.match(r"^#{2,3}\s+(\d+)(?:\.\d+)?\.?\s+(.*)$", ln.strip())
        if head:
            num = int(head.group(1))
            if not ln.strip().startswith("###") or num != section:
                section, title = num, head.group(2).strip()
            in_table = False
            continue

        if not ln.startswith("|"):
            in_table = False
            continue
        if any(h in ln for h in RULE_HEADER):
            in_table = True
            continue
        if not in_table or re.match(r"^\|\s*-", ln):
            continue

        cells = [c.strip() for c in ln.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        left = re.sub(r"[`*]", "", cells[0]).split("(")[0].strip()
        suggest = re.sub(r"[`*]", "", cells[1]).strip() if len(cells) > 1 else ""
        for found in split_left(left):
            rules.append({
                "found": found, "suggest": suggest, "section": f"§{section} {title}".strip(),
                "tier": "고침" if section == FIX_SECTION else "검토",
                "fixable": section == FIX_SECTION and bool(suggest) and " · " not in suggest,
            })
    return rules


# 한 칸에 활용형을 여럿 적은 행이 있다 — `적는다 · 적었다`, `올라간다 · 내려간다`.
# 통째로 한 규칙으로 두면 어느 쪽도 걸리지 않으므로 갈라서 각각을 규칙으로 만든다.
MIN_LEN = 2          # 홑 표현. `익일`·`요망` 은 두 글자로 충분히 특정된다
MIN_SPLIT_LEN = 3    # 갈라 나온 조각


def split_left(left: str) -> list[str]:
    """
    「쓰지 않는다」 칸을 규칙 목록으로 바꾼다.

    갈라 나온 조각에는 더 엄한 길이 하한을 건다. `상기 · 하기 · 여히` 의 `하기` 가
    그 이유다 — 「실행하기」·「하기 전에」의 `하기` 와 구별하려면 형태소 분석이
    필요하다. 두 글자 조각은 버린다. 못 잡는 편이 아무 데나 거는 편보다 낫다.
    """
    if " · " not in left:
        return [left] if len(left) >= MIN_LEN else []
    return [p for p in (s.strip() for s in left.split(" · ")) if len(p) >= MIN_SPLIT_LEN]


# ── 산문만 남기기 ─────────────────────────────────────────────

TAG = re.compile(r"<[^>]*>")
SKIP_BLOCK = re.compile(r"</?(?:pre|code|script|style)\b", re.I)


def _blank(m: re.Match) -> str:
    """열 번호가 어긋나지 않게 같은 길이의 공백으로 지운다."""
    return " " * len(m.group(0))


def prose_lines(text: str, html: bool):
    """(줄 번호, 검사 대상 문자열) 을 낸다. 검사하면 안 되는 자리는 공백으로 지운다."""
    fence = skip = False
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()

        if html:
            for m in SKIP_BLOCK.finditer(raw):
                skip = not m.group(0).startswith("</")
            if skip or not s:
                continue
            line = TAG.sub(_blank, raw)
            if EXEMPT in raw:
                continue
        else:
            if s.startswith("```"):
                fence = not fence
                continue
            if fence or s.startswith(">") or s.startswith("|") or EXEMPT in s:
                continue
            line = raw

        yield i, QUOTED.sub(_blank, line)


def heading_lines(text: str):
    """마크다운 절 제목만 낸다. HTML 은 대상이 아니다 — 조판된 제목은 도해일 수 있다."""
    fence = False
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s.startswith("#") or EXEMPT in s:
            continue
        title = re.sub(r"^#+\s*", "", s)
        title = re.sub(r"^[\d.]+\s*", "", title).strip().rstrip(".")
        if title:
            yield i, title


# ── 검사 ────────────────────────────────────────────────────

def lint(text: str, name: str = "-", rules=None, html: bool = False) -> list[Finding]:
    rules = load_rules() if rules is None else rules
    out = []

    for i, line in prose_lines(text, html):
        for r in rules:
            start = 0
            while (at := line.find(r["found"], start)) != -1:
                out.append(Finding(name, i, at + 1, r["tier"], r["section"],
                                   r["found"], r["suggest"], line.strip()[:80]))
                start = at + len(r["found"])

    if not html:
        for i, title in heading_lines(text):
            if not re.search(r"[가-힣]", title):      # 영문 표제는 대상이 아니다
                continue
            if BAD_HEADING.search(title) or QUESTION_OPENER.match(title):
                out.append(Finding(name, i, 1, "제목", "§1.1 제목은 명사구",
                                   title, "명사구로 고친다", title[:80]))

    out.sort(key=lambda f: (f.line, f.col))
    return out


def fix(text: str, rules) -> tuple[str, int]:
    """§1 어미만 치환한다. 나머지는 문맥을 봐야 하므로 손대지 않는다."""
    hits = 0
    lines = text.splitlines(keepends=True)
    fence = False
    for n, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or s.startswith(">") or s.startswith("|") or EXEMPT in s:
            continue
        guard = QUOTED.sub(_blank, raw)
        for r in rules:
            if not r["fixable"]:
                continue
            at = guard.find(r["found"])
            while at != -1:
                raw = raw[:at] + r["suggest"] + raw[at + len(r["found"]):]
                guard = (guard[:at] + " " * len(r["suggest"])
                         + guard[at + len(r["found"]):])
                hits += 1
                at = guard.find(r["found"], at + len(r["suggest"]))
        lines[n] = raw
    return "".join(lines), hits


# ── 보고 ────────────────────────────────────────────────────

def report(found: list[Finding]) -> None:
    if not found:
        print("문체 규약 위반 없음")
        return
    width = max(len(f.tier) for f in found)
    for f in found:
        arrow = f" → {f.suggest}" if f.suggest else ""
        print(f"{f.path}:{f.line}:{f.col}  [{f.tier:{width}}] "
              f"{f.found}{arrow}    ({f.section})")
    tally = {t: sum(1 for f in found if f.tier == t) for t in TIERS}
    print("\n" + " · ".join(f"{t} {n}" for t, n in tally.items() if n))
    print("인용이 꼭 필요하면 백틱·「」로 감싸거나 줄 끝에 <!-- style-exempt --> 를 단다.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="한국어 보고 문서 문체 규약 검사")
    ap.add_argument("paths", nargs="+", help="검사할 파일. - 는 표준 입력")
    ap.add_argument("--json", action="store_true", help="기계가 읽는 형식으로 낸다")
    ap.add_argument("--tier", choices=TIERS, action="append",
                    help="이 갈래만 본다. 여러 번 줄 수 있다")
    ap.add_argument("--fix", action="store_true",
                    help="§1 어미를 파일에 직접 치환한다. 나머지는 손대지 않는다")
    a = ap.parse_args(argv)

    rules = load_rules()
    found: list[Finding] = []
    fixed = 0

    for name in a.paths:
        if name == "-":
            text, path, html = sys.stdin.read(), "-", False
        else:
            path = pathlib.Path(name)
            if not path.exists():
                print(f"파일이 없다: {path}", file=sys.stderr)
                return 2
            text = path.read_text(encoding="utf-8")
            html = path.suffix.lower() in (".html", ".htm")

        if a.fix and name != "-":
            text, n = fix(text, rules)
            if n:
                path.write_text(text, encoding="utf-8")
                fixed += n
                print(f"{path} — 어미 {n}곳을 고쳤다")

        found += lint(text, str(path), rules, html)

    if a.tier:
        found = [f for f in found if f.tier in a.tier]

    if a.json:
        print(json.dumps({"findings": [f.as_dict() for f in found], "fixed": fixed},
                         ensure_ascii=False, indent=2))
    else:
        report(found)

    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())

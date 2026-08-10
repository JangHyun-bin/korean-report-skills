# -*- coding: utf-8 -*-
"""
new-document.py — 새 문서 생성기의 뼈대를 만든다.

    python scripts/new-document.py --title "문서 제목" --mode paper
    python scripts/new-document.py --title "협의 자료" --mode deck --out agenda.py

만들어진 파일은 **그 자체로 전체 파이프라인을 돈다.**

    python 문서제목.py            생성 → mathbuild → QA 까지 한 번에

`SKILL.md` §2 를 처음부터 읽지 않아도 첫 문서가 나오게 하는 것이 목적이다.
파이프라인을 이해하고 나면 생성된 파일을 그대로 고쳐 쓰면 된다.
"""
import argparse
import pathlib
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "skills" / "korean-report-doc" / "assets"

PAPER_BODY = '''<header class="paper-head">
<p class="eyebrow">기술보고 · {date}</p>
<h1>{title}</h1>
<p class="subtitle">부제</p>
<div class="byline"><span>소속 · 작성자</span><span>{date}</span></div>
</header>

<section class="abstract"><h2>ABSTRACT</h2>
<p>발견한 것, 새로 기여한 것, 아직 없는 것을 이 순서로 적는다.</p>
<div class="legend">%s 실제로 측정된 값 · %s 수단은 있으나 미사용 · %s 아직 측정하지 않음</div>
</section>

<section id="s1"><h2><span class="sn">1</span>첫 절</h2>
<p>결과를 먼저 적고 배경을 뒤에 둔다. 제목은 명사구로 쓴다.</p>
%s%s
%s%s
</section>

<section id="s2"><h2><span class="sn">2</span>둘째 절</h2>
<div class="finding"><p>이 문서가 주장하는 것.</p>
<p class="cav">그 주장의 한계.</p></div>
<ol class="concl"><li>결정이 필요한 것.</li></ol>
</section>'''

# 치환 자리 수와 순서는 PAPER_BODY 와 같아야 한다 —
# 생성기의 sub() 호출이 두 모드에서 같은 인자 목록을 넘기기 때문이다.
DECK_BODY = '''<section class="tile black cover"><div class="wrap">
<h1 class="hero">{title}</h1>
<div class="rule"></div>
<div class="meta">{date}<br>소속 · 작성자</div>
</div></section>

<section class="tile light"><div class="wrap">
<p class="eyebrow">아젠다</p>
<h2><span class="sn">1</span>첫 절</h2>
<p>한 페이지에 한 가지만 담는다. 문단이 길어지면 paper 모드가 맞다.</p>
<div class="legend">%s 실제로 측정된 값 · %s 수단은 있으나 미사용 · %s 아직 측정하지 않음</div>
</div></section>

<section class="tile dark"><div class="wrap">
<p class="eyebrow">핵심</p>
<h2><span class="sn">2</span>가장 중요한 절</h2>
%s%s
</div></section>

<section class="tile parch"><div class="wrap">
<h2><span class="sn">3</span>상태와 결정 요청</h2>
%s%s
<ol class="concl"><li>결정이 필요한 것.</li></ol>
</div></section>'''

TEMPLATE = '''# -*- coding: utf-8 -*-
"""{title} — 생성기

    python {stem}.py [--font <woff2>]...

생성 → mathbuild → QA 를 한 번에 돈다. 산출물은 {stem}.html 이다.
"""
import pathlib
import subprocess
import sys

ASSETS = pathlib.Path(r"{assets}")
sys.path.insert(0, str(ASSETS))

from figures import (  # noqa: E402
    BADGE_IMPL, BADGE_MEAS, BADGE_NONE, esc, fig_compare, figcap, tbl, tblcap,
)

TITLE = "{title}"
MODE = "{mode}"
HERE = pathlib.Path(__file__).resolve().parent
STEM = "{stem}"


def I(t):   # 인라인 수식
    return "\\u27e6I\\u27e7" + t + "\\u27e6/I\\u27e7"


def D(t):   # 디스플레이 수식
    return "\\u27e6D\\u27e7" + t + "\\u27e6/D\\u27e7"


def sub(tpl, *args):
    """%s 를 순서대로 치환하고 %% 를 % 로 되돌린다"""
    out, i, ai = [], 0, 0
    while True:
        j = tpl.find("%s", i)
        if j < 0:
            out.append(tpl[i:]); break
        out.append(tpl[i:j]); out.append(str(args[ai])); ai += 1; i = j + 2
    return "".join(out).replace("%%", "%")


# ── 여기부터 고쳐 쓴다 ──────────────────────────────────────
FIG = fig_compare(
    rows=[("항목 A", 60, 100, "60", "100"),
          ("항목 B", 35, 80, "35", "80")],
    maxv=100, title="개선 전후", sub="진한 막대가 현재",
    note="같은 단위끼리만 한 그림에 올린다")

TBL = tbl(
    ["항목", "상태", "값"],
    [["측정한 것", BADGE_MEAS, "60"],
     ["수단은 있는 것", BADGE_IMPL, "미적용"],
     {{"c": "hl", "v": ["아직 없는 것", BADGE_NONE, esc("—")]}}],
    cls="num")

BODY = sub("""{body}""",
           BADGE_MEAS, BADGE_IMPL, BADGE_NONE,
           FIG, figcap(1, "그림 설명"),
           TBL, tblcap(1, "표 설명"))
# ── 여기까지 ────────────────────────────────────────────────


def main() -> int:
    fonts = []
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--font" and i + 1 < len(argv):
            fonts += ["--font", argv[i + 1]]

    tpl = (ASSETS / f"{{MODE}}_template.html").read_text(encoding="utf-8")
    raw = HERE / f"{{STEM}}_raw.html"
    out = HERE / f"{{STEM}}.html"
    raw.write_text(tpl.replace("__BODY__", BODY).replace("__TITLE__", TITLE), encoding="utf-8")

    build = subprocess.run(
        ["node", str(ASSETS / "mathbuild.js"), str(raw), str(out),
         "--assets", str(ASSETS), *fonts])
    if build.returncode:
        return build.returncode

    qa = ASSETS.parent.parent.parent / "scripts" / "qa.py"
    if qa.exists():
        return subprocess.run([sys.executable, str(qa), str(out)]).returncode
    print(f"{{out}} — QA 스크립트를 찾지 못해 건너뛴다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def slug(title: str) -> str:
    s = re.sub(r"[^\w가-힣]+", "_", title).strip("_")
    return s or "document"


def main() -> int:
    ap = argparse.ArgumentParser(description="새 문서 생성기의 뼈대를 만든다")
    ap.add_argument("--title", required=True, help="문서 제목")
    ap.add_argument("--mode", choices=["paper", "deck"], default="paper")
    ap.add_argument("--date", default="", help="표지에 넣을 날짜. 비우면 자리표시자만 둔다")
    ap.add_argument("--out", type=pathlib.Path, default=None, help="생성할 .py 경로")
    args = ap.parse_args()

    stem = slug(args.title)
    out = args.out or pathlib.Path(f"{stem}.py")
    if out.exists():
        print(f"이미 있다: {out}. --out 으로 다른 경로를 준다.", file=sys.stderr)
        return 1

    body = (PAPER_BODY if args.mode == "paper" else DECK_BODY).format(
        title=args.title, date=args.date or "YYYY-MM-DD")
    out.write_text(
        TEMPLATE.format(title=args.title, mode=args.mode, assets=ASSETS,
                        stem=out.stem, body=body),
        encoding="utf-8")

    print(f"만들었다 — {out}")
    print()
    print("다음:")
    print(f"  python {out}                      # 생성 → 빌드 → QA")
    print(f"  python {out} --font Pretendard-Regular.woff2   # 글꼴 내장")
    print()
    print("`# 여기부터 고쳐 쓴다` 구간의 도해·표·본문을 바꾸면 된다.")
    print("도해 7종은 references/figures.md, 문체 규약은 korean-report-style 참조.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

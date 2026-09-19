# -*- coding: utf-8 -*-
"""
build_styleguide.py — token 과 component 를 한 문서에 늘어놓는 styleguide.

    python examples/build_styleguide.py            paper · deck 둘 다
    python examples/build_styleguide.py paper

dist/styleguide_<mode>_raw.html 을 생성한다. 이어서 실제 문서와 같은 mathbuild.js 를
통과시킨다 — 별도 렌더 경로를 두면 styleguide 만 통과하고 문서는 깨지는 일이 생긴다.

각 절은 <section data-sg="<id>"> 로 구분한다. 내용은 가상 사례 「A사 — 인라인 계측
체계 확립과 수율 개선」에서 가져온다.
"""
import itertools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "plugins" / "korean-report" / "skills" / "korean-report-doc" / "assets"
sys.path.insert(0, str(ASSETS))
sys.path.insert(0, str(ROOT / "scripts"))

import csstokens as T  # noqa: E402
from figures import (  # noqa: E402
    BADGE_IMPL,
    BADGE_MEAS,
    BADGE_NO,
    BADGE_NONE,
    fig_cards,
    fig_compare,
    fig_flow,
    fig_gantt,
    fig_numberline,
    fig_scatter,
    fig_timeline,
    figcap,
    tbl,
    tblcap,
    wide,
)

TOKENS = (ASSETS / "css" / "tokens.css").read_text(encoding="utf-8")
ROOT_T = T.declared(TOKENS, ":root")
DARK_T = T.declared(TOKENS, ".dark")
BLACK_T = T.declared(TOKENS, ".black")
STEPS = ["-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
SAMPLE = f"A사 인라인 계측 3,240 m² · 검사 SDK v2.1 — 위치 오차 ±0.35 m, 갱신 주기 12 ms {BADGE_MEAS}"
SHORT = "계측 3,240 m² · ±0.35 m"
COLOR_TOKENS = ["--ink", "--ink-2", "--ink-3", "--accent", "--surface", "--surface-2", "--surface-3",
                "--rule", "--rule-soft", "--mark", "--fig-line", "--fig-soft", "--fig-pale", "--fig-mid"]
# (이름, class, 배경) — paper 에서는 div 로, deck 에서는 tile 로 surface 를 재현한다
SURFACES = [("light", "", "var(--surface)"), ("parch", "", "var(--surface-2)"),
            ("dark", "dark", "var(--surface)"), ("black", "black", "var(--surface)")]
_fig_no = itertools.count(1)


def section(sg, n, title, body):
    return (f'<section id="sg-{sg}" data-sg="{sg}"><h2><span class="sn">{n}</span>{title}</h2>\n'
            f'{body}\n</section>')


def surface_box(cls, bg, inner):
    return (f'<div class="{cls}" style="background:{bg};color:var(--ink);padding:24px;'
            f'border-radius:12px;margin:16px 0">{inner}</div>')


def ratio(fg, bg):
    ok = fg.startswith("#") and bg.startswith("#")
    return f"{T.contrast(fg, bg):.2f}" if ok else "—"


def color_section():
    rows = []
    for name in COLOR_TOKENS:
        light, dark = ROOT_T[name], DARK_T.get(name, ROOT_T[name])
        chip = (f'<span style="display:inline-block;width:40px;height:16px;background:var({name});'
                'border:1px solid var(--rule)"></span>')
        rows.append([f"<code>{name}</code>", chip, light, ratio(light, ROOT_T["--surface"]),
                     ratio(light, ROOT_T["--surface-2"]), dark, ratio(dark, DARK_T["--surface"]),
                     ratio(dark, BLACK_T["--surface"])])
    head = ["token", "", "light", "대 surface", "대 surface-2", "dark", "대 dark", "대 black"]
    # 8열 표는 720px 본문 폭을 넘는다 — 가로 스크롤 컨테이너로 감싼다.
    return wide(tbl(head, rows, cls="num")) + tblcap(1, "색 token 과 WCAG 대비비")


def type_section(sample, steps=STEPS):
    out = []
    for s in steps:
        t, lh, tr = (ROOT_T[f"--{p}{s}"] for p in ("t", "lh", "tr"))
        out.append(f'<p class="srcline">t{s} · {t} / {lh} · {tr}</p>'
                   f'<p style="font-size:var(--t{s});line-height:var(--lh{s});letter-spacing:var(--tr{s})">'
                   f'{sample}</p>')
    return "\n".join(out)


def space_section():
    return "\n".join(
        f'<div style="display:flex;align-items:center;gap:12px;margin:4px 0"><code>--s-{n}</code>'
        f'<span style="display:inline-block;height:12px;width:var(--s-{n});background:var(--accent)"></span>'
        f'{ROOT_T[f"--s-{n}"]}</div>' for n in range(1, 11))


def components():
    table = tbl(["항목", "개선 전", "개선 후", "상태"],
                [["계측 시간", "900초", "590초", BADGE_MEAS],
                 {"c": "hl", "v": ["유효 검출률", "4/7", "5/7", BADGE_MEAS]},
                 ["오버레이", "—", "—", BADGE_NONE]], cls="num")
    return f'''<p class="eyebrow">eyebrow</p>
<p>본문 — {SAMPLE}. <mark>강조는 독자 층위다.</mark>
<a href="#sg-tokens-color">링크</a> · <code>retryLimit</code></p>
<div class="legend">{BADGE_MEAS} 실측 · {BADGE_IMPL} 구현됨 · {BADGE_NONE} 미측정 · {BADGE_NO} 해당 없음</div>
<h3>h3 — 소제목</h3>
{table}
<div class="note"><p>note — 보충 설명.</p></div>
<div class="warn"><p>warn — 주의가 필요한 전제.</p></div>
<div class="finding"><p>finding — 이 문서의 주장.</p><p class="cav">cav — 그 주장의 한계.</p></div>
<div class="claim">claim — 한 문장 요지.</div>
<div class="metrics"><div class="metric"><div class="mlabel">계측 시간</div><div class="mval">590초</div>
<div class="mnote">웨이퍼당 · 실측</div></div>
<div class="metric gap"><div class="mlabel">오버레이</div><div class="mval">—</div>
<div class="mnote">미측정</div></div></div>
<ul class="plain"><li>plain 목록 항목</li><li>두 번째 항목</li></ul>
<ol class="concl"><li>결론 목록 항목</li><li>두 번째 결론</li></ol>
<blockquote>blockquote — 인용한 원문.</blockquote>
<div class="quote-box"><p>quote-box — 강조 인용.</p></div>
<div class="rsn"><div class="rsn-no">근거 1</div><p>rsn — 근거 카드.</p></div>
<pre><span class="c"># code block</span>
retryLimit = 3</pre>
<p class="srcline">출처 — A사 계측 기록(가상) · 2026-08-31</p>'''


def figure_set():
    figs = [
        fig_timeline([("2026-08-10", "08-10", "계측 규격 초안", True),
                      ("2026-10-22", "10-22", "인증 시험", False)],
                     "2026-08-01", "2026-11-01", note="남은 82일"),
        fig_cards([(1, "검사–빈닝 연결", "판정 기준 정정"), (2, "양산 조건 벤치", "수율 재측정")]),
        fig_flow([("검사", "결함 좌표"), ("빈닝", "판정"), ("분석", "수율")], highlight=1),
        fig_numberline([("개선 후", 590.0), ("개선 전", 900.0)], 0, 1000),
        fig_compare([("계측 시간", 590, 900, "590초", "900초")], 1000),
        fig_scatter([(1, 2, "L1"), (2, 3, "L2"), (3, 1.5, "L3")], 0, 4),
    ]
    out = [f + figcap(next(_fig_no), "도해 견본") for f in figs]
    out.append(fig_gantt([("검사 레시피 정비", "2026-08-01", "2026-08-25", "done"),
                          ("오버레이 계측 보강", "2026-08-20", "2026-09-20", "plan"),
                          ("인증 시험", "2026-10-01", "2026-10-25", "key")],
                         "2026-08-01", "2026-11-01", markers=[("2026-08-31", "품질보고", "gate")]))
    return "\n".join(out)


def math_section():
    table = tbl(["기호", "의미"], [["⟦I⟧D_0⟦/I⟧", "결함 밀도"], ["⟦I⟧A⟦/I⟧", "다이 면적"]])
    return (r"<p>수율 ⟦I⟧Y⟦/I⟧ 는 다음과 같다.</p>"
            r"⟦D⟧Y = \left(1 + \frac{D_0 A}{\alpha}\right)^{-\alpha}⟦/D⟧" + table)


KEEPALL = ("<p>인라인계측장비의 교정주기재산정 결과를 양산조건기준수율벤치에 반영하였다. "
           "어절 단위 줄바꿈이 적용되면 「교정주기재산정」 같은 긴 어절이 중간에서 잘리지 않는다. "
           "분절할 수 없는 문자열은 overflow-wrap 이 처리한다 — "
           "https://example.com/very/long/path/that/cannot/break/at/any/space</p>")

PUNCT = ("<ul class=\"plain\"><li>중간점 — 그림 3 · 제목</li><li>줄표 — K — 핵심이자 약점</li>"
         "<li>범위 — 600–900 ms</li><li>단위 — 0.35 m · 12 ms · 4.8%</li>"
         "<li>인용 — 「계측 규격 초안」</li></ul>")


def tnum_section():
    rows = [["1111", "0.35", "12,340"], ["8888", "10.07", "3,240"], ["1010", "0.08", "999"]]
    return (tbl(["정수", "소수", "천 단위"], rows, cls="num")
            + tblcap(2, "tabular-nums — 자릿수가 세로로 정렬된다"))


def breaks_section():
    long = tbl(["회차", "계측 시간", "검출률"],
               [[f"{i}", f"{900 - i * 10}초", f"{i % 7}/7"] for i in range(1, 25)], cls="num")
    return "\n".join([long, tblcap(3, "쪽 경계에 걸리는 긴 표"),
                      '<div class="finding"><p>표 다음 callout — 쪽 경계에서 잘리지 않아야 한다.</p></div>',
                      figure_set()])


def paper():
    parts = [
        '<header class="paper-head"><p class="eyebrow">styleguide · paper</p>'
        '<h1>korean-report-doc styleguide</h1>'
        '<p class="subtitle">token · component · 도해 · typesetting 검사</p>'
        '<div class="byline"><span>가상 사례 A사</span><span>2026-09-19</span></div></header>',
        section("tokens-color", 1, "색 token 과 대비", color_section()),
        section("tokens-type", 2, "type scale 13단계", type_section(SAMPLE)),
        section("tokens-space", 3, "space token", space_section()),
        *[section(f"comp-{name}", 4 + i, f"component — {name}", surface_box(cls, bg, components()))
          for i, (name, cls, bg) in enumerate(SURFACES)],
        section("fig-light", 8, "도해 — light", figure_set()),
        section("fig-dark", 9, "도해 — dark", surface_box("dark", "var(--surface)", figure_set())),
        section("math", 10, "수식", math_section()),
        section("check-keepall", 11, "어절 단위 줄바꿈", KEEPALL),
        section("check-tnum", 12, "숫자 폭 정렬", tnum_section()),
        section("check-punct", 13, "문장부호와 단위", PUNCT),
        section("check-breaks", 14, "쪽 경계", breaks_section()),
    ]
    return "\n".join(parts)


def tile(bg, sg, n, title, body):
    return (f'<section class="tile {bg}" data-sg="{sg}"><div class="wrap">'
            f'<h2><span class="sn">{n}</span>{title}</h2>\n{body}\n</div></section>')


def deck_components():
    table = tbl(["항목", "개선 전", "개선 후"],
                [["계측 시간", "900초", "590초"], {"c": "hl", "v": ["유효 검출률", "4/7", "5/7"]}], cls="num")
    return f'''<div class="legend">{BADGE_MEAS} 실측 · {BADGE_IMPL} 구현됨 · {BADGE_NONE} 미측정</div>
{table}
<div class="finding"><p>finding — 이 문서의 주장. <mark>강조</mark> · <code>retryLimit</code></p>
<p class="cav">cav — 한계.</p></div>
<div class="metrics"><div class="metric"><div class="mlabel">계측 시간</div>
<div class="mval">590초</div></div>
<div class="metric gap"><div class="mlabel">오버레이</div><div class="mval">—</div></div></div>'''


def deck():
    # 인접 tile 은 배경을 공유하지 않는다. black 은 표지 전용이다(design.md §2.1) —
    # EOD tile 은 deck_template.html 이 이미 붙인다.
    cover = ('<section class="tile black cover" data-sg="cover"><div class="wrap">'
             '<h1 class="hero">styleguide · deck</h1><div class="rule"></div>'
             '<div class="meta">가상 사례 A사<br>2026-09-19</div></div></section>')
    cards = fig_cards([(1, "검사–빈닝 연결", "판정 기준 정정"), (2, "양산 조건 벤치", "수율 재측정")])
    compare = fig_compare([("계측 시간", 590, 900, "590초", "900초")], 1000)
    return "\n".join([
        cover,
        # type scale 13단계를 한 tile 에 다 넣으면 한 쪽을 넘는다(qa.py: 「한 쪽을
        # 넘는다」) — 두 tile 로 나눈다(controller 결정 1). component tile 은
        # deck_components() 그대로도 한 쪽 안에 들어가 나누지 않는다.
        tile("light", "tokens-type-1", 1, "type scale · -3 ~ 3", type_section(SHORT, STEPS[:7])),
        tile("dark", "tokens-type-2", 2, "type scale · 4 ~ 9", type_section(SHORT, STEPS[7:])),
        tile("parch", "comp-parch", 3, "component — parch", deck_components()),
        tile("dark", "comp-dark", 4, "component — dark", deck_components()),
        tile("light", "comp-light", 5, "component — light", deck_components()),
        tile("parch", "fig-parch", 6, "도해 — parch", cards + figcap(1, "도해 견본")),
        tile("dark", "fig-dark", 7, "도해 — dark", compare + figcap(2, "도해 견본")),
    ])


def build(mode):
    body = paper() if mode == "paper" else deck()
    tpl = (ASSETS / f"{mode}_template.html").read_text(encoding="utf-8")
    html = tpl.replace("__BODY__", body).replace("__TITLE__", f"styleguide {mode}")
    out = ROOT / "dist" / f"styleguide_{mode}_raw.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    for m in sys.argv[1:] or ["paper", "deck"]:
        if m not in ("paper", "deck"):
            raise SystemExit(f"모드는 paper 또는 deck 이다 — 받은 값: {m}")
        print(build(m))

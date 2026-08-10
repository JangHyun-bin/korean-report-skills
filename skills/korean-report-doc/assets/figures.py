# -*- coding: utf-8 -*-
"""
figures.py — 도해·표 생성 헬퍼

이 파일을 생성기에서 import 하거나 내용을 복사해 쓴다.
모든 도해는 인라인 SVG 문자열을 반환한다. 래스터를 만들지 않는다.

색 — 리터럴 hex 를 박지 않고 **클래스로 방출한다**(fi-* 채움 · st-* 선).
base.css 가 그 클래스를 CSS 변수에 연결하므로 도해가 문서 토큰을 실제로 상속한다.
다크 타일 위에서는 deck.css 가 토큰을 바꾸고, 도해는 자동으로 따라간다.
hex 를 박으면 #1d1d1f 글자가 #272729 타일 위에서 사라진다(실제로 겪은 버그).

좌표계 — SVG 는 y 가 아래로 증가한다. 모든 배치 계산을 그 기준으로 한다.
matplotlib 식 y-up 으로 계산한 뒤 뒤집지 않으면 행 순서가 역전된다(실제로 겪은 버그).

경계조건 — 기간이 0 이거나 축 범위가 뒤집힌 입력은 ValueError 로 즉시 실패한다.
조용히 깨진 도해를 내보내는 것이 도해가 없는 것보다 나쁘다.
"""
import itertools

# 팔레트 — base.css 의 토큰과 1:1 로 대응한다. 값을 바꾸면 양쪽을 함께 바꾼다.
INK   = '#1d1d1f'   # 본문·최중요 요소      → --ink        · fi-ink   / st-ink
INK48 = '#7a7a7a'   # 캡션·축 라벨          → --ink48      · fi-ink48 / st-ink48
PRI   = '#0066cc'   # 액센트 — 그 하나       → --primary    · fi-pri   / st-pri
MID   = '#8695a6'   # 화살표·보조 막대       → --fig-mid    · fi-mid   / st-mid
LINE  = '#c7ccd2'   # 테두리                → --fig-line   · fi-line  / st-line
SOFT  = '#dfe4e9'   # 채움                  → --fig-soft   · fi-soft
PALE  = '#eef3f8'   # 강조 배경             → --fig-pale   · fi-pale
FONT  = 'Pretendard'

_seq = itertools.count(1)   # SVG 내부 id 충돌 방지 (한 문서에 도해가 여럿일 때)


# ══════════════════════════════════════════════════ 이스케이프
def esc(s):
    """표·라벨에 넣을 신뢰할 수 없는 문자열을 HTML 이스케이프한다."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;").replace('"', "&quot;"))


# ══════════════════════════════════════════════════ 표
def tbl(head, rows, cls=""):
    """
    rows: list. 각 원소는 list 또는 {"c":"hl","v":[...]} (하이라이트 행)

    셀은 **원시 HTML 로 취급**한다. 배지(BADGE_MEAS)와 수식 마커(⟦I⟧)를
    셀에 직접 넣는 것이 정상 용법이기 때문이다.
    외부에서 들어온 값은 호출부에서 esc() 로 감싼다.
    """
    h = "".join("<th>" + str(c) + "</th>" for c in head)
    b = ""
    for r in rows:
        if isinstance(r, dict):
            b += '<tr class="' + r.get("c", "") + '">' + \
                 "".join("<td>" + str(c) + "</td>" for c in r["v"]) + "</tr>"
        else:
            b += "<tr>" + "".join("<td>" + str(c) + "</td>" for c in r) + "</tr>"
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def wide(t):
    """7열 이상 표를 가로 스크롤로 감싼다. 인쇄 시 자동 축소된다."""
    return '<div class="scroll wide">' + t + '</div>'


# ══════════════════════════════════════════════════ 상태 배지
BADGE_MEAS = '<span class="bdg meas">실측</span>'
BADGE_IMPL = '<span class="bdg impl">구현됨</span>'
BADGE_NONE = '<span class="bdg none">미측정</span>'
BADGE_NO   = '<span class="bdg no">불가</span>'


def _span(start, end, what="기간"):
    """iso 두 날짜의 일수 차. 0 이하이면 실패한다."""
    import datetime
    b = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    d = (e - b).days
    if d <= 0:
        raise ValueError(f"{what}이 0 이하다 — start={start} end={end}")
    return b, e, d


# ══════════════════════════════════════════════════ 1. 타임라인
def fig_timeline(marks, start, end, title="", note="", bands=None):
    """
    marks : [(iso날짜, 라벨, 설명, 강조여부)]
    bands : [(시작iso, 끝iso, 라벨, 강조여부)] — 구간 표시
    """
    import datetime
    b, e, T = _span(start, end, "타임라인 기간")
    X = lambda d: 60 + (datetime.date.fromisoformat(d) - b).days / T * 790

    out = ""
    for i, (d, lab, desc, hl) in enumerate(marks):
        lab, desc = esc(lab), esc(desc)
        x = X(d); up = (i % 2 == 0)
        fi, st = ("fi-pri", "st-pri") if hl else ("fi-ink48", "st-ink48")
        y1, y2 = (96, 120) if up else (152, 128)
        ty, ty2 = (88, 74) if up else (172, 186)
        out += f'<line class="{st}" x1="{x:.1f}" y1="{y1}" x2="{x:.1f}" y2="{y2}" stroke-width="1.2"/>'
        out += f'<circle class="{fi}" cx="{x:.1f}" cy="124" r="5"/>'
        out += (f'<text class="{fi}" x="{x:.1f}" y="{ty}" text-anchor="middle" '
                f'font-size="12" font-weight="600">{lab}</text>')
        out += (f'<text class="fi-ink48" x="{x:.1f}" y="{ty2}" text-anchor="middle" '
                f'font-size="10.5">{desc}</text>')

    bd = ""
    for s, t, lab, hl in (bands or []):
        lab = esc(lab)
        sx, ex = X(s), X(t)
        cls = "fi-pale st-pri" if hl else "fi-soft"
        dash = ' stroke-dasharray="4 3"' if hl else ''
        tcls = "fi-pri" if hl else "fi-ink48"
        bd += (f'<rect class="{cls}" x="{sx:.1f}" y="196" width="{max(ex-sx,0):.1f}" '
               f'height="30" rx="6"{dash}/>')
        bd += (f'<text class="{tcls}" x="{(sx+ex)/2:.1f}" y="215" text-anchor="middle" '
               f'font-size="11.5">{lab}</text>')

    return f'''<svg viewBox="0 0 900 250" class="fig" role="img" aria-label="{esc(title)}">
<g font-family="{FONT}">{bd}
<line class="st-line" x1="60" y1="124" x2="850" y2="124" stroke-width="1.6"/>
{out}
<circle class="fi-canvas st-ink" cx="60" cy="124" r="7" stroke-width="2"/>
<text class="fi-ink48" x="60" y="242" font-size="11">{esc(note)}</text>
</g></svg>'''


# ══════════════════════════════════════════════════ 2. 간트
def fig_gantt(tasks, start, end, markers=None, title=""):
    """
    tasks   : [(라벨, 시작iso, 끝iso, kind)]  kind ∈ done|plan|wbs|key
    markers : [(iso, 라벨, kind)]             kind ∈ meet|gate|pilot

    HTML 을 반환한다. 막대 색과 마커 선종은 base.css 의 .gbar / .gmark 가 정한다.
    인라인 style 은 위치(left·width)만 나른다.
    """
    import datetime
    b, e, T = _span(start, end, "간트 기간")
    P = lambda d: (datetime.date.fromisoformat(d) - b).days / T * 100

    KINDS = ("done", "plan", "wbs", "key")
    MARKS = ("meet", "gate", "pilot")
    rows = ""
    for lab, s, t, k in tasks:
        lab = esc(lab)
        if k not in KINDS:
            raise ValueError(f"알 수 없는 kind: {k} — {' | '.join(KINDS)} 중 하나여야 한다")
        l, w = P(s), P(t) - P(s)
        rows += (f'<div class="grow"><div class="glabel">{lab}</div>'
                 f'<div class="gtrack"><div class="gbar {k}" '
                 f'style="left:{l:.2f}%;width:{max(w,0):.2f}%"></div></div></div>')

    mk = ""
    for d, lab, k in (markers or []):
        lab = esc(lab)
        if k not in MARKS:
            raise ValueError(f"알 수 없는 marker kind: {k} — {' | '.join(MARKS)} 중 하나여야 한다")
        mk += f'<div class="gmark {k}" style="left:{P(d):.2f}%"><span>{lab}</span></div>'

    months = ""
    cur = datetime.date(b.year, b.month, 1)
    while cur <= e:
        if cur >= b:
            months += (f'<div class="gline" style="left:{P(cur.isoformat()):.2f}%">'
                       f'<span>{cur.month}월</span></div>')
        cur = datetime.date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)

    return (f'<div class="gantt" role="img" aria-label="{esc(title)}">'
            f'<div class="gmarks">{mk}</div>{rows}'
            f'<div class="gaxis">{months}</div></div>')


# ══════════════════════════════════════════════════ 3. 카드 그리드
def fig_cards(items, title="", sub="", cols=3):
    """
    items : [(번호, 제목, 설명)] — 설명은 "\\n" 으로 줄을 나눈다

    헤더는 전부 같은 색이고 번호로만 구분한다.
    항목마다 색을 다르게 하면 색이 의미를 갖는 것처럼 읽힌다.
    """
    if cols < 1:
        raise ValueError("cols 는 1 이상이어야 한다")
    W, H, GX, GY, R, HH = 280, 132, 20, 18, 10, 30
    PADX = 30
    top = 0
    head_svg = ""
    if title:
        head_svg += (f'<text class="fi-ink" x="{PADX}" y="18" font-size="13" '
                     f'font-weight="600">{esc(title)}</text>')
        top = 30
    if sub:
        head_svg += f'<text class="fi-ink48" x="{PADX}" y="{top+8}" font-size="11.5">{esc(sub)}</text>'
        top += 20

    out = ""
    for i, (n, t, d) in enumerate(items):
        n, t = esc(n), esc(t)
        r, c = divmod(i, cols)
        x = PADX + c * (W + GX)
        y = top + r * (H + GY)          # 아래로 증가 — 행이 위에서 아래로 쌓인다
        out += (f'<rect class="fi-canvas st-line" x="{x}" y="{y}" width="{W}" height="{H}" '
                f'rx="{R}" stroke-width="1"/>')
        # 헤더 바 — 카드 위쪽, 상단 모서리만 둥글게
        out += (f'<path class="fi-ink" d="M{x},{y+HH} L{x},{y+R} A{R},{R} 0 0 1 {x+R},{y} '
                f'L{x+W-R},{y} A{R},{R} 0 0 1 {x+W},{y+R} L{x+W},{y+HH} Z"/>')
        for tx, txt in ((x + 16, n), (x + 40, t)):
            out += (f'<text class="fi-oncard" x="{tx}" y="{y+HH/2}" font-size="12.5" '
                    f'font-weight="600" dominant-baseline="central">{txt}</text>')
        # 설명은 헤더 아래 본문 영역의 수직 중앙에 놓는다
        lines = [esc(x) for x in str(d).split("\n")]
        cy = y + HH + (H - HH) / 2
        for j, line in enumerate(lines):
            ly = cy - (len(lines) - 1) * 19 / 2 + j * 19
            out += (f'<text class="fi-ink" x="{x+W/2}" y="{ly:.1f}" font-size="11.5" '
                    f'text-anchor="middle" dominant-baseline="central">{line}</text>')

    rows = (len(items) + cols - 1) // cols
    VW = PADX * 2 + cols * W + (cols - 1) * GX
    VH = top + rows * H + max(rows - 1, 0) * GY + 12
    return (f'<svg viewBox="0 0 {VW} {VH}" class="fig" role="img" aria-label="{esc(title)}">'
            f'<g font-family="{FONT}">{head_svg}{out}</g></svg>')


# ══════════════════════════════════════════════════ 4. 플로우
def fig_flow(steps, title="", note="", highlight=None):
    """steps : [(제목, 설명)] · highlight : 강조할 인덱스"""
    n = len(steps)
    W, GAP = 196, 36
    aid = f"arrow{next(_seq)}"       # 한 문서에 도해가 여럿이어도 id 가 겹치지 않게
    out = ""
    for i, (t, d) in enumerate(steps):
        t = esc(t)
        x = 30 + i * (W + GAP)
        hl = (i == highlight)
        out += (f'<rect class="{"fi-pale st-pri" if hl else "fi-canvas st-line"}" '
                f'x="{x}" y="56" width="{W}" height="112" rx="10" '
                f'stroke-width="{1.6 if hl else 1}"/>')
        out += (f'<text class="{"fi-pri" if hl else "fi-ink"}" x="{x+14}" y="82" '
                f'font-size="13" font-weight="600">{t}</text>')
        for k, line in enumerate(str(d).split("\n")):
            out += f'<text class="fi-ink48" x="{x+14}" y="{106+k*17}" font-size="10.5">{esc(line)}</text>'
        if i < n - 1:
            ax = x + W + 4
            out += (f'<line class="st-mid" x1="{ax}" y1="112" x2="{ax+GAP-10}" y2="112" '
                    f'stroke-width="1.4" marker-end="url(#{aid})"/>')
    w = 30 + n * (W + GAP)
    return f'''<svg viewBox="0 0 {w} 216" class="fig" role="img" aria-label="{esc(title)}">
<defs><marker id="{aid}" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
<path class="fi-mid" d="M0,0 L8,3 L0,6 z"/></marker></defs>
<g font-family="{FONT}">{out}
<text class="fi-ink48" x="30" y="206" font-size="11">{esc(note)}</text>
</g></svg>'''


# ══════════════════════════════════════════════════ 5. 수직선 (분포)
def fig_numberline(points, lo, hi, marker=None, title="", note=""):
    """
    points : [(라벨, 값)]
    marker : (값, 라벨) — 기준선
    """
    if hi <= lo:
        raise ValueError(f"축 범위가 뒤집혔다 — lo={lo} hi={hi}")
    X = lambda v: 70 + (v - lo) / (hi - lo) * 780
    dots = ""
    for i, (n, v) in enumerate(points):
        n = esc(n)                 # v 는 좌표 계산에 쓰이므로 표시할 때만 이스케이프한다
        up = (i % 2 == 0)
        dots += f'<circle class="fi-pri" cx="{X(v):.1f}" cy="120" r="5.5"/>'
        dots += (f'<text class="fi-ink" x="{X(v):.1f}" y="{100 if up else 150}" '
                 f'text-anchor="middle" font-size="11.5">{n}</text>')
        dots += (f'<text class="fi-ink48" x="{X(v):.1f}" y="{86 if up else 164}" '
                 f'text-anchor="middle" font-size="11">{esc(v)}</text>')
    mk = ""
    if marker:
        mv, ml = marker
        mk = (f'<line class="st-ink" x1="{X(mv):.1f}" y1="46" x2="{X(mv):.1f}" y2="176" '
              f'stroke-width="1.6" stroke-dasharray="5 4"/>'
              f'<text class="fi-ink" x="{X(mv)+8:.1f}" y="42" font-size="12" '
              f'font-weight="600">{esc(ml)}</text>')
    ticks = ""
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        ticks += (f'<line class="st-line" x1="{X(v):.1f}" y1="120" x2="{X(v):.1f}" y2="127"/>'
                  f'<text class="fi-ink48" x="{X(v):.1f}" y="142" text-anchor="middle" '
                  f'font-size="11">{v:.2f}</text>')
    return f'''<svg viewBox="0 0 900 200" class="fig" role="img" aria-label="{esc(title)}">
<g font-family="{FONT}">
<line class="st-line" x1="70" y1="120" x2="850" y2="120" stroke-width="1.4"/>
{ticks}{dots}{mk}
<text class="fi-ink48" x="70" y="192" font-size="11.5">{esc(note)}</text>
</g></svg>'''


# ══════════════════════════════════════════════════ 6. 대비 막대
def fig_compare(rows, maxv, title="", sub="", note=""):
    """
    rows : [(라벨, 주값, 부값, 주표기, 부표기)] — 두 기준 대비

    차이 구간을 파선 사각형으로 감싸 차이 자체가 발견임을 드러낸다.
    주값과 부값의 대소는 가리지 않는다 — 어느 쪽이 크든 구간은 그려진다.
    """
    if maxv <= 0:
        raise ValueError(f"maxv 는 0 보다 커야 한다 — maxv={maxv}")
    X = lambda v: 250 + v / maxv * 520
    out = ""
    for i, (lab, a, b, la, lb) in enumerate(rows):
        lab, la, lb = esc(lab), esc(la), esc(lb)
        y = 76 + i * 84
        out += (f'<text class="fi-ink" x="238" y="{y+6}" text-anchor="end" '
                f'font-size="12.5" font-weight="600">{lab}</text>')
        out += f'<rect class="fi-ink" x="250" y="{y-14}" width="{X(a)-250:.1f}" height="17" rx="4"/>'
        out += (f'<text class="fi-ink" x="{X(a)+10:.1f}" y="{y-1}" font-size="12" '
                f'font-weight="600">{la}</text>')
        out += f'<rect class="fi-soft" x="250" y="{y+8}" width="{X(b)-250:.1f}" height="17" rx="4"/>'
        out += f'<text class="fi-ink48" x="{X(b)+10:.1f}" y="{y+21}" font-size="12">{lb}</text>'
        # 차이 구간 — 음수 폭은 렌더되지 않으므로 항상 작은 쪽에서 시작한다
        x0, x1 = sorted((X(a), X(b)))
        out += (f'<rect class="fi-none st-pri" x="{x0:.1f}" y="{y-14}" '
                f'width="{x1-x0:.1f}" height="39" stroke-dasharray="3 3"/>')
    H = 90 + len(rows) * 84
    return f'''<svg viewBox="0 0 900 {H}" class="fig" role="img" aria-label="{esc(title)}">
<g font-family="{FONT}">
<text class="fi-ink" x="40" y="30" font-size="13" font-weight="600">{esc(title)}</text>
<text class="fi-ink48" x="40" y="48" font-size="11.5">{esc(sub)}</text>
{out}
<text class="fi-pri" x="40" y="{H-12}" font-size="11">{esc(note)}</text>
</g></svg>'''


# ══════════════════════════════════════════════════ 7. 산점 + 모형선
def fig_scatter(points, lo, hi, xlabel="", ylabel="", title=""):
    """points : [(x, y, 라벨)] · y=x 항등선을 함께 그린다"""
    if hi <= lo:
        raise ValueError(f"축 범위가 뒤집혔다 — lo={lo} hi={hi}")
    X = lambda v: 70 + (v - lo) / (hi - lo) * 520
    Y = lambda v: 250 - (v - lo) / (hi - lo) * 200
    dots = ""
    for x, y, lab in points:
        lab = esc(lab)
        dots += f'<circle class="fi-pri" cx="{X(x):.1f}" cy="{Y(y):.1f}" r="6"/>'
        dots += f'<text class="fi-ink" x="{X(x)+14:.1f}" y="{Y(y)+4:.1f}" font-size="11.5">{lab}</text>'
    ticks = ""
    for k in range(6):
        v = lo + (hi - lo) * k / 5
        ticks += (f'<text class="fi-ink48" x="{X(v):.1f}" y="270" text-anchor="middle" '
                  f'font-size="11">{v:g}</text>'
                  f'<text class="fi-ink48" x="58" y="{Y(v)+4:.1f}" text-anchor="end" '
                  f'font-size="11">{v:g}</text>')
    return f'''<svg viewBox="0 0 660 300" class="fig narrow" role="img" aria-label="{esc(title)}">
<g font-family="{FONT}">
<line class="st-line" x1="70" y1="250" x2="620" y2="250"/>
<line class="st-line" x1="70" y1="250" x2="70" y2="40"/>
<line class="st-mid" x1="{X(lo):.1f}" y1="{Y(lo):.1f}" x2="{X(hi):.1f}" y2="{Y(hi):.1f}"
      stroke-dasharray="5 4"/>
{ticks}{dots}
<text class="fi-ink48" x="345" y="292" text-anchor="middle" font-size="12">{esc(xlabel)}</text>
<text class="fi-ink48" x="18" y="145" text-anchor="middle" font-size="12"
      transform="rotate(-90 18 145)">{esc(ylabel)}</text>
</g></svg>'''


# ══════════════════════════════════════════════════ 캡션
def figcap(n, text):
    return f'<p class="figcap">그림 {n} · {text}</p>'

def tblcap(n, text):
    return f'<p class="figcap">표 {n} · {text}</p>'

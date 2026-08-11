# -*- coding: utf-8 -*-
"""
build_example.py — SKILL.md §2 파이프라인의 참조 구현.

    python examples/build_example.py paper
    python examples/build_example.py deck

dist/example_<mode>_raw.html 을 만든다. 이어서 mathbuild.js 가 자립형 HTML 로 만든다.
도해 7종·표·배지·콜아웃·메트릭·수식을 모두 한 번씩 쓰므로 회귀 확인에도 쓴다.

내용은 **가상 사례**다 — 「A사 — 인라인 계측 체계 확립과 수율 개선」.
실재하는 기업·공정·수치가 아니며, 문체 규약을 보이기 위한 예시일 뿐이다.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "plugins" / "korean-report" / "skills" / "korean-report-doc" / "assets"
sys.path.insert(0, str(ASSETS))

from figures import (  # noqa: E402
    BADGE_IMPL,
    BADGE_MEAS,
    BADGE_NONE,
    esc,
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

TITLE = "인라인 계측 체계 확립과 수율 개선"


def I(t):  # 인라인 수식
    return "⟦I⟧" + t + "⟦/I⟧"


def D(t):  # 디스플레이 수식
    return "⟦D⟧" + t + "⟦/D⟧"


def sub(tpl, *args):
    """%s 를 순서대로 치환하고 %% 를 % 로 되돌린다"""
    out, i, ai = [], 0, 0
    while True:
        j = tpl.find("%s", i)
        if j < 0:
            out.append(tpl[i:]); break
        out.append(tpl[i:j]); out.append(str(args[ai])); ai += 1; i = j + 2
    return "".join(out).replace("%%", "%")


# ── 도해 ────────────────────────────────────────────────────
TIMELINE = fig_timeline(
    marks=[("2026-08-10", "08-10", "계측 규격 초안", True),
           ("2026-08-31", "08-31", "분기 품질보고", True),
           ("2026-10-22", "10-22", "인증 시험", False)],
    start="2026-08-09", end="2026-11-06",
    bands=[("2026-09-01", "2026-09-30", "9월 계측 보강", True)],
    note="남은 82일")

GANTT = fig_gantt(
    tasks=[("검사 레시피 정비", "2026-08-01", "2026-08-25", "done"),
           ("오버레이 계측 보강", "2026-08-20", "2026-09-20", "plan"),
           ("공정 개선 전체 구간", "2026-08-01", "2026-11-01", "wbs"),
           ("인증 시험", "2026-10-01", "2026-10-25", "key")],
    start="2026-08-01", end="2026-11-01",
    markers=[("2026-08-31", "품질보고", "gate"), ("2026-10-15", "목표", "pilot")])

CARDS = fig_cards(
    items=[(1, "검사–빈닝 연결", "판정 기준 정정\n계측 900 → 590초"),
           (2, "양산 조건 벤치", "양산 구성 기준으로\n수율 재측정 체계 확립"),
           (3, "인라인 데이터 편입", "계측값을 수율 분석\n체인에 연결"),
           (4, "장비 매칭 경로", "매칭 검증 복구\n재현 감시 재개")],
    title="구조적 개선 네 가지", sub="각 항목은 측정 가능한 결과를 동반한다", cols=3)

FLOW = fig_flow(
    steps=[("검사", "결함 검출"), ("빈닝", "킬러 · 뉴슨스 판정"),
           ("수율 분석", "시그니처 추출"), ("공정 피드백", "레시피 보정")],
    highlight=1, note="강조 단계가 이번 개선의 대상이다")

NUMLINE = fig_numberline(
    points=[("중심부", 0.42), ("중간부", 0.61), ("외곽부", 1.08), ("엣지", 1.94)],
    lo=0.0, hi=2.5, marker=(1.50, "고객 규격 상한"),
    note="웨이퍼 반경 구역별 CD 편차 (nm). 값이 클수록 편차가 크다")

# 대비막대는 축을 공유한다. 단위가 섞이면 작은 값이 보이지 않으므로 초 단위로 통일한다.
COMPARE = fig_compare(
    rows=[("웨이퍼당 계측", 590, 900, "590초", "900초"),
          ("로트당 빈닝 판정", 210, 480, "210초", "480초"),
          ("재검 리포트 생성", 95, 260, "95초", "260초")],
    maxv=900, title="계측 소요 시간 개선", sub="진한 막대가 현재, 옅은 막대가 이전",
    note="세 항목 모두 낮을수록 좋다")

SCATTER = fig_scatter(
    points=[(1.0, 2.4, "×2.4"), (2.0, 3.1, "×1.6")],
    lo=0, hi=4, xlabel="모형 예측 결함 수", ylabel="실측 결함 수",
    title="예측 대 실측")

# ── 표 ──────────────────────────────────────────────────────
STATUS_TBL = tbl(
    ["항목", "상태", "값"],
    [["웨이퍼당 계측 시간", BADGE_MEAS, "590초"],
     ["오버레이 계측 레시피", BADGE_IMPL, "미적용"],
     {"c": "hl", "v": ["양산 로트 오버레이", BADGE_NONE, "—"]}],
    cls="num")

WIDE_TBL = wide(tbl(
    ["구역", "회차", "검사 다이", "킬러 비율", "계측", "CD 편차", "비고"],
    [[z, 3, 1200 + i * 40, f"{9+i}%", f"{600-i*7}초", f"{0.4+i*0.5:.2f} nm", esc("<정상>")]
     for i, z in enumerate(["중심부", "중간부", "외곽부", "엣지"])],
    cls="num"))


def build(mode: str) -> pathlib.Path:
    if mode == "paper":
        body = sub('''<header class="paper-head">
<p class="eyebrow">기술보고 · 2026-08-10 · (가상 사례)</p>
<h1>%s</h1>
<p class="subtitle">분기 품질보고 대비 현재 상태</p>
<div class="byline"><span>A사 · 홍길동</span><span>2026-08-10</span></div>
</header>

<section class="abstract"><h2>ABSTRACT</h2>
<p>검사 판정 기준을 정정하고 양산 조건 기준으로 수율 벤치를 재확립하였다. 유효 검출률은
4/7 에서 5/7 로, 웨이퍼당 계측 시간은 약 900초에서 약 590초로 개선되었다.
양산 로트의 오버레이는 아직 계측되지 않았다.</p>
<div class="legend">%s 실제로 계측된 값 · %s 레시피는 있으나 해당 로트에 미적용 ·
%s 아직 계측하지 않음</div>
<p class="srcline">본 문서는 문체 규약을 보이기 위한 가상 사례다. 실재하는 기업·공정·수치가 아니다.</p>
</section>

<section id="s0"><h2><span class="sn">0</span>배경</h2>
<p>웨이퍼 한 장에서 수백 개의 다이를 만들고, 그중 규격을 만족하는 비율이 수율이다.
공정 중간중간 선폭(CD)과 층간 정렬 정확도(오버레이)를 재고, 표면 결함을 검사한다.
검출된 결함 중 수율에 영향을 주는 것을 <b>킬러</b>, 영향이 없는 것을 <b>뉴슨스</b>라 한다.
둘을 가르는 판정을 <b>빈닝</b>이라 하며, 이 판정이 어긋나면 유효한 결함이 함께 버려진다.
이 문서는 그 계측·검사 체계를 정비한 결과를 정리한다.</p>
</section>

<section id="s1"><h2><span class="sn">1</span>일정 시사점</h2>
%s%s
<div class="metrics">
<div class="metric"><div class="mlabel">웨이퍼당 계측 시간</div><div class="mval">590초</div>
<div class="mnote">이전 약 900초</div></div>
<div class="metric gap"><div class="mlabel">양산 로트 오버레이</div><div class="mval">미계측</div>
<div class="mnote">계측 보강 후 산출</div></div>
</div>
<p class="figcap">기준 변경 고지 — 수율 수치는 양산 조건 기준이며 이전 공유분과 산출 기준이 다르다.</p>
%s%s
</section>

<section id="s2"><h2><span class="sn">2</span>구조적 개선</h2>
%s%s
%s%s
</section>

<section id="s3"><h2><span class="sn">3</span>수율 구조</h2>
<p>결함 밀도 %s 와 다이 면적 %s 로 수율 %s 를 추정한다.
결함이 웨이퍼 위에 무작위로 분포하면 포아송 모형이 성립한다.</p>
%s
<p>실제로는 결함이 특정 구역에 뭉치므로(시그니처) 클러스터링 계수 %s 를 도입한
음이항 모형(<i lang="en">negative binomial</i>)이 관측에 더 부합한다.
%s 가 작을수록 뭉침이 심하다.</p>
%s
%s%s
%s%s
<div class="finding"><p>고객 규격 상한 대비 여유는 엣지 구역에서 가장 작다.</p>
<p class="cav">엣지 구역은 계측 보강 대상이며 현재 값은 잠정치다.</p></div>
</section>

<section id="s4"><h2><span class="sn">4</span>상태와 범위</h2>
<p>이번 회차에서 확인이 필요한 것은 <mark>양산 로트의 오버레이 실측</mark> 하나다.</p>
%s%s
%s%s
<div class="note"><p>본 문서의 수치는 양산 조건 기준 벤치에서 산출되었다.
임의 조건으로 측정된 항목은 표기하지 않았다.</p></div>
<ol class="concl"><li>착수 시점을 먼저 확정한다.</li>
<li>오버레이 계측 보강 대상 구역을 결정한다.</li>
<li>양산 로트의 오버레이 산출 방법을 합의한다.</li></ol>
</section>''',
            TITLE,
            BADGE_MEAS, BADGE_IMPL, BADGE_NONE,
            TIMELINE, figcap(1, "8월~10월 마일스톤 배치"),
            GANTT, figcap(2, "준비 단계의 선행 관계"),
            CARDS, figcap(3, "구조적 개선 네 가지 (개념도)"),
            FLOW, figcap(4, "인라인 데이터의 수율 분석 체인 편입"),
            I("D_0"), I("A"), I("Y"),
            D(r"Y = \underbrace{e^{-D_0 A}}_{\text{포아송 모형}}"),
            I(r"\alpha"), I(r"\alpha"),
            D(r"Y = \left(1 + \frac{D_0 A}{\alpha}\right)^{-\alpha}"),
            NUMLINE, figcap(5, "구역별 CD 편차와 고객 규격 상한"),
            SCATTER, figcap(6, "예측 대 실측 — 항등선 대비 배수"),
            STATUS_TBL, tblcap(1, "항목별 상태 표기"),
            WIDE_TBL, tblcap(2, "구역별 계측 요약"))
    else:
        body = sub('''<section class="tile black cover"><div class="wrap">
<h1 class="hero">인라인 계측 체계 확립과<br>수율 개선</h1>
<div class="rule"></div>
<div class="meta">2026-08-10 · (가상 사례)<br>A사 · 홍길동</div>
</div></section>

<section class="tile light"><div class="wrap">
<p class="eyebrow">배경</p>
<h2><span class="sn">0</span>용어 정리</h2>
<p>검출된 결함 중 수율에 영향을 주는 것을 <b>킬러</b>, 영향이 없는 것을 <b>뉴슨스</b>라 한다.
둘을 가르는 판정이 <b>빈닝</b>이며, 이 판정이 어긋나면 유효한 결함이 함께 버려진다.</p>
%s%s
</div></section>

<section class="tile parch"><div class="wrap">
<h2><span class="sn">1</span>구조적 개선</h2>
%s%s
</div></section>

<section class="tile dark"><div class="wrap">
<p class="eyebrow">핵심</p>
<h2><span class="sn">2</span>개선 전후 대비</h2>
<p>세 항목 모두 개선되었으며 <mark>웨이퍼당 계측 시간</mark>의 감소폭이 가장 크다.</p>
%s%s
</div></section>

<section class="tile light"><div class="wrap">
<h2><span class="sn">3</span>수율 구조</h2>
<p>결함 밀도 %s 와 다이 면적 %s 가 수율 %s 를 결정한다.</p>
%s
</div></section>

<section class="tile parch"><div class="wrap">
<h2><span class="sn">4</span>상태와 결정 요청</h2>
%s%s
<ol class="concl"><li>착수 시점 확정</li><li>오버레이 계측 보강 대상 결정</li>
<li>양산 로트 오버레이 산출 방법 합의</li></ol>
</div></section>''',
            TIMELINE, figcap(1, "8월~10월 마일스톤 배치"),
            CARDS, figcap(2, "구조적 개선 네 가지 (개념도)"),
            COMPARE, figcap(3, "개선 전후 대비"),
            I("D_0"), I("A"), I("Y"),
            D(r"Y = \left(1 + \frac{D_0 A}{\alpha}\right)^{-\alpha}"),
            STATUS_TBL, tblcap(1, "항목별 상태 표기"))

    tpl = (ASSETS / f"{mode}_template.html").read_text(encoding="utf-8")
    html = tpl.replace("__BODY__", body).replace("__TITLE__", TITLE)
    out = ROOT / "dist" / f"example_{mode}_raw.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    modes = sys.argv[1:] or ["paper", "deck"]
    for m in modes:
        if m not in ("paper", "deck"):
            raise SystemExit(f"모드는 paper 또는 deck 이다 — 받은 값: {m}")
        print(build(m))

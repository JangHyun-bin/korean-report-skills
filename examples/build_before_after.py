# -*- coding: utf-8 -*-
"""
build_before_after.py — README 용 전후 대비 자산을 만든다.

    python examples/build_before_after.py

두 가지를 낸다.
  dist/ba_before.html  브라우저 기본 스타일 (스킬 없이 HTML 로 저장한 상태)
  dist/ba_after.html   korean-report-doc 로 조판한 자립형 문서

내용은 examples/before_after.md 의 「전」·「후」 원고와 같다.
가상 사례 「B사 — 고객 문의 대응 체계 개선」이며 실재하는 기업·수치가 아니다.

저장소의 다른 예시(반도체 계측)와 도메인이 다른 것은 의도한 것이다 —
규칙이 분야에 묶이지 않는다는 것을 보이기 위해서다.
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
    fig_compare,
    figcap,
    tbl,
    tblcap,
)

TITLE = "문의 대응 지연의 구조와 개선 방향"

# ── 전 — 평소 쓰는 방식. 스타일 없이 브라우저 기본으로 렌더한다. ──
BEFORE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>문의 대응이 왜 느려졌나</title></head><body>
<h1>문의 대응이 왜 느려졌나</h1>

<p>본 문서는 최근 문의 대응이 늦어진 원인을 정리하고 앞으로 뭘 할지 정하기 위한 자료입니다.
각 절은 현황과 원인, 그리고 결정이 필요한 사항을 함께 담습니다.</p>

<h2>지표가 말해주는 것</h2>
<p>1분기 대비 평균 응답 시간이 반토막 넘게 늘었습니다. 정확히는 4.2시간에서 9.1시간이 됐고,
야간 문의는 12시간이 넘어갑니다. 티켓이 계속 쌓이고 큐가 밀리면서 상담원들이 지쳐가고 있습니다.</p>

<h2>원인 분석에서 드러난 결함 세 가지</h2>
<p>조사해보니 문제가 여럿 나왔습니다. 먼저 분류 규칙이 오래돼서 신규 문의 유형의 30% 정도가
엉뚱한 팀으로 넘어가고 있었습니다. 그리고 자동응답 템플릿이 죽어 있어서 단순 문의도
사람이 다 처리했고요. 마지막으로 야간 인력 배치가 실제 문의량이랑 안 맞았습니다.</p>

<table border="1">
<tr><td>구분</td><td>1분기</td><td>3분기</td></tr>
<tr><td>평균 응답</td><td>4.2시간</td><td>9.1시간</td></tr>
<tr><td>야간 응답</td><td>6.8시간</td><td>12.4시간</td></tr>
<tr><td>오배정률</td><td>11%</td><td>30%</td></tr>
</table>

<h2>이대로 두면 위험합니다</h2>
<p>지금 안 고치면 다음 분기 갱신 시즌에 문의가 몰릴 때 완전히 무너집니다. 이탈률도 올라갈 겁니다.</p>

<h2>결정해 주세요</h2>
<p>야간 인력을 얼마나 늘릴지 정해 주십시오.</p>
</body></html>
"""

# ── 후 — 규약 + 조판 ────────────────────────────────────────
COMPARE = fig_compare(
    rows=[("평균 응답", 9.1, 4.2, "9.1h", "4.2h"),
          ("야간 응답", 12.4, 6.8, "12.4h", "6.8h")],
    maxv=13, title="분기별 응답 시간", sub="진한 막대가 3분기, 옅은 막대가 1분기",
    note="두 항목 모두 낮을수록 좋다")

METRIC_TBL = tbl(
    ["구분", "1분기", "3분기", "상태"],
    [["평균 응답", "4.2시간", "9.1시간", BADGE_MEAS],
     ["야간 응답", "6.8시간", "12.4시간", BADGE_MEAS],
     {"c": "hl", "v": ["오배정률", "11%", "30%", BADGE_MEAS]},
     ["자동 처리율", "—", "0%", BADGE_IMPL],
     ["증원 소요", "—", "3명(안)", BADGE_NONE]],
    cls="num")

RISK_TBL = tbl(
    ["리스크", "대응"],
    [["갱신 시즌 문의 집중", "분류 규칙 정비를 갱신 2주 전까지 완료"],
     ["자동응답 오답변", "초기 4주간 상담원 검수 병행"]])

AFTER_BODY = f"""<header class="paper-head">
<p class="eyebrow">진행현황 · 3분기 · (가상 사례)</p>
<h1>{TITLE}</h1>
<p class="subtitle">대응 실적과 개선안</p>
<div class="byline"><span>B사 · 홍길동</span><span>3분기</span></div>
</header>

<section class="abstract"><h2>ABSTRACT</h2>
<p>평균 응답 시간이 4.2시간에서 9.1시간으로 증가하였다. 분류 규칙 미비로 인한 오배정,
자동응답 템플릿 비활성, 야간 인력 배치 불일치가 지배적 원인이다.
세 항목의 개선안과 산정 근거를 제시한다.</p>
<div class="legend">{BADGE_MEAS} 실제로 측정된 값 · {BADGE_IMPL} 수단은 있으나 미사용 ·
{BADGE_NONE} 아직 측정하지 않음</div>
<p class="srcline">본 문서는 문체·조판 규약을 보이기 위한 가상 사례다. 실재하는 기업·수치가 아니다.</p>
</section>

<section id="s1"><h2><span class="sn">1</span>대응 시간 지표</h2>
<p>평균 응답 시간은 4.2시간에서 9.1시간으로 증가하였다. 야간 접수분은 12시간을 초과한다.
미처리 티켓이 누적되어 큐에 적체가 발생하고 있다.</p>
{COMPARE}{figcap(1, "분기별 응답 시간 대비")}
{METRIC_TBL}{tblcap(1, "지표별 상태 표기")}
</section>

<section id="s2"><h2><span class="sn">2</span>구조적 개선 — 분류 체계 정비와 자동응답 복구</h2>

<h3>① 분류 규칙 정비 — 오배정 감소</h3>
<div class="finding"><p>결과 · 오배정률 30% → 목표 10% 이하</p>
<p class="cav">목표치는 미측정이며 정비 후 재산출한다.</p></div>
<p>신규 문의 유형이 분류 규칙에 등재되지 않아 담당 팀이 아닌 곳으로 이관되고 있었다.</p>

<h3>② 자동응답 템플릿 복구 — 단순 문의 자동 처리</h3>
<div class="finding"><p>결과 · 단순 문의 자동 처리율 0% → 목표 40%</p></div>
<p>템플릿이 비활성 상태였으므로 단순 문의도 상담원이 직접 처리하였다.</p>

<h3>③ 야간 인력 배치 정합 — 접수량 기준 재산정</h3>
<div class="finding"><p>결과 · 야간 응답 12시간 초과 → 목표 6시간 이내</p></div>
<p>인력 배치가 시간대별 접수량을 참조하지 않는 구조였다.</p>
</section>

<section id="s3"><h2><span class="sn">3</span>리스크와 대응</h2>
{RISK_TBL}{tblcap(2, "리스크별 대응 방안")}
<div class="note"><p>대응을 기재할 수 없는 항목은 이 표에 두지 않았다.
리스크만 나열하면 문제 제기가 되고, 대응을 병기하면 관리 중이라는 서술이 된다.</p></div>
</section>

<section id="s4"><h2><span class="sn">4</span>야간 인력 증원 (안)</h2>
<p>시간대별 접수량을 기준으로 3명 증원을 산정하였다. 산정 근거는 부록 A에 기재하였다.
여건에 따라 조정을 요청한다.</p>
<ol class="concl"><li>분류 규칙 정비 착수 시점을 확정한다.</li>
<li>자동응답 적용 범위를 합의한다.</li>
<li>증원 규모를 조정하거나 확정한다.</li></ol>
</section>"""


def main() -> None:
    out = ROOT / "dist"
    out.mkdir(parents=True, exist_ok=True)

    (out / "ba_before.html").write_text(BEFORE, encoding="utf-8")

    tpl = (ASSETS / "paper_template.html").read_text(encoding="utf-8")
    (out / "ba_after_raw.html").write_text(
        tpl.replace("__BODY__", AFTER_BODY).replace("__TITLE__", TITLE), encoding="utf-8")

    print(out / "ba_before.html")
    print(out / "ba_after_raw.html")
    print("→ mathbuild.js 로 ba_after_raw.html 을 처리한다")


if __name__ == "__main__":
    main()

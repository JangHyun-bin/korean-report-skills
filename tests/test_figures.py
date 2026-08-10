# -*- coding: utf-8 -*-
"""
figures.py 의 기하와 계약.

여기 있는 검사는 대부분 실제로 났던 버그에서 나왔다.
좌표계 역전(fig_cards), 음수 폭(fig_compare), 0 나눗셈(기간 0), id 충돌(fig_flow).
"""
import re
import xml.etree.ElementTree as ET

import figures as F  # assets/ 경로는 conftest.py 가 sys.path 에 넣는다
import pytest


def parse(svg: str) -> ET.Element:
    """SVG 가 well-formed 인지 확인하며 파싱한다."""
    return ET.fromstring(svg)


def rects(svg: str):
    return [e for e in parse(svg).iter() if e.tag.endswith("rect")]


# ── 공통 계약 ───────────────────────────────────────────────
def samples():
    return {
        "timeline": F.fig_timeline([("2026-08-10", "a", "b", True)], "2026-08-01", "2026-09-01"),
        "cards": F.fig_cards([(1, "t", "d")]),
        "flow": F.fig_flow([("a", "1"), ("b", "2")]),
        "numberline": F.fig_numberline([("p", 1.0)], 0, 3),
        "compare": F.fig_compare([("r", 3, 8, "3", "8")], 10),
        "scatter": F.fig_scatter([(1, 2, "l")], 0, 4),
    }


@pytest.mark.parametrize("name,svg", list(samples().items()))
def test_svg_is_wellformed(name, svg):
    parse(svg)


@pytest.mark.parametrize("name,svg", list(samples().items()))
def test_no_literal_hex_colors_in_output(name, svg):
    """색은 클래스로 나가야 한다. hex 를 박으면 다크 타일에서 글자가 사라진다."""
    hexes = re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,8})"', svg)
    assert not hexes, f"{name} 이 리터럴 색을 방출한다: {set(hexes)} — fi-* / st-* 클래스를 쓴다"


@pytest.mark.parametrize("name,svg", list(samples().items()))
def test_font_family_is_declared(name, svg):
    """SVG 는 폰트를 상속하지 않는다."""
    assert 'font-family="Pretendard"' in svg


@pytest.mark.parametrize("name,svg", list(samples().items()))
def test_no_negative_geometry(name, svg):
    for r in rects(svg):
        for attr in ("width", "height"):
            v = float(r.get(attr, 0))
            assert v >= 0, f"{name} 의 rect {attr} 가 음수({v}) — SVG 는 이 요소를 렌더하지 않는다"


# ── fig_cards — 좌표계 ──────────────────────────────────────
def card_rows(svg: str, w=280.0):
    """카드 본체 rect 만 골라 (y, x) 로 돌려준다."""
    return [(float(r.get("y")), float(r.get("x")))
            for r in rects(svg) if float(r.get("width", 0)) == w]


def test_cards_rows_stack_downward():
    svg = F.fig_cards([(i, f"t{i}", "d") for i in range(1, 7)], cols=3)
    ys = [y for y, _ in card_rows(svg)]
    assert ys[0] < ys[3], "두 번째 행이 첫 행보다 위에 있다 — y-up 좌표를 뒤집지 않았다"
    assert len(set(ys[:3])) == 1 and len(set(ys[3:])) == 1, "같은 행의 카드 y 가 다르다"


def test_cards_first_row_precedes_in_reading_order():
    svg = F.fig_cards([(i, f"t{i}", "d") for i in range(1, 5)], cols=3)
    coords = card_rows(svg)
    assert coords == sorted(coords), "카드가 좌→우, 위→아래 순서로 놓이지 않았다"


def test_cards_fit_inside_viewbox():
    for n, cols in ((1, 3), (4, 3), (7, 3), (5, 2), (3, 1)):
        svg = F.fig_cards([(i, f"t{i}", "x\ny") for i in range(1, n + 1)], cols=cols,
                          title="T", sub="S")
        vb = [float(v) for v in parse(svg).get("viewBox").split()]
        for y, x in card_rows(svg):
            assert vb[1] <= y and y + 132 <= vb[1] + vb[3], f"n={n} cols={cols} 카드가 세로로 삐져나온다"
            assert vb[0] <= x and x + 280 <= vb[0] + vb[2], f"n={n} cols={cols} 카드가 가로로 삐져나온다"


def test_cards_header_is_at_top_of_card():
    svg = F.fig_cards([(1, "t", "d")])
    y0 = card_rows(svg)[0][0]
    path = [e for e in parse(svg).iter() if e.tag.endswith("path")][0]
    start_y = float(re.match(r"M[\d.]+,([\d.]+)", path.get("d")).group(1))
    assert abs(start_y - (y0 + 30)) < 0.01, "헤더 바가 카드 위쪽에 있지 않다"


def test_cards_rejects_bad_cols():
    with pytest.raises(ValueError):
        F.fig_cards([(1, "t", "d")], cols=0)


# ── fig_compare — 대소 무관 ────────────────────────────────
@pytest.mark.parametrize("a,b", [(3, 8), (8, 3), (5, 5)])
def test_compare_difference_box_survives_either_ordering(a, b):
    svg = F.fig_compare([("r", a, b, str(a), str(b))], 10)
    boxes = [r for r in rects(svg) if r.get("height") == "39"]
    assert len(boxes) == 1
    assert float(boxes[0].get("width")) >= 0, "차이 구간 폭이 음수다 — 렌더되지 않는다"


def test_compare_rejects_nonpositive_maxv():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            F.fig_compare([("r", 1, 2, "1", "2")], bad)


# ── 경계조건 ────────────────────────────────────────────────
@pytest.mark.parametrize("fn", [F.fig_timeline, F.fig_gantt])
def test_zero_length_period_raises(fn):
    with pytest.raises(ValueError):
        if fn is F.fig_timeline:
            fn([("2026-08-01", "a", "b", True)], "2026-08-01", "2026-08-01")
        else:
            fn([("t", "2026-08-01", "2026-08-02", "done")], "2026-08-01", "2026-08-01")


@pytest.mark.parametrize("fn", [F.fig_numberline, F.fig_scatter])
def test_inverted_axis_raises(fn):
    with pytest.raises(ValueError):
        if fn is F.fig_numberline:
            fn([("p", 1)], 3, 1)
        else:
            fn([(1, 1, "l")], 3, 1)


def test_gantt_rejects_unknown_kind():
    with pytest.raises(ValueError):
        F.fig_gantt([("t", "2026-08-01", "2026-08-10", "bogus")], "2026-08-01", "2026-09-01")
    with pytest.raises(ValueError):
        F.fig_gantt([("t", "2026-08-01", "2026-08-10", "done")], "2026-08-01", "2026-09-01",
                    markers=[("2026-08-05", "m", "bogus")])


def test_gantt_bar_style_carries_position_only():
    """색은 CSS 가 정한다. 인라인 style 에 색이 들어가면 다크 타일에서 못 바꾼다."""
    html = F.fig_gantt([("t", "2026-08-01", "2026-08-20", "done")], "2026-08-01", "2026-11-01")
    for style in re.findall(r'class="gbar[^"]*"\s+style="([^"]*)"', html):
        assert "background" not in style and "border" not in style, \
            f"gbar 인라인 style 에 색이 있다: {style}"


# ── id 충돌 ─────────────────────────────────────────────────
def test_flow_marker_ids_are_unique_across_calls():
    a = F.fig_flow([("a", "1"), ("b", "2")])
    b = F.fig_flow([("c", "3"), ("d", "4")])
    ids = re.findall(r'<marker id="([^"]+)"', a + b)
    assert len(ids) == len(set(ids)), f"한 문서에 도해가 둘이면 marker id 가 겹친다: {ids}"


# ── 이스케이프 ──────────────────────────────────────────────
def test_esc_escapes_markup():
    assert F.esc('<a href="x">&') == "&lt;a href=&quot;x&quot;&gt;&amp;"


def test_title_is_escaped_in_aria_label():
    svg = F.fig_cards([(1, "t", "d")], title='제목 "인용" & <꺾쇠>')
    assert 'aria-label="제목 &quot;인용&quot; &amp; &lt;꺾쇠&gt;"' in svg
    parse(svg)


def test_tbl_keeps_cell_html_raw():
    """배지·수식 마커를 셀에 직접 넣는 것이 정상 용법이다."""
    assert F.BADGE_MEAS in F.tbl(["h"], [[F.BADGE_MEAS]])


def test_tbl_highlight_row_and_class():
    html = F.tbl(["h"], [["a"], {"c": "hl", "v": ["b"]}], cls="num")
    assert '<table class="num">' in html
    assert '<tr class="hl">' in html

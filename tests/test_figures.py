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
from conftest import ROOT


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


# ── embed_svg — 외부 도구가 생성한 SVG ──────────────────────
# 두 fixture 는 실제 도구 출력을 손대지 않고 저장한 것이다.
#   tikz_pdftocairo.svg — TikZ(standalone) → tectonic → pdftocairo 26.04 -svg
#   matplotlib.svg      — matplotlib 3.10 savefig(format=svg), Date·Creator metadata 제거
# pdftocairo 는 출력마다 같은 id(glyph-0-0 · clip-0)를 쓴다. 한 문서에 둘을 넣으면
# 뒤 그림이 앞 그림의 글리프를 참조한다.
SVG_FIXTURES = ROOT / "tests" / "fixtures" / "svg"
EXTERNAL = {p.name: p.read_text(encoding="utf-8") for p in sorted(SVG_FIXTURES.glob("*.svg"))}
XLINK = "{http://www.w3.org/1999/xlink}href"
URL_REF = re.compile(r"url\(\s*['\"]?#([^'\")\s]+)")


def ids_and_refs(svg: str):
    """(id 집합, 참조 대상 목록). 참조는 href · xlink:href · 속성과 <style> 안의 url(#…)."""
    root = parse(svg)
    ids, refs = set(), []
    for e in root.iter():
        for k, v in e.attrib.items():
            if k == "id":
                assert v not in ids, f"id 중복: {v}"
                ids.add(v)
            elif k in ("href", XLINK) and v.startswith("#"):
                refs.append(v[1:])
            refs.extend(URL_REF.findall(v))
        if e.tag.endswith("style") and e.text:
            refs.extend(URL_REF.findall(e.text))
    return ids, refs


def test_svg_fixtures_are_present():
    assert set(EXTERNAL) == {"tikz_pdftocairo.svg", "matplotlib.svg"}, sorted(EXTERNAL)


@pytest.mark.parametrize("name", sorted(EXTERNAL))
def test_embed_svg_two_copies_have_disjoint_ids(name):
    src = EXTERNAL[name]
    a = F.embed_svg(src, "fa", "a")
    b = F.embed_svg(src, "fb", "b")
    ids_a, refs_a = ids_and_refs(a)
    ids_b, refs_b = ids_and_refs(b)
    src_ids, src_refs = ids_and_refs(src)
    assert src_refs, f"{name} 에 내부 참조가 없다 — fixture 가 검사 대상을 담고 있지 않다"
    assert len(ids_a) == len(src_ids), "id 가 사라지거나 늘었다"
    assert not ids_a & ids_b, f"두 사본의 id 가 겹친다: {sorted(ids_a & ids_b)[:5]}"
    assert len(refs_a) == len(src_refs), "참조가 사라지거나 늘었다"
    for ids, refs, label in ((ids_a, refs_a, "fa"), (ids_b, refs_b, "fb")):
        dangling = sorted(set(refs) - ids)
        assert not dangling, f"{label} 사본의 참조가 자기 SVG 밖을 가리킨다: {dangling[:5]}"


def test_embed_svg_source_ids_really_collide():
    """대조군 — 접두어 없이 두 개를 넣으면 id 가 실제로 겹친다. 위 검사가 성립하는 전제다."""
    src_ids, _ = ids_and_refs(EXTERNAL["tikz_pdftocairo.svg"])
    assert {"glyph-0-0", "clip-0"} <= src_ids


@pytest.mark.parametrize("name", sorted(EXTERNAL))
def test_embed_svg_root_takes_css_sizing_and_accessibility(name):
    src = EXTERNAL[name]
    out = F.embed_svg(src, "fa", '제목 "인용" & <꺾쇠>')
    assert out.startswith("<svg"), "XML 선언 · DOCTYPE 이 남았다"
    assert "<?xml" not in out and "<!DOCTYPE" not in out
    root = parse(out)
    assert "width" not in root.attrib and "height" not in root.attrib, \
        "루트 width · height 가 남으면 .fig{width:100%} 가 걸리지 않는다"
    src_vb = re.search(r'<svg\b[^>]*\bviewBox="([^"]+)"', src).group(1)
    assert root.get("viewBox") == src_vb
    assert root.get("class") == "fig" and root.get("role") == "img"
    assert root.get("aria-label") == '제목 "인용" & <꺾쇠>'
    assert root.get("data-embed") == "fa"


def test_embed_svg_rewrites_url_references_in_style_attributes():
    src = ('<svg viewBox="0 0 10 10"><defs><clipPath id="c"><rect width="1" height="1"/></clipPath>'
           '<linearGradient id="g"/></defs>'
           '<g style="clip-path:url(#c);fill:url( \'#g\' )"/><g clip-path="url(#c)"/></svg>')
    out = F.embed_svg(src, "p", "x")
    assert out.count("url(#p-c)") == 2 and "url(#p-g)" in out
    assert not re.search(r"url\(\s*'?#[cg]\b", out), out


def test_embed_svg_scopes_style_rules_to_itself():
    """matplotlib 의 `*{stroke-linecap:butt}` 가 문서의 다른 도해까지 바꾸지 않게 한다."""
    out = F.embed_svg(EXTERNAL["matplotlib.svg"], "mpl", "x")
    css = re.search(r"<style[^>]*>(.*?)</style>", out, re.S).group(1)
    for rule in re.findall(r"([^{}]+)\{", css):
        for sel in rule.split(","):
            assert sel.strip().startswith('svg[data-embed="mpl"] '), f"범위가 한정되지 않은 선택자: {sel}"


def test_embed_svg_renames_id_selectors_inside_style():
    src = '<svg viewBox="0 0 1 1"><style>#a, .k{fill:#fff}</style><g id="a"/></svg>'
    out = F.embed_svg(src, "p", "x")
    assert 'svg[data-embed="p"] #p-a, svg[data-embed="p"] .k{fill:#fff}' in out


def test_embed_svg_strips_leading_comments():
    src = '﻿<?xml version="1.0"?>\n<!-- Created with a tool -->\n<svg viewBox="0 0 1 1"><g/></svg>\n'
    assert F.embed_svg(src, "p", "x").startswith("<svg ")


@pytest.mark.parametrize("src,why", [
    ('<svg width="10" height="10"><g/></svg>', "viewBox 없음"),
    ('<svg viewBox="0 0 0 10"><g/></svg>', "viewBox 폭 0"),
    ('<svg viewBox="0 0 a b"><g/></svg>', "viewBox 숫자 아님"),
    ('<html><svg viewBox="0 0 1 1"/></html>', "루트가 svg 아님"),
    ("", "빈 입력"),
    ('<svg viewBox="0 0 1 1"><g/>', "잘린 SVG"),
    ('<svg viewBox="0 0 1 1"><use href="#nope"/></svg>', "없는 id 참조"),
    ('<svg viewBox="0 0 1 1"><g clip-path="url(#nope)"/></svg>', "없는 url() 참조"),
    ('<svg viewBox="0 0 1 1"><image href="plot.png"/></svg>', "외부 파일 참조"),
    ('<svg viewBox="0 0 1 1"><g id="a"/><g id="a"/></svg>', "id 중복"),
    ('<svg viewBox="0 0 1 1"><style>@media print{g{fill:red}}</style></svg>', "at-rule"),
])
def test_embed_svg_rejects_bad_input(src, why):
    with pytest.raises(ValueError):
        F.embed_svg(src, "p", "x")


@pytest.mark.parametrize("prefix", ["", "1a", "a b", 'a"b', None])
def test_embed_svg_rejects_bad_prefix(prefix):
    with pytest.raises(ValueError):
        F.embed_svg('<svg viewBox="0 0 1 1"><g/></svg>', prefix, "x")


def test_embed_svg_requires_a_label():
    with pytest.raises(ValueError):
        F.embed_svg('<svg viewBox="0 0 1 1"><g/></svg>', "p", "  ")


def test_embed_svg_keeps_data_uris_and_hyperlinks():
    src = ('<svg viewBox="0 0 1 1"><image href="data:image/png;base64,AAAA"/>'
           '<a href="https://example.com"><g/></a></svg>')
    out = F.embed_svg(src, "p", "x")
    assert 'href="data:image/png;base64,AAAA"' in out and 'href="https://example.com"' in out

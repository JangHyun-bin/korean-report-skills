# -*- coding: utf-8 -*-
"""
embed_svg 로 삽입한 외부 SVG 가 실제 문서 안에서도 서로 간섭하지 않는지 브라우저로 확인한다.

단위 검사는 문자열을 본다. 여기서는 빌드한 문서를 렌더해 문서 전체의 id 가 고유한지,
<use> 가 자기 그림 안의 글리프를 가리키는지, matplotlib 의 <style> 이 본문의 다른 도해에
번지지 않는지를 본다.
"""
import shutil
import subprocess
import sys

import figures as F
import pytest
from conftest import ASSETS, ROOT
from test_build_e2e import have_chromium

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not (shutil.which("node") and have_chromium()), reason="node · chromium 이 필요하다"),
]

FIX = ROOT / "tests" / "fixtures" / "svg"


def build(tmp_path, mode, body):
    tpl = (ASSETS / f"{mode}_template.html").read_text(encoding="utf-8")
    raw = tmp_path / f"{mode}_raw.html"
    raw.write_text(tpl.replace("__BODY__", body).replace("__TITLE__", "embed"), encoding="utf-8")
    out = tmp_path / f"{mode}.html"
    subprocess.run(["node", str(ASSETS / "mathbuild.js"), str(raw), str(out), "--assets", str(ASSETS)],
                   cwd=ROOT, check=True, capture_output=True)
    return out


def qa(out):
    return subprocess.run([sys.executable, str(ASSETS / "qa.py"), str(out)], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8")


def test_embedded_figures_do_not_interfere(tmp_path):
    tikz = (FIX / "tikz_pdftocairo.svg").read_text(encoding="utf-8")
    mpl = (FIX / "matplotlib.svg").read_text(encoding="utf-8")
    body = "<section><h2>외부 그림</h2>" + "".join([
        F.fig_flow([("계측", "a"), ("판정", "b")], title="native"), F.figcap(1, "흐름 (개념도)"),
        F.embed_svg(tikz, "tz1", "첫 그림"), F.figcap(2, "첫 그림"),
        F.embed_svg(tikz, "tz2", "둘째 그림"), F.figcap(3, "둘째 그림"),
        F.embed_svg(mpl, "mp1", "막대"), F.figcap(4, "막대"),
    ]) + "</section>"
    out = build(tmp_path, "paper", body)
    r = qa(out)
    assert r.returncode == 0, r.stdout + r.stderr

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(out.resolve().as_uri())
        got = pg.evaluate("""() => {
          const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
          const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
          const foreign = [];
          document.querySelectorAll('svg[data-embed] use').forEach(u => {
            const ref = (u.getAttribute('href') || u.getAttribute('xlink:href') || '').slice(1);
            const t = document.getElementById(ref);
            if (!t || t.closest('svg[data-embed]') !== u.closest('svg[data-embed]')) foreign.push(ref);
          });
          const native = document.querySelector('svg.fig:not([data-embed]) rect');
          return { dup, foreign, uses: document.querySelectorAll('svg[data-embed] use').length,
                   join: getComputedStyle(native).strokeLinejoin };
        }""")
        b.close()
    assert got["uses"] > 0, "삽입한 그림에 <use> 가 없다 — 검사가 아무것도 보지 않았다"
    assert not got["dup"], f"문서 안 id 가 겹친다: {got['dup'][:5]}"
    assert not got["foreign"], f"<use> 가 다른 그림의 글리프를 가리킨다: {got['foreign'][:5]}"
    assert got["join"] == "miter", f"matplotlib <style> 이 본문 도해에 번졌다 — stroke-linejoin {got['join']}"


def test_qa_rejects_an_embedded_figure_on_a_dark_tile(tmp_path):
    tikz = (FIX / "tikz_pdftocairo.svg").read_text(encoding="utf-8")
    body = ('<section class="tile dark"><div class="wrap"><h2>어두운 타일</h2>'
            + F.embed_svg(tikz, "tz", "다크 위 그림") + F.figcap(1, "x") + "</div></section>")
    r = qa(build(tmp_path, "deck", body))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "다크 surface 위의 외부 SVG" in r.stdout

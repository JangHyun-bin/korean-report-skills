# -*- coding: utf-8 -*-
"""paper PDF 는 쪽 하단에 제목과 쪽번호를 인쇄한다. deck 은 full-bleed 라 인쇄하지 않는다."""
import re
import shutil
import subprocess
import sys

import pytest
from conftest import ASSETS, ROOT
from test_build_e2e import have_chromium

qa = pytest.importorskip("qa")


def test_footer_carries_page_numbers_and_escaped_title():
    html = qa.footer_template("A&B <보고서>")
    assert 'class="pageNumber"' in html and 'class="totalPages"' in html
    assert "A&amp;B &lt;보고서&gt;" in html


@pytest.mark.e2e
@pytest.mark.skipif(not (shutil.which("pdftotext") and shutil.which("node") and have_chromium()),
                    reason="pdftotext · node · chromium 이 필요하다")
def test_paper_pdf_prints_the_footer(tmp_path):
    tpl = (ASSETS / "paper_template.html").read_text(encoding="utf-8")
    body = "<section><h2>본문</h2>" + "<p>쪽을 넘길 만큼 긴 문단이다.</p>\n" * 120 + "</section>"
    raw = tmp_path / "raw.html"
    raw.write_text(tpl.replace("__BODY__", body).replace("__TITLE__", "Footer check"), encoding="utf-8")
    out = tmp_path / "doc.html"
    subprocess.run(["node", str(ASSETS / "mathbuild.js"), str(raw), str(out), "--assets", str(ASSETS)],
                   cwd=ROOT, check=True, capture_output=True)
    subprocess.run([sys.executable, str(ASSETS / "qa.py"), str(out), "--pdf"], cwd=ROOT, check=True,
                   capture_output=True)
    text = subprocess.run(["pdftotext", str(out.with_suffix(".pdf")), "-"], capture_output=True,
                          text=True, check=True).stdout
    assert "Footer check" in text
    # "쪽번호 / 총쪽수"는 짧고 고립된 글자 뭉치라 pdftotext가 슬래시 둘레 공백을
    # 안정적으로 복원하지 못한다(qlmanage 캡처로는 공백이 뚜렷이 보인다) — 슬래시
    # 둘레 공백은 있어도 없어도 통과시키고, 숫자 자체가 찍혔는지만 본다.
    assert re.search(r"1\s*/\s*\d", text), text
    assert re.search(r"2\s*/\s*\d", text), text


@pytest.mark.e2e
@pytest.mark.skipif(not (shutil.which("node") and have_chromium()), reason="node · chromium 이 필요하다")
def test_deck_pdf_keeps_print_css_after_measuring_tiles(tmp_path):
    """
    qa.py 의 run() 은 타일 높이를 재려고 emulate_media(media="print")를 걸었다가
    화면 검사를 위해 media="screen"으로 되돌린다. 그 뒤에 호출하는 pg.pdf()는
    screen emulation 이 걸려 있으면 print CSS 를 무시하고 화면 CSS 로 렌더한다 —
    그 결과 deck PDF 의 쪽 수가 타일 수와 어긋나고 다크 타일도 되돌아가지 않는다.
    media="null"로 되돌려야 emulation 이 풀리고 PDF 가 다시 print CSS 를 쓴다.
    """
    tpl = (ASSETS / "deck_template.html").read_text(encoding="utf-8")
    body = (
        '<section class="tile light"><div class="wrap"><h2>하나</h2><p>본문</p></div></section>'
        '<section class="tile dark"><div class="wrap"><h2>둘</h2><p>본문</p></div></section>'
    )
    raw = tmp_path / "raw.html"
    raw.write_text(tpl.replace("__BODY__", body).replace("__TITLE__", "Deck check"), encoding="utf-8")
    out = tmp_path / "deck.html"
    subprocess.run(["node", str(ASSETS / "mathbuild.js"), str(raw), str(out), "--assets", str(ASSETS)],
                   cwd=ROOT, check=True, capture_output=True)
    subprocess.run([sys.executable, str(ASSETS / "qa.py"), str(out), "--pdf"], cwd=ROOT, check=True,
                   capture_output=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(out.resolve().as_uri())
        tiles = len(pg.query_selector_all("section.tile"))
        b.close()
    assert tiles == 3, f"template 이 EOD 타일을 붙였는지 확인한다 (센 값: {tiles})"

    pdf_bytes = out.with_suffix(".pdf").read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf_bytes))
    assert pages == tiles, f"타일 {tiles}개인데 {pages}쪽이다 — deck PDF 가 print CSS 를 잃었다"

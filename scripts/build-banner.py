# -*- coding: utf-8 -*-
"""
build-banner.py — README 배너를 실제 문서에서 합성한다.

    python scripts/build-banner.py

문서 세 조각을 캡처해 겹친 뒤 라이트·다크 두 벌을 PNG 로 찍는다.
손으로 갱신하는 스크린샷은 반드시 문서와 어긋나므로 CI 가 매번 재생성한다.

선행 조건 — dist/example_paper.html 과 dist/example_deck.html 이 있어야 한다.
    python examples/build_example.py
    node <assets>/mathbuild.js dist/example_<mode>_raw.html dist/example_<mode>.html --assets <assets>
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PARTS = DIST / "banner-parts"
OUT = ROOT / "docs" / "assets"

W, H, SCALE = 1120, 300, 2

THEME = {
    "light": {"bg": "linear-gradient(180deg,#f7f8fa,#eef1f5)",
              "ring": "rgba(0,0,0,.09)", "shadow": "0 8px 24px -12px rgba(0,0,0,.28)"},
    "dark":  {"bg": "linear-gradient(180deg,#161b22,#0d1117)",
              "ring": "rgba(255,255,255,.12)", "shadow": "0 10px 30px -14px rgba(0,0,0,.7)"},
}

LAYOUT = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{w}px;height:{h}px;overflow:hidden;background:{bg}}}
.s{{position:absolute;border-radius:7px;overflow:hidden;background:#fff;
   box-shadow:0 0 0 1px {ring}, {shadow}}}
.s.dk{{background:#272729}}
.s img{{display:block;width:100%}}
.s1{{width:290px;left:56px;top:30px}}
.s2{{width:410px;left:320px;top:84px;z-index:2}}
.s3{{width:280px;left:712px;top:38px}}
</style></head><body>
<div class="s s1"><img src="{top}"></div>
<div class="s s2 dk"><img src="{dark}"></div>
<div class="s s3"><img src="{body}"></div>
</body></html>"""


def capture_parts() -> dict:
    """예시 문서에서 서로 다른 세 조각을 캡처한다."""
    PARTS.mkdir(parents=True, exist_ok=True)
    paper = DIST / "example_paper.html"
    deck = DIST / "example_deck.html"
    for f in (paper, deck):
        if not f.exists():
            raise SystemExit(f"{f} 가 없다. examples/build_example.py 를 먼저 실행한다.")

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 900, "height": 760}, device_scale_factor=2)
        pg.goto(paper.resolve().as_uri()); pg.wait_for_timeout(2000)
        pg.screenshot(path=str(PARTS / "top.png"),
                      clip={"x": 0, "y": 0, "width": 900, "height": 760})
        y = pg.evaluate('document.querySelector("#s1").getBoundingClientRect().top + window.scrollY')
        pg.screenshot(path=str(PARTS / "body.png"), full_page=True,
                      clip={"x": 0, "y": y - 20, "width": 900, "height": 720})
        pg.close()

        pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=2)
        pg.goto(deck.resolve().as_uri()); pg.wait_for_timeout(2000)
        pg.query_selector_all("section.tile")[3].screenshot(path=str(PARTS / "dark.png"))
        pg.close()
        b.close()
    return {k: (PARTS / f"{k}.png").resolve().as_uri() for k in ("top", "dark", "body")}


def build(theme: str, parts: dict) -> pathlib.Path:
    """한 테마의 배너를 합성해 PNG 로 기록하고 그 경로를 돌려준다."""
    html = LAYOUT.format(w=W, h=H, **THEME[theme], **parts)
    page = DIST / f"banner-{theme}.html"
    page.write_text(html, encoding="utf-8")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"banner-{theme}.png"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=SCALE)
        pg.goto(page.resolve().as_uri()); pg.wait_for_timeout(900)
        pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": W, "height": H})
        b.close()
    return out


def main() -> None:
    parts = capture_parts()
    for theme in ("light", "dark"):
        print(build(theme, parts))


if __name__ == "__main__":
    main()

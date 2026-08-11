# -*- coding: utf-8 -*-
"""
build-shots.py — README 가 싣는 이미지를 전부 실제 문서에서 찍는다.

    python scripts/build-shots.py

배너 두 벌(문서 세 조각을 겹쳐 합성)과 전후 대비 세 장을 만든다.
**손으로 갱신하는 스크린샷은 반드시 문서와 어긋나므로** CI 가 매번 재생성해
커밋된 것과 바이트로 대조한다. 이 저장소에 손으로 찍어 넣는 이미지는 없다.

선행 조건 — dist/ 에 아래 네 파일이 있어야 한다.
    python examples/build_example.py
    python examples/build_before_after.py
    node <assets>/mathbuild.js dist/<name>_raw.html dist/<name>.html --assets <assets>
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

# 전후 대비 — README 가 표로 반씩 나눠 싣는 폭에 맞춘다.
BA_W = 880
BA_TOP_H = 669     # 표제부터 초록까지. 「전」과 같은 구간을 잘라야 대비가 성립한다
BA_BODY_H = 870    # 도해와 상태 배지가 한 화면에 들어가는 본문 구간

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


def capture_before_after() -> list[pathlib.Path]:
    """
    README 의 전후 대비 세 장. 「전」과 「후」는 같은 구간을 잘라야 대비가 성립한다.

    `ba_before.html` 은 브라우저 기본 스타일이라 글꼴이 내장되어 있지 않다.
    그것이 보이려는 상태 자체이므로 맞추지 않는다.
    """
    before, after = DIST / "ba_before.html", DIST / "ba_after.html"
    for f in (before, after):
        if not f.exists():
            raise SystemExit(f"{f} 가 없다. examples/build_before_after.py 를 먼저 실행한다.")

    OUT.mkdir(parents=True, exist_ok=True)
    top = {"x": 0, "y": 0, "width": BA_W, "height": BA_TOP_H}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": BA_W, "height": BA_TOP_H}, device_scale_factor=SCALE)

        pg.goto(before.resolve().as_uri()); pg.wait_for_timeout(1200)
        pg.screenshot(path=str(OUT / "ba_before.png"), clip=top)

        pg.goto(after.resolve().as_uri()); pg.wait_for_timeout(2000)
        pg.screenshot(path=str(OUT / "ba_after.png"), clip=top)

        # 본문 — 초록 아래 첫 절. 위로 조금 올려 잡아 초록의 마감 괘선이 함께 들어간다.
        y = pg.evaluate('document.querySelector("#s1").getBoundingClientRect().top + window.scrollY')
        pg.screenshot(path=str(OUT / "ba_after_body.png"), full_page=True,
                      clip={"x": 0, "y": y - 24, "width": BA_W, "height": BA_BODY_H})
        b.close()
    return [OUT / f"ba_{n}.png" for n in ("before", "after", "after_body")]


def main() -> None:
    parts = capture_parts()
    for theme in ("light", "dark"):
        print(build(theme, parts))
    for f in capture_before_after():
        print(f)


if __name__ == "__main__":
    main()

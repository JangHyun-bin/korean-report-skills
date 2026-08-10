# -*- coding: utf-8 -*-
"""
qa.py — 렌더링해서 확인한다. 소스를 믿지 않는다.

    python scripts/qa.py dist/example_paper.html [--pdf dist/example_paper.pdf] [--shot dir]

SKILL.md §4 체크리스트의 기계 검사 부분을 수행한다.
사람이 봐야 하는 항목(다크 타일 반전, 절반 이상 빈 페이지)은 --shot 으로 이미지를 남긴다.
검사에 실패하면 exit 1 이다.
"""
import argparse
import pathlib
import sys

from playwright.sync_api import sync_playwright

# Windows 기본 콘솔은 cp949 다. 한글·중간점·줄표가 UnicodeEncodeError 를 낸다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:  # 리다이렉트된 스트림
        pass

CHECK_JS = """() => {
  const bad = [];
  document.querySelectorAll('table').forEach((t, i) => {
    if (t.scrollWidth > t.parentElement.clientWidth + 2) bad.push(i);
  });
  return {
    overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    wideTables: bad,
    katex: document.querySelectorAll('.katex').length,
    figs: document.querySelectorAll('svg.fig').length,
    figcaps: document.querySelectorAll('.figcap').length,
    tiles: document.querySelectorAll('section.tile').length,
    badges: document.querySelectorAll('.bdg').length,
    gantt: document.querySelectorAll('.gantt').length,
    metrics: document.querySelectorAll('.metric').length,
    // 스타일이 실제로 걸렸는지 — 토큰이 비어 있으면 CSS 삽입이 실패한 것이다
    primary: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(),
    bodyFont: getComputedStyle(document.body).fontFamily,
    // 도해가 뷰박스 밖으로 나갔는지
    svgClipped: [...document.querySelectorAll('svg.fig')].filter(s => {
      const vb = s.viewBox.baseVal, bb = s.getBBox();
      return bb.x < vb.x - 1 || bb.y < vb.y - 1 ||
             bb.x + bb.width > vb.x + vb.width + 1 ||
             bb.y + bb.height > vb.y + vb.height + 1;
    }).map(s => s.getAttribute('aria-label') || '(무제)'),
  };
}"""


def run(target: pathlib.Path, pdf: pathlib.Path | None, shot: pathlib.Path | None,
        landscape: bool) -> int:
    fails, notes = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.goto(target.resolve().as_uri())
        pg.wait_for_timeout(2500)

        text = pg.inner_text("body")
        for marker in ("⟦", "__BODY__", "__TITLE__", "__BASECSS__", "__MODECSS__"):
            if marker in text:
                fails.append(f"본문에 {marker} 가 남아 있다")
        if "%%I%%" in text or "%%D%%" in text:
            fails.append("구버전 ASCII 수식 마커가 본문에 남아 있다")

        r = pg.evaluate(CHECK_JS)
        if r["overflow"]:
            fails.append(f"가로 넘침 — scrollWidth {r['scrollWidth']} > innerWidth {r['innerWidth']}")
        if r["wideTables"]:
            fails.append(f"컨테이너를 넘는 표 인덱스 {r['wideTables']}")
        if r["primary"] != "#0066cc":
            fails.append(f"--primary 토큰이 걸리지 않았다 (값: {r['primary'] or '없음'}) — CSS 삽입 실패")
        if "Pretendard" not in r["bodyFont"]:
            fails.append(f"body 폰트 스택에 Pretendard 가 없다 — {r['bodyFont']}")
        if r["svgClipped"]:
            fails.append(f"viewBox 밖으로 나간 도해 — {r['svgClipped']}")
        if r["figs"] != r["figcaps"] - r["tiles"] * 0:  # 캡션은 표에도 붙으므로 하한만 본다
            pass
        if r["figcaps"] < r["figs"]:
            fails.append(f"캡션 없는 도해가 있다 — svg {r['figs']} · figcap {r['figcaps']}")

        notes.append(f"수식 {r['katex']} · 도해 {r['figs']} · 캡션 {r['figcaps']} · "
                     f"배지 {r['badges']} · 간트 {r['gantt']} · 메트릭 {r['metrics']} · 타일 {r['tiles']}")

        if shot:
            shot.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(shot / f"{target.stem}.png"), full_page=True)
            notes.append(f"스크린샷 — {shot / (target.stem + '.png')}")

        if pdf:
            pdf.parent.mkdir(parents=True, exist_ok=True)
            pg.pdf(path=str(pdf), format="A4", landscape=landscape, print_background=True)
            notes.append(f"PDF — {pdf}")

        b.close()

    print(f"── {target.name}")
    for n in notes:
        print("   " + n)
    for f in fails:
        print("   FAIL  " + f)
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+", type=pathlib.Path)
    ap.add_argument("--pdf", action="store_true", help="같은 이름의 PDF 도 뽑는다")
    ap.add_argument("--shot", type=pathlib.Path, default=None)
    args = ap.parse_args()

    rc = 0
    for t in args.targets:
        landscape = "deck" in t.stem
        rc |= run(t, t.with_suffix(".pdf") if args.pdf else None, args.shot, landscape)
    return rc


if __name__ == "__main__":
    sys.exit(main())

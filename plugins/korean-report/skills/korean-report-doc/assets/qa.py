# -*- coding: utf-8 -*-
"""
qa.py — 배포된 스킬 안에서 HTML을 렌더링해 검사한다.

    python <스킬경로>/assets/qa.py out.html [--pdf] [--shot dir]

SKILL.md §4 체크리스트의 기계 검사 부분을 수행한다.
사람이 봐야 하는 항목(다크 타일 반전, 절반 이상 빈 페이지)은 --shot으로 이미지를 남긴다.

종료 코드
    0  통과
    1  검사 실패 — 문서를 고친다
    2  검사를 실행하지 못함 — Playwright·Chromium 미설치, 대상 파일 없음, 인자 오류.
       문서가 아니라 환경의 문제다. stderr 한 줄이 다음 명령을 알린다
"""
import argparse
import html
import pathlib
import re
import shutil
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # 실행 시점에 NotReady 로 알린다. import traceback 은 다음 할 일을 알리지 않는다
    sync_playwright = None

EXIT_OK = 0
EXIT_FAILED = 1
# argparse 의 인자 오류도 2 다. 둘 다 「검사를 실행하지 못하였다」는 같은 뜻이다.
EXIT_NOT_READY = 2


class NotReady(RuntimeError):
    """검사를 실행할 환경이 갖춰지지 않았다. 메시지는 다음 할 일을 한 줄로 담는다."""


# Windows 기본 콘솔은 cp949다. 한글·중간점·줄표가 UnicodeEncodeError를 낸다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:  # 리다이렉트된 스트림
        pass

# design.md §7.1 — deck은 1 섹션 = 1 페이지다. 넘치면 타일이 잘린다.
# `.tile`은 인쇄 시 overflow:hidden이라 넘친 내용이 조용히 사라진다.
PRINT_JS = """() => {
  const MM = 96 / 25.4;              // 1mm = 3.78 CSS px
  const PAGE = 210 * MM;             // A4 가로 방향의 높이
  const over = [];
  document.querySelectorAll('section.tile').forEach((t, i) => {
    const need = t.scrollHeight;
    if (need > PAGE + 2) {
      const h2 = t.querySelector('h2');
      over.push({
        i,
        label: (h2 ? h2.innerText : t.className).replace(/\\s+/g, ' ').trim().slice(0, 30),
        need: Math.round(need),
        page: Math.round(PAGE),
      });
    }
  });
  return over;
}"""

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
    accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(),
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


def footer_template(title: str) -> str:
    """
    paper PDF 의 쪽 하단. Chromium 이 pageNumber · totalPages class 에 값을 채운다.
    header · footer 는 문서와 분리된 문맥에서 렌더되어 문서의 token 과 글꼴을 읽지 못한다.
    그래서 여기만 색과 글꼴을 직접 지정한다.
    """
    return ('<div style="width:100%;margin:0 16mm;display:flex;justify-content:space-between;'
            'font:7pt sans-serif;color:#7a7a7a">'
            f'<span>{html.escape(title)}</span>'
            '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


def _python() -> str:
    """
    설치 안내에 적을 interpreter. PATH 의 이름이 지금 interpreter 와 같을 때만 짧게 쓴다.
    `python` 이 없는 macOS 처럼 짧은 이름이 다른 interpreter 를 가리키면 그 안내는 틀린다.
    """
    for name in ("python", "python3"):
        if shutil.which(name) == sys.executable:
            return name
    exe = sys.executable or "python"
    return f'"{exe}"' if " " in exe else exe


def browser_missing(err: BaseException) -> bool:
    """
    Chromium 실행 파일이 없어 launch 가 실패하였는가.
    Playwright 는 이때 설치 안내 상자를 메시지에 붙여 던진다. `install-deps`(시스템 라이브러리
    부족)는 다른 처치가 필요하므로 여기에 포함하지 않는다.
    """
    msg = str(err)
    return "Executable doesn't exist" in msg or re.search(r"playwright install(?!-deps)", msg) is not None


def launch(p):
    """Chromium 을 띄운다. 설치되어 있지 않으면 Playwright 의 안내 상자 대신 한 줄로 알린다."""
    try:
        return p.chromium.launch()
    except Exception as e:
        if browser_missing(e):
            raise NotReady(f"Chromium 이 설치되어 있지 않다 — {_python()} -m playwright install chromium "
                           "실행 후 다시 검사한다") from None
        raise


def run(target: pathlib.Path, pdf: pathlib.Path | None, shot: pathlib.Path | None) -> int:
    """한 문서를 검사한다. 통과 0 · 실패 1. 환경이 갖춰지지 않았으면 NotReady 를 던진다."""
    if sync_playwright is None:
        py = _python()
        raise NotReady(f"Playwright 가 설치되어 있지 않다 — {py} -m pip install playwright 와 "
                       f"{py} -m playwright install chromium 실행 후 다시 검사한다")
    fails, notes = [], []
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.goto(target.resolve().as_uri())
        pg.wait_for_timeout(2500)

        # 모드는 파일명이 아니라 문서가 스스로 밝힌 것을 믿는다.
        mode = pg.evaluate("() => document.documentElement.dataset.mode || ''")
        if mode not in ("paper", "deck"):
            fails.append(f"data-mode가 없거나 알 수 없다 ({mode or '없음'})")
        landscape = mode == "deck"

        text = pg.inner_text("body")
        for marker in ("⟦", "__BODY__", "__TITLE__", "__TOKENCSS__", "__BASECSS__", "__MODECSS__"):
            if marker in text:
                fails.append(f"본문에 {marker}가 남아 있다")
        if "%%I%%" in text or "%%D%%" in text:
            fails.append("구버전 ASCII 수식 마커가 본문에 남아 있다")

        r = pg.evaluate(CHECK_JS)
        if r["overflow"]:
            fails.append(f"가로 넘침 — scrollWidth {r['scrollWidth']} > innerWidth {r['innerWidth']}")
        if r["wideTables"]:
            fails.append(f"컨테이너를 넘는 표 인덱스 {r['wideTables']}")
        if r["accent"] != "#0066cc":
            fails.append(f"--accent token 이 걸리지 않았다 (값: {r['accent'] or '없음'}) — CSS 삽입 실패")
        if "Pretendard" not in r["bodyFont"]:
            fails.append(f"body 폰트 스택에 Pretendard가 없다 — {r['bodyFont']}")
        if r["svgClipped"]:
            fails.append(f"viewBox 밖으로 나간 도해 — {r['svgClipped']}")
        # 캡션은 표에도 붙으므로 하한만 본다.
        if r["figcaps"] < r["figs"]:
            fails.append(f"캡션 없는 도해가 있다 — svg {r['figs']} · figcap {r['figcaps']}")

        notes.append(f"모드 {mode} · 수식 {r['katex']} · 도해 {r['figs']} · 캡션 {r['figcaps']} · "
                     f"배지 {r['badges']} · 간트 {r['gantt']} · 메트릭 {r['metrics']} · 타일 {r['tiles']}")

        # deck은 인쇄 레이아웃에서 타일이 한 쪽을 넘지 않아야 한다.
        if landscape:
            pg.set_viewport_size({"width": 1123, "height": 794})   # A4 가로 @96dpi
            pg.emulate_media(media="print")
            pg.wait_for_timeout(400)
            for o in pg.evaluate(PRINT_JS):
                fails.append(
                    f"타일 {o['i']}「{o['label']}」이 한 쪽을 넘는다 — "
                    f"{o['need']}px 필요, 쪽 높이 {o['page']}px. 섹션을 쪼갠다"
                )
            # "screen"이 아니라 "null"로 되돌린다 — screen으로 명시하면 emulation이 걸린
            # 채로 남아 뒤의 pg.pdf()가 print CSS 대신 화면 CSS 로 렌더한다.
            # 스크린샷은 emulation 을 걸지 않아도 기본이 screen 이라 영향이 없다.
            pg.emulate_media(media="null")

        if shot:
            shot.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(shot / f"{target.stem}.png"), full_page=True)
            notes.append(f"스크린샷 — {shot / (target.stem + '.png')}")

        if pdf:
            pdf.parent.mkdir(parents=True, exist_ok=True)
            if landscape:
                pg.pdf(path=str(pdf), format="A4", landscape=True, print_background=True)
            else:
                # 여백은 paper.css 의 @page 와 같다. footer 는 아래 여백 안에 인쇄된다.
                pg.pdf(path=str(pdf), format="A4", print_background=True,
                       display_header_footer=True, header_template="<span></span>",
                       footer_template=footer_template(pg.title()),
                       margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
            notes.append(f"PDF — {pdf}")

        b.close()

    print(f"── {target.name}")
    for n in notes:
        print("   " + n)
    for f in fails:
        print("   FAIL  " + f)
    return EXIT_FAILED if fails else EXIT_OK


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+", type=pathlib.Path)
    ap.add_argument("--pdf", action="store_true", help="같은 이름의 PDF도 뽑는다")
    ap.add_argument("--shot", type=pathlib.Path, default=None)
    args = ap.parse_args()

    missing = [t for t in args.targets if not t.is_file()]
    for t in missing:
        print(f"검사 대상 파일이 없다 — {t}", file=sys.stderr)
    if missing:
        return EXIT_NOT_READY

    rc = EXIT_OK
    try:
        for target in args.targets:
            rc = max(rc, run(target, target.with_suffix(".pdf") if args.pdf else None, args.shot))
    except NotReady as e:
        print(e, file=sys.stderr)
        return EXIT_NOT_READY
    return rc


if __name__ == "__main__":
    sys.exit(main())

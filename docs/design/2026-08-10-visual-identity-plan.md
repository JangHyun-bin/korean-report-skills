# 첫 화면 시각 정체성 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/design/2026-08-10-visual-identity.md` 가 규정한 로고·뱃지·배너를 저장소에 반영하고, 배너가 낡지 않도록 CI 가 재생성하게 한다.

**Architecture:** 로고는 정적 SVG 세 벌이며 테마 대응을 파일 안의 `@media (prefers-color-scheme: dark)` 로 처리한다. 배너는 실제 예시 문서에서 조각을 캡처해 HTML 레이아웃으로 합성한 뒤 PNG 두 벌로 찍는다. README 는 `<picture>` 로 두 벌을 전환한다. 검사는 자산 규격과 README 참조를 고정한다.

**Tech Stack:** SVG · Python 3.11+ · Playwright(Chromium) · pytest · GitHub Actions

## Global Constraints

- 액센트는 한 색이다. 라이트 `#0066cc`, 다크 `#2997ff`. 두 번째 색조를 추가하지 않는다.
- 잉크는 라이트 `#1d1d1f`, 다크 `#ffffff`. 회색은 잉크의 `opacity` 로만 표현한다.
- 로고 SVG 의 `viewBox` 는 `0 0 100 100` 이다.
- 뱃지는 위 제약에서 제외한다. GitHub 관용 색을 따른다.
- 모든 산문은 `tests/test_own_prose.py` 를 통과한다. 절 제목은 명사구다.
- 커밋 메시지에 AI 사용 흔적(트레일러·서명)을 넣지 않는다.
- 새 파이썬 스크립트는 Windows 콘솔에서도 한글이 깨지지 않게 `sys.stdout.reconfigure(encoding="utf-8")` 를 둔다.
- `ruff check .` 가 통과한다. 줄 길이 상한은 110 이다.

## 스펙과 달라지는 점 하나

스펙은 로고 색을 `currentColor` 로 규정하였다. **그대로 구현하면 동작하지 않는다.**
SVG 가 `<img src>` 로 불릴 때는 부모의 `color` 를 상속할 대상이 없다.
파일 안에 `<style>` 을 두고 `@media (prefers-color-scheme: dark)` 로 색을 전환한다.
이 방식은 `<img>` 로 불린 SVG 에서도 브라우저 설정을 따른다.

---

> **이후 변경 (2026-08-10)** — 이 문서가 규정한 것 중 **GitHub Pages 관련 부분은
> 실현되지 않았다.** 구현 직후 Pages 를 전면 제거하기로 결정하여 사이트·워크플로·
> 색인(`pages-index.html`)이 모두 없어졌다. 아래에서 그것들을 가리키는 대목은
> 이력으로 읽고 따르지 않는다. 파비콘 자산 자체는 남아 있다.
> Codex 는 이 저장소를 파일 추가 없이 마켓플레이스로 인식한다는 것이 뒤에 확인되었다.

## 파일 구조

| 파일 | 책임 |
|---|---|
| `docs/assets/logo.svg` | V2 — 40px 이상. README 헤더 |
| `docs/assets/logo-sm.svg` | V4 — 24~32px |
| `docs/assets/favicon.svg` | V6 — 16px. Pages 탭 아이콘 |
| `scripts/build-banner.py` | 조각 캡처 · 배너 합성 · PNG 두 벌 출력 |
| `docs/assets/banner-light.png` · `banner-dark.png` | 산출물. CI 가 재생성 |
| `tests/test_visual_identity.py` | 자산 규격과 README 참조 검사 |
| `README.md` | 헤더 교체 |
| `docs/pages-index.html` | favicon 연결 |
| `.github/workflows/ci.yml` · `pages.yml` | 배너 재생성 |

---

### Task 1: 로고 SVG 세 벌

**Files:**
- Create: `docs/assets/logo.svg`
- Create: `docs/assets/logo-sm.svg`
- Create: `docs/assets/favicon.svg`
- Test: `tests/test_visual_identity.py`

**Interfaces:**
- Produces: 세 SVG 파일. Task 3 이 `docs/assets/logo.svg` 를 README 에서 참조하고,
  Task 4 가 `docs/assets/favicon.svg` 를 Pages `<head>` 에서 참조한다.
- Produces: `tests/test_visual_identity.py` — Task 3 이 이 파일에 검사를 추가한다.

- [ ] **Step 1: 실패하는 검사 작성**

`tests/test_visual_identity.py` 를 새로 작성한다.

```python
# -*- coding: utf-8 -*-
"""
첫 화면 자산의 규격.

로고와 배너는 사람이 눈으로 볼 때만 문제가 드러나는 자산이라, 기계가 잡을 수 있는
것이라도 잡아 둔다 — 규격, 색 하드코딩, 참조 실재.
판단 근거는 docs/design/2026-08-10-visual-identity.md 에 있다.
"""
import re

import pytest
from conftest import ROOT, read

LOGOS = ["logo.svg", "logo-sm.svg", "favicon.svg"]


@pytest.mark.parametrize("name", LOGOS)
def test_logo_exists_with_fixed_viewbox(name):
    """viewBox 가 흔들리면 크기별 마크가 서로 다른 비율로 앉는다."""
    svg = read(ROOT / "docs" / "assets" / name)
    assert 'viewBox="0 0 100 100"' in svg, f"{name} 의 viewBox 가 규격과 다르다"


@pytest.mark.parametrize("name", LOGOS)
def test_logo_follows_dark_theme(name):
    """
    GitHub 다크에서 잉크가 검은색으로 남으면 로고가 사라진다.
    `<img>` 로 불린 SVG 는 부모 색을 상속하지 못하므로 파일 안에서 처리한다.
    """
    svg = read(ROOT / "docs" / "assets" / name)
    assert "prefers-color-scheme: dark" in svg, f"{name} 에 다크 대응이 없다"


@pytest.mark.parametrize("name", LOGOS)
def test_logo_uses_only_one_accent(name):
    """액센트 한 색 규칙. 라이트·다크 각 한 벌씩만 허용한다."""
    svg = read(ROOT / "docs" / "assets" / name)
    hexes = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{3,6}", svg)}
    allowed = {"#0066cc", "#2997ff", "#1d1d1f", "#ffffff", "#fff"}
    assert hexes <= allowed, f"{name} 에 규격 밖의 색이 있다: {hexes - allowed}"
```

- [ ] **Step 2: 검사 실패 확인**

Run: `python -m pytest tests/test_visual_identity.py -q`
Expected: FAIL — `docs/assets/logo.svg` 가 없어 `FileNotFoundError`

- [ ] **Step 3: `docs/assets/logo.svg` 작성**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img"
     aria-label="korean-report-skills">
  <style>
    .a { fill: #0066cc }
    .i { fill: #1d1d1f }
    .d { fill: #1d1d1f; opacity: .42 }
    @media (prefers-color-scheme: dark) {
      .a { fill: #2997ff }
      .i { fill: #ffffff }
      .d { fill: #ffffff; opacity: .42 }
    }
  </style>
  <rect class="a" x="4"  y="8"  width="17" height="17" rx="3.5"/>
  <rect class="i" x="27" y="8"  width="61" height="17" rx="3.5"/>
  <rect class="i" x="4"  y="38" width="92" height="14" rx="7"/>
  <rect class="d" x="4"  y="66" width="92" height="7"  rx="3.5"/>
  <rect class="d" x="4"  y="83" width="62" height="7"  rx="3.5"/>
</svg>
```

- [ ] **Step 4: `docs/assets/logo-sm.svg` 작성**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img"
     aria-label="korean-report-skills">
  <style>
    .a { fill: #0066cc }
    .i { fill: #1d1d1f }
    @media (prefers-color-scheme: dark) {
      .a { fill: #2997ff }
      .i { fill: #ffffff }
    }
  </style>
  <rect class="a" x="4"  y="20" width="22" height="22" rx="4.5"/>
  <rect class="i" x="33" y="20" width="63" height="22" rx="4.5"/>
  <rect class="i" x="4"  y="60" width="92" height="13" rx="6.5"/>
</svg>
```

- [ ] **Step 5: `docs/assets/favicon.svg` 작성**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img"
     aria-label="korean-report-skills">
  <style>
    .a { fill: #0066cc }
    .i { fill: #1d1d1f }
    @media (prefers-color-scheme: dark) {
      .a { fill: #2997ff }
      .i { fill: #ffffff }
    }
  </style>
  <rect class="a" x="6" y="16" width="30" height="30" rx="6"/>
  <rect class="i" x="6" y="62" width="88" height="18" rx="9"/>
</svg>
```

- [ ] **Step 6: 검사 통과 확인**

Run: `python -m pytest tests/test_visual_identity.py -q`
Expected: PASS — 9개

- [ ] **Step 7: 눈으로 확인**

Run:
```bash
python - <<'PY'
import pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
H = """<body style="margin:0;background:#fff;display:flex;gap:24px;align-items:flex-end;padding:24px">
%s</body>""" % "".join(
    f'<img src="{p}" width="{w}" height="{w}">'
    for p in ["logo.svg", "logo-sm.svg", "favicon.svg"] for w in (64, 32, 16))
pathlib.Path("docs/assets/_check.html").write_text(H, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(device_scale_factor=2)
    pg.goto(pathlib.Path("docs/assets/_check.html").resolve().as_uri()); pg.wait_for_timeout(700)
    pg.screenshot(path="dist/logo_check.png", full_page=True); b.close()
pathlib.Path("docs/assets/_check.html").unlink()
print("dist/logo_check.png")
PY
```
`dist/logo_check.png` 를 열어 세 마크가 각 크기에서 읽히는지 본다.
`favicon.svg` 가 16px 에서 파란 사각과 잉크 선으로 또렷해야 한다.

- [ ] **Step 8: 커밋**

```bash
git add docs/assets/logo.svg docs/assets/logo-sm.svg docs/assets/favicon.svg \
        tests/test_visual_identity.py
git commit -m "로고 SVG 세 벌

design.md §2.2 의 절 표제를 잘라낸 마크다. 크기별로 디테일을 덜어낸 세 벌을
두어, 하나로 16px 까지 버티려다 큰 크기가 빈약해지는 것을 피한다.

색은 파일 안의 @media (prefers-color-scheme: dark) 로 처리한다. currentColor
는 <img> 로 불린 SVG 에서 상속할 부모가 없어 동작하지 않는다."
```

---

### Task 2: 배너 생성기

**Files:**
- Create: `scripts/build-banner.py`
- Create: `docs/assets/banner-light.png` · `docs/assets/banner-dark.png` (실행 산출물)
- Modify: `tests/test_visual_identity.py` (검사 추가)

**Interfaces:**
- Consumes: `dist/example_paper.html` · `dist/example_deck.html` — `examples/build_example.py` 와
  `mathbuild.js` 가 앞서 생성한다.
- Produces: `docs/assets/banner-light.png` · `banner-dark.png`, 각 2240×600.
  Task 3 이 README 에서 이 두 경로를 참조한다.
- Produces: `build(theme: str) -> pathlib.Path` — 테마 문자열 `"light"` 또는 `"dark"` 를 받아
  기록한 PNG 경로를 돌려준다.

- [ ] **Step 1: 실패하는 검사 작성**

`tests/test_visual_identity.py` 끝에 추가한다.

```python
BANNERS = ["banner-light.png", "banner-dark.png"]


@pytest.mark.parametrize("name", BANNERS)
def test_banner_exists_with_expected_size(name):
    """
    배너 규격이 흔들리면 README 에서 높이가 튄다.
    2240×600 은 1120×300 을 2배 밀도로 찍은 것이다.
    """
    from PIL import Image

    path = ROOT / "docs" / "assets" / name
    assert path.exists(), f"{name} 이 없다 — python scripts/build-banner.py 로 생성한다"
    with Image.open(path) as im:
        assert im.size == (2240, 600), f"{name} 의 크기가 {im.size} 다"
```

- [ ] **Step 2: 검사 실패 확인**

Run: `python -m pytest tests/test_visual_identity.py -q -k banner`
Expected: FAIL — `banner-light.png 이 없다`

- [ ] **Step 3: `scripts/build-banner.py` 작성**

```python
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


def build(theme: str) -> pathlib.Path:
    """한 테마의 배너를 합성해 PNG 로 기록하고 그 경로를 돌려준다."""
    parts = capture_parts()
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
    for theme in ("light", "dark"):
        print(build(theme))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 배너 생성**

Run:
```bash
python examples/build_example.py
for m in paper deck; do
  node plugins/korean-report/skills/korean-report-doc/assets/mathbuild.js \
    "dist/example_${m}_raw.html" "dist/example_${m}.html" \
    --assets plugins/korean-report/skills/korean-report-doc/assets
done
python scripts/build-banner.py
```
Expected: `docs/assets/banner-light.png` 과 `banner-dark.png` 두 줄이 출력된다

- [ ] **Step 5: 검사 통과 확인**

Run: `python -m pytest tests/test_visual_identity.py -q`
Expected: PASS — 11개

`PIL` 이 없어 실패하면 `pip install pillow` 를 실행하고 `pyproject.toml` 의
`[project.optional-dependencies] dev` 에 `"pillow>=10"` 을 추가한다.

- [ ] **Step 6: 눈으로 확인**

`docs/assets/banner-light.png` 과 `banner-dark.png` 를 연다. 확인할 것은 셋이다.

- 세 조각이 서로 다른 내용인가 — 같은 이미지가 두 번 들어가면 실패다
- 가운데 다크 타일이 앞에 있고 대비가 보이는가
- 다크 판에서 흰 종이가 어둠 위에 떠 있는 것으로 읽히는가

- [ ] **Step 7: `ruff` 통과 확인**

Run: `python -m ruff check .`
Expected: `All checks passed!`

- [ ] **Step 8: 커밋**

```bash
git add scripts/build-banner.py docs/assets/banner-light.png docs/assets/banner-dark.png \
        tests/test_visual_identity.py pyproject.toml
git commit -m "배너 생성기

실제 예시 문서에서 세 조각을 캡처해 겹쳐 합성한다. 손으로 갱신하는 스크린샷은
반드시 문서와 어긋나므로 CI 가 매번 재생성하게 한다.

라이트·다크 두 벌을 찍는다. 흰 종이가 다크에서 뜨는 것은 문제가 아니다 —
배경만 어둡게 하면 종이가 어둠 위에 떠 있는 것으로 읽히고, 가운데 다크 타일과
대비가 생겨 두 모드가 있다는 것이 한 장에서 전달된다."
```

---

### Task 3: README 헤더

**Files:**
- Modify: `README.md:1-8`
- Modify: `tests/test_visual_identity.py` (검사 추가)

**Interfaces:**
- Consumes: `docs/assets/logo.svg` (Task 1), `docs/assets/banner-light.png` ·
  `banner-dark.png` (Task 2)

- [ ] **Step 1: 실패하는 검사 작성**

`tests/test_visual_identity.py` 끝에 추가한다.

```python
def test_readme_header_carries_logo_and_banner():
    """첫 화면의 시각 앵커. 빠지면 스펙이 규정한 구조가 무너진다."""
    readme = read(ROOT / "README.md")
    assert "docs/assets/logo.svg" in readme, "README 에 로고가 없다"
    for name in BANNERS:
        assert f"docs/assets/{name}" in readme, f"README 에 {name} 참조가 없다"


def test_readme_banner_switches_by_theme():
    """
    다크에서 라이트 배너가 뜨면 첫 화면이 튄다.
    `<picture>` 의 source 가 다크를 먼저 잡아야 한다.
    """
    readme = read(ROOT / "README.md")
    m = re.search(r"<picture>.*?</picture>", readme, re.S)
    assert m, "README 에 <picture> 블록이 없다"
    block = m.group(0)
    assert "prefers-color-scheme: dark" in block, "다크 source 가 없다"
    assert "banner-dark.png" in block and "banner-light.png" in block


def test_readme_badges_are_present():
    """뱃지 행은 신뢰 신호다. 넷을 유지한다."""
    readme = read(ROOT / "README.md")
    for label in ("tests", "release", "plugin", "license"):
        assert f"img.shields.io/badge/{label}" in readme or f"-{label}-" in readme, \
            f"{label} 뱃지가 없다"
```

- [ ] **Step 2: 검사 실패 확인**

Run: `python -m pytest tests/test_visual_identity.py -q -k readme`
Expected: FAIL — `README 에 로고가 없다`

- [ ] **Step 3: README 머리 교체**

`README.md` 의 1~8행(제목부터 `---` 앞까지)을 아래로 교체한다.
**질문형 제목이 h1 자리를 유지한다** — 스펙이 규정한 구조이며, 워드마크는 일반 행이다.
그 아래
`## "디자인이 별로예요"` 부터는 손대지 않는다.

```markdown
<img src="docs/assets/logo.svg" width="44" align="left" alt="">

**korean-report-skills**

[![tests](https://img.shields.io/badge/tests-170%20passing-3fb950)](../../actions)
[![release](https://img.shields.io/badge/release-v1.9.0-0066cc)](../../releases)
[![plugin](https://img.shields.io/badge/plugin-Claude%20Code-8957e5)](INSTALL.md)
[![license](https://img.shields.io/badge/license-Apache--2.0-d29922)](LICENSE)

# 왜 Claude가 만든 한국어 문서는 어딘가 이상할까

내용은 맞는데 **문서로 내밀기가 망설여지는** 경험. 그 이유를 다섯 가지로 나누고
각각을 규약으로 고정한 스킬셋입니다.

Claude Code · Codex · Cursor 에 파일 수정 없이 들어갑니다 →
[설치](#설치) · [실물 문서 보기](https://janghyun-bin.github.io/korean-report-skills/)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.png">
  <img src="docs/assets/banner-light.png" alt="paper 보고서와 deck 협의자료 — 스킬이 만들어낸 문서 세 장">
</picture>

paper(세로·보고서) · deck(가로·협의자료) — 전부 HTML 파일 하나로 완결됩니다
```

- [ ] **Step 4: 검사 통과 확인**

Run: `python -m pytest tests/ -q`
Expected: PASS — 전부

`test_own_prose.py` 는 README 를 대상에서 제외하므로 질문형 제목은 통과한다.

- [ ] **Step 5: 눈으로 확인**

GitHub 에서 라이트·다크를 오가며 본다. 확인할 것은 셋이다.

- 로고가 워드마크와 시각 무게가 맞는가
- 다크에서 로고의 잉크가 흰색으로 바뀌는가
- 다크에서 배너가 어두운 판으로 바뀌는가

- [ ] **Step 6: 커밋**

```bash
git add README.md tests/test_visual_identity.py
git commit -m "README 헤더에 로고와 배너

첫 화면에 시각 앵커가 없었다. 이 저장소는 문서 layout 도구라 첫 화면이
볼품없으면 그 자체가 반증이 된다.

구조는 로고 · 뱃지 · 태그라인 · 배너다. 질문형 제목이 태그라인 자리를 그대로
차지하므로 기존 구조와 충돌하지 않는다. 배너는 <picture> 로 테마를 따라간다."
```

---

### Task 4: Pages 파비콘과 CI 연결

**Files:**
- Modify: `docs/pages-index.html:5` (`<title>` 다음 줄)
- Modify: `.github/workflows/ci.yml:51-57`
- Modify: `.github/workflows/pages.yml` (사이트 구성 단계)

**Interfaces:**
- Consumes: `docs/assets/favicon.svg` (Task 1), `scripts/build-banner.py` (Task 2)

- [ ] **Step 1: Pages 에 파비콘 연결**

`docs/pages-index.html` 의 `<meta name="description" ...>` 다음 줄에 추가한다.

```html
<link rel="icon" href="favicon.svg" type="image/svg+xml">
```

- [ ] **Step 2: Pages 워크플로에 파비콘 복사 추가**

`.github/workflows/pages.yml` 의 `사이트 구성` 단계 안, `cp docs/pages-index.html site/index.html`
다음 줄에 추가한다.

```bash
          cp docs/assets/favicon.svg  site/favicon.svg
```

- [ ] **Step 3: CI 에 배너 재생성 추가**

`.github/workflows/ci.yml` 의 `README 전후 대비 자산 빌드` 단계 **뒤에** 새 단계를 삽입한다.

```yaml
      - name: 배너 재생성과 대조
        run: |
          python scripts/build-banner.py
          git diff --exit-code --stat docs/assets/banner-light.png docs/assets/banner-dark.png \
            || { echo "배너가 문서와 어긋난다. python scripts/build-banner.py 를 실행하고 커밋한다."; exit 1; }
```

- [ ] **Step 4: 로컬에서 같은 명령 확인**

Run:
```bash
python scripts/build-banner.py
git diff --exit-code --stat docs/assets/banner-light.png docs/assets/banner-dark.png
```
Expected: 종료 코드 0. 차이가 나오면 배너를 커밋하지 않은 것이다.

PNG 는 렌더 환경에 따라 바이트가 달라질 수 있다. CI(우분투)와 로컬(윈도)의 결과가
매번 어긋나면 이 단계를 `continue-on-error: true` 로 낮추고, 대조 대신
**배너 파일이 존재하는지**만 확인하도록 완화한다. 판단 기준은 CI 가 두 번 연속
같은 이유로 실패하는가이다.

- [ ] **Step 5: 워크플로 문법 확인**

Run: `python -c "import yaml,sys; [yaml.safe_load(open(f,encoding='utf-8')) for f in ['.github/workflows/ci.yml','.github/workflows/pages.yml']]; print('yaml ok')"`
Expected: `yaml ok`

`yaml` 이 없으면 `pip install pyyaml` 을 실행한다.

- [ ] **Step 6: 전체 검증**

Run:
```bash
python -m ruff check .
npm run test:node
python -m pytest tests/ -q
bash scripts/pack-skills.sh && bash scripts/pack-skills.sh --verify
```
Expected: 전부 통과

- [ ] **Step 7: 커밋과 푸시**

```bash
git add docs/pages-index.html .github/workflows/ci.yml .github/workflows/pages.yml
git commit -m "파비콘 연결과 배너 재생성 자동화

Pages 탭 아이콘을 favicon.svg 로 연결한다.

CI 가 배너를 매번 다시 만들고 커밋된 것과 대조한다. 실제 문서에서 잘라낸
자산이라 문서가 바뀌면 낡는데, 스크린샷을 손으로 갱신하는 저장소는 반드시
어긋난다."
git push origin main
```

- [ ] **Step 8: CI 통과 확인**

Run: `gh run watch $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status`
Expected: CI 와 Pages 두 워크플로가 모두 성공

Pages 배포 뒤 `https://janghyun-bin.github.io/korean-report-skills/` 의 탭 아이콘을 확인한다.

---

## 마무리

- [ ] `CHANGELOG.md` 에 `[1.10.0]` 항목 추가. 로고 세 벌, 배너 생성기, README 헤더, 파비콘.
- [ ] `package.json` · `pyproject.toml` · `.claude-plugin/marketplace.json` ·
      `plugins/korean-report/.claude-plugin/plugin.json` 의 version 을 `1.10.0` 으로 정합한다.
      `tests/test_consistency.py::test_version_is_the_same_in_every_place` 와
      `test_plugin_version_matches_package_version` 이 넷을 대조한다.
- [ ] README 뱃지의 검사 수(`170 passing`)를 실제 수와 정합한다.
      `python -m pytest tests/ -q` 의 마지막 줄과 `npm run test:node` 의 `# pass` 를 더한다.
- [ ] 프리뷰 서버 정리 — `pkill -f "http.server"`, `dist/logo-preview.html` ·
      `logo-a1.html` · `banner.html` · `banner-a.html` 삭제. `dist/` 는 추적하지 않으므로
      커밋에 영향이 없다.

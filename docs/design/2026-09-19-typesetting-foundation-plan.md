# ① typesetting 기반 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `korean-report-doc`의 값을 `tokens.css` 한 곳으로 모으고, 한글 typesetting 규칙 · type scale ·
동봉 본문 font · paper PDF footer · styleguide 를 추가한다.

**Architecture:** CSS custom property 가 token 체계다. `tokens.css`가 색 · type scale · space · surface
재매핑 · 인쇄 복귀를 담고, `base.css` · `paper.css` · `deck.css`는 `var()`로만 참조한다.
`mathbuild.js`가 `__TOKENCSS__` 자리를 채우고 동봉 Pretendard subset 을 기본으로 내장한다.
규칙은 `tests/test_tokens.py`가 강제한다. generator 는 두지 않는다.

**Tech Stack:** CSS custom property · `color-mix()` · Node 20+ (`mathbuild.js`, KaTeX) ·
Python 3.11+ (pytest, Playwright) · Pretendard 1.3.9 공식 subset woff2

**Spec:** `docs/design/2026-09-19-design-system.md` §4

## Global Constraints

- 새 runtime 의존성을 추가하지 않는다. font 는 Pretendard 1.3.9 공식 배포본을 **변경 없이** 동봉한다
- 색 리터럴(`#…` · `rgb(` · `rgba(`)은 `assets/css/tokens.css`에만 존재한다
- 금지어 — `tests/test_own_prose.py::test_deprecated_korean_typesetting_word_is_absent`가 저장소 전체에서 차단하는 한국어 용어를 쓰지 않는다. `typesetting`으로 쓴다
- 예시 내용은 가상 사례 「A사 — 인라인 계측 체계 확립과 수율 개선」에서만 가져온다
- 새 `.md` 산문은 `korean-report-style` lint 를 통과해야 한다
- commit message 는 전문 영어로 쓰고 끝에 다음 두 줄을 부기한다

  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
  ```

- 경로 약어 — 아래에서 `$A`는 `plugins/korean-report/skills/korean-report-doc/assets`다

---

## 파일 구조

| 파일 | 변경 | 책임 |
|---|---|---|
| `$A/css/tokens.css` | 신설 | 값의 단일 원천. surface 재매핑 · 인쇄 복귀 · 1.x alias |
| `$A/css/base.css` · `paper.css` · `deck.css` | 수정 | `var()` 참조만 유지 |
| `$A/paper_template.html` · `deck_template.html` | 수정 | `__TOKENCSS__` 자리 |
| `$A/mathbuild.js` | 수정 | `__TOKENCSS__` 삽입, 동봉 font 기본 내장, subset 밖 한글 경고 |
| `$A/qa.py` | 수정 | `--accent` 검사, paper PDF footer |
| `$A/figures.py` | 수정 | 미사용 hex 상수 삭제 |
| `$A/fonts/` | 신설 | Pretendard subset woff2 3종 · `LICENSE.txt` · `subset_glyphs.txt` |
| `scripts/csstokens.py` | 신설 | CSS 블록 parser 와 WCAG 대비 계산. 검사와 styleguide 가 공유 |
| `examples/build_styleguide.py` | 신설 | styleguide raw HTML 생성 |
| `tests/test_tokens.py` · `tests/test_fonts.py` · `tests/test_qa_pdf.py` | 신설 | 규칙 검사 |
| `tests/conftest.py` · `test_consistency.py` · `test_build_e2e.py` · `mathbuild.test.js` | 수정 | 새 자리와 이름 반영 |
| `.github/workflows/ci.yml` · `package.json` · `scripts/package-smoke.js` | 수정 | styleguide build, 배포 목록 |
| `.gitignore` · `NOTICE` · `README.md` · `INSTALL.md` · `CHANGELOG.md` · `SKILL.md` · `references/design.md` · `references/figures.md` · `scripts/new-document.py` | 수정 | 문서 정합 |

---

### Task 1: 값 불변 token 이관

**Files:**
- Create: `$A/css/tokens.css`, `scripts/csstokens.py`, `tests/test_tokens.py`
- Modify: `$A/css/base.css`, `$A/css/paper.css`, `$A/css/deck.css`, `$A/paper_template.html`, `$A/deck_template.html`, `$A/mathbuild.js`, `$A/qa.py`, `$A/figures.py`, `tests/conftest.py`, `tests/test_consistency.py`, `tests/test_build_e2e.py`, `tests/mathbuild.test.js`

**Interfaces:**
- Produces: CSS token 이름 — `--accent` `--on-accent` `--ink` `--ink-2` `--ink-3` `--surface` `--surface-2` `--surface-3` `--rule` `--rule-soft` `--rule-heavy` `--mark` `--mark-ink` `--fig-line` `--fig-soft` `--fig-pale` `--fig-mid` `--code-bg` `--code-ink` `--code-dim` `--cover-rule` `--scroll-thumb` `--font-body` `--mono`
- Produces: `csstokens.strip_comments(text) -> str`, `csstokens.blocks(css) -> list[tuple[str, str, dict[str, str]]]`, `csstokens.declared(css, selector, media="") -> dict[str, str]`, `csstokens.contrast(hex_a, hex_b) -> float`, `csstokens.COLOR_LITERAL`
- Produces: template 자리 `__TOKENCSS__` (`__KATEXCSS__` 다음, `__BASECSS__` 앞)

- [ ] **Step 1: 이관 전 screenshot 기준 확보**

값이 그대로인지 판정하는 기준이다. CSS 를 수정하기 **전에** 실행한다.

```bash
npm ci
python3 examples/build_example.py
A=plugins/korean-report/skills/korean-report-doc/assets
for m in paper deck; do node $A/mathbuild.js dist/example_${m}_raw.html dist/example_${m}.html --assets $A; done
python3 scripts/qa.py dist/example_paper.html dist/example_deck.html --shot dist/shots-before
```

Expected: 두 문서 모두 FAIL 없이 종료, `dist/shots-before/example_paper.png` · `example_deck.png` 생성.

- [ ] **Step 2: `scripts/csstokens.py` 작성**

```python
# -*- coding: utf-8 -*-
"""
csstokens.py — tokens.css 를 읽는 최소 parser 와 WCAG 대비 계산.

tests/test_tokens.py 와 examples/build_styleguide.py 가 함께 쓴다.
CSS 전체를 해석하지 않는다. 이 저장소의 CSS 가 쓰는 형태 — 규칙, 한 겹의 @media,
@page — 만 읽는다.
"""
import re

# 색 리터럴. tokens.css 밖에서 발견되면 theme 이 그 자리의 색을 교체하지 못한다.
COLOR_LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(")


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/|<!--.*?-->", "", text, flags=re.S)


def blocks(css: str, media: str = "") -> list[tuple[str, str, dict[str, str]]]:
    """(media, selector 목록, 선언) 을 파일 순서대로 돌려준다. @media 는 풀고 @page 는 건너뛴다."""
    css = strip_comments(css)
    out, i = [], 0
    while True:
        j = css.find("{", i)
        if j < 0:
            return out
        head = css[i:j].strip()
        depth, k = 1, j + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        body = css[j + 1:k - 1]
        if head.startswith("@media"):
            out += blocks(body, head)
        elif not head.startswith("@"):
            decls = {p.strip(): v.strip() for p, v in re.findall(r"([\w-]+)\s*:\s*([^;]+)", body)}
            out.append((media, head, decls))
        i = k


def declared(css: str, selector: str, media: str = "") -> dict[str, str]:
    """selector 목록에 `selector` 가 정확히 들어 있는 블록의 선언을 파일 순서대로 합친다."""
    merged: dict[str, str] = {}
    for m, head, decls in blocks(css):
        if m == media and selector in [s.strip() for s in head.split(",")]:
            merged.update(decls)
    return merged


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG 2 대비비. 두 값 모두 불투명 hex 여야 한다."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


if __name__ == "__main__":
    assert round(contrast("#000", "#fff"), 1) == 21.0
    assert round(contrast("#7a7a7a", "#fff"), 2) == 4.3
    sample = ":root{--a:#fff}\n.dark,.black{--a:#000}\n@media print{.dark,.black{--a:#fff}}"
    assert declared(sample, ".dark") == {"--a": "#000"}
    assert declared(sample, ".black", "@media print") == {"--a": "#fff"}
    print("ok")
```

Run: `python3 scripts/csstokens.py`
Expected: `ok`

- [ ] **Step 3: `tests/conftest.py`에 경로와 bundle 반영**

`sys.path.insert(0, str(STYLE_ASSETS))` 다음 줄에 추가한다. **앞이 아니라 뒤에** 추가한다 —
`scripts/qa.py` 호환 진입점이 `assets/qa.py`를 가리면 `import qa`가 다른 module 을 읽는다.

```python
sys.path.append(str(ROOT / "scripts"))   # csstokens — assets/qa.py 를 가리지 않도록 뒤에 둔다
```

`css_bundle()`의 파일 목록을 교체한다.

```python
def css_bundle() -> str:
    return "\n".join(read(CSS / f) for f in ("tokens.css", "base.css", "paper.css", "deck.css"))
```

- [ ] **Step 4: 실패하는 `tests/test_tokens.py` 작성**

```python
# -*- coding: utf-8 -*-
"""
tokens.css 가 값의 단일 원천인지 검사한다.

색 리터럴이 component CSS 로 새면 theme 이 그 자리를 교체하지 못한다. 다크 surface 에서
글자가 사라지던 사고(figures.py 가 hex 를 방출하던 때)와 같은 계통이다.
"""
import re
import warnings

import csstokens as T
import pytest
from conftest import ASSETS, CSS, read

TOKENS = read(CSS / "tokens.css")
COMPONENT = {f: read(CSS / f) for f in ("base.css", "paper.css", "deck.css")}
TEMPLATES = {f: read(ASSETS / f) for f in ("paper_template.html", "deck_template.html")}
ROOT_T = T.declared(TOKENS, ":root")
DARK_T = T.declared(TOKENS, ".dark")
BLACK_T = T.declared(TOKENS, ".black")
LIGHT_SURFACES = ("--surface", "--surface-2", "--surface-3")


@pytest.mark.parametrize("name", [*COMPONENT, *TEMPLATES])
def test_color_literals_live_only_in_tokens(name):
    text = T.strip_comments({**COMPONENT, **TEMPLATES}[name])
    found = T.COLOR_LITERAL.findall(text)
    assert not found, f"{name} 에 색 리터럴 {found} — tokens.css 에 token 을 두고 var() 로 참조한다"


def test_every_var_is_defined():
    """alias 가 가리키는 대상도 여기서 함께 검사된다."""
    text = "\n".join(T.strip_comments(s) for s in (TOKENS, *COMPONENT.values()))
    used = set(re.findall(r"var\(\s*(--[\w-]+)", text))
    defined = set(re.findall(r"(--[\w-]+)\s*:", text))
    assert not used - defined, f"정의되지 않은 token: {sorted(used - defined)}"


@pytest.mark.parametrize("surface,values", [(".dark", DARK_T), (".black", BLACK_T)])
def test_print_restores_every_dark_override(surface, values):
    """인쇄는 다크 surface 를 밝은 값으로 되돌린다. 하나라도 빠지면 인쇄본에 어두운 값이 남는다."""
    restored = T.declared(TOKENS, surface, "@media print")
    overrides = {k for k, v in values.items() if ROOT_T.get(k) != v and not v.startswith("var(")}
    assert not overrides - set(restored), f"{surface} 인쇄 복귀 누락: {sorted(overrides - set(restored))}"
    wrong = {k: v for k, v in restored.items() if ROOT_T.get(k) != v}
    assert not wrong, f"{surface} 인쇄 복귀 값이 :root 와 다르다: {wrong}"


def test_mark_ink_is_never_redefined():
    """--mark-ink 는 고정이다. 다크 surface 가 뒤집으면 노랑 위 흰 글자가 된다."""
    for media, head, decls in T.blocks(TOKENS):
        if "--mark-ink" in decls:
            assert head == ":root" and not media, f"{media} {head} 가 --mark-ink 를 다시 정의한다"


def _body_pairs():
    for ink in ("--ink", "--ink-2"):
        for s in LIGHT_SURFACES:
            yield f"light {ink} / {s}", ROOT_T[ink], ROOT_T[s]
        yield f"dark {ink}", DARK_T[ink], DARK_T["--surface"]
        yield f"black {ink}", BLACK_T[ink], BLACK_T["--surface"]


@pytest.mark.parametrize("label,fg,bg", list(_body_pairs()))
def test_body_text_contrast(label, fg, bg):
    ratio = T.contrast(fg, bg)
    assert ratio >= 4.5, f"{label} 대비 {ratio:.2f}:1 — 본문 역할은 4.5:1 이상"


def test_accent_contrast():
    pairs = [(ROOT_T["--accent"], ROOT_T[s]) for s in LIGHT_SURFACES]
    pairs += [(DARK_T["--accent"], DARK_T["--surface"]), (BLACK_T["--accent"], BLACK_T["--surface"])]
    low = [(fg, bg, round(T.contrast(fg, bg), 2)) for fg, bg in pairs if T.contrast(fg, bg) < 3]
    assert not low, f"accent 대비 3:1 미달: {low}"


def test_secondary_text_contrast_is_recorded():
    """--ink-3 은 1.0 에서 경고만 한다. 값 조정은 theme 단계에서 surface 별로 정한다(명세 §9)."""
    pairs = [(f"light / {s}", ROOT_T["--ink-3"], ROOT_T[s]) for s in LIGHT_SURFACES]
    pairs += [("dark", DARK_T["--ink-3"], DARK_T["--surface"])]
    for label, fg, bg in pairs:
        ratio = T.contrast(fg, bg)
        if ratio < 4.5:
            warnings.warn(f"--ink-3 {label} 대비 {ratio:.2f}:1", stacklevel=1)
```

Run: `python3 -m pytest tests/test_tokens.py -q`
Expected: FAIL — `FileNotFoundError: ... tokens.css`

- [ ] **Step 5: `$A/css/tokens.css` 작성**

```css
/* tokens.css — 값의 단일 원천
 *
 * 색 리터럴은 이 파일에만 둔다. base.css · paper.css · deck.css 는 var() 로만 참조한다.
 * tests/test_tokens.py 가 강제한다.
 *
 * 파생 token 과 1.x alias 는 `:root,.dark,.black` 에 선언한다. custom property 안의
 * var() 는 선언된 요소에서 계산되어 자식에게 값으로 상속되므로, :root 에만 두면
 * 다크 surface 안에서도 밝은 값이 남는다.
 */

:root{
 /* accent — 유일한 유채색 */
 --accent:#0066cc;
 --on-accent:#fff;

 /* ink */
 --ink:#1d1d1f; --ink-2:#333; --ink-3:#7a7a7a;

 /* surface */
 --surface:#fff; --surface-2:#f5f5f7; --surface-3:#fafafc;

 /* rule */
 --rule:#e0e0e0; --rule-soft:#f0f0f0;

 /* 강조 — accent 가 아니라 독자 층위다. design.md §4.7 */
 --mark:#fbeaa0;
 --mark-ink:#1d1d1f;   /* 고정이다. 다크 surface 가 뒤집는 --ink 를 상속하면 안 된다 */

 /* 도해 팔레트 — figures.py 는 fi-* · st-* class 만 방출하고 base.css 가 이 token 에 잇는다 */
 --fig-line:#c7ccd2; --fig-soft:#dfe4e9; --fig-pale:#eef3f8; --fig-mid:#8695a6;

 /* code block — surface 와 무관하게 어둡다 */
 --code-bg:#272729; --code-ink:#e6e6e8; --code-dim:#8b8b90;

 --cover-rule:#5a5a60;
 --scroll-thumb:#d5d9de;

 /* spacing */
 --s-xs:8px; --s-sm:12px; --s-md:17px; --s-lg:24px;
 --s-xl:32px; --s-xxl:48px; --s-sec:80px;

 /* radius */
 --r-sm:8px; --r-md:12px; --r-lg:18px; --r-pill:9999px;

 --font-body:'Pretendard','Pretendard Variable',-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
 --mono:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
}

/* 다크 surface — 밝은 면의 파랑은 #272729 에서 대비가 모자라 accent 도 교체한다 */
.dark,.black{
 --accent:#2997ff;
 --ink:#fff; --ink-2:#d6d6da; --ink-3:#8b8b90;
 --rule:#3a3a3e; --rule-soft:#2f2f33;
 --surface-2:rgba(255,255,255,.10); --surface-3:rgba(255,255,255,.06);
 /* 도해 token 도 함께 뒤집는다 — 빠뜨리면 #1d1d1f 글자가 #272729 위에서 사라진다 */
 --fig-line:#4a4a50; --fig-soft:#3d3d43; --fig-pale:rgba(41,151,255,.16); --fig-mid:#8b95a3;
}
.dark{--surface:#272729}
.black{--surface:#000}

/* 파생 token 과 1.x alias — surface 마다 다시 계산되도록 세 곳에 선언한다 */
:root,.dark,.black{
 --rule-heavy:var(--ink);
 /* 1.x alias. 2.0 에서 제거한다 */
 --primary:var(--accent); --ink80:var(--ink-2); --ink48:var(--ink-3);
 --canvas:var(--surface); --parchment:var(--surface-2); --pearl:var(--surface-3);
 --hairline:var(--rule); --divider:var(--rule-soft);
 --tile1:var(--code-bg); --black:#000; --font:var(--font-body);
}

/* 큰 다크 면을 인쇄하지 않는다(design.md §7.3). 다크 surface 를 :root 의 값으로 되돌린다 */
@media print{
 .dark,.black{
  --accent:#0066cc;
  --ink:#1d1d1f; --ink-2:#333; --ink-3:#7a7a7a;
  --surface:#fff; --surface-2:#f5f5f7; --surface-3:#fafafc;
  --rule:#e0e0e0; --rule-soft:#f0f0f0;
  --fig-line:#c7ccd2; --fig-soft:#dfe4e9; --fig-pale:#eef3f8; --fig-mid:#8695a6;
 }
}
```

- [ ] **Step 6: `base.css` · `paper.css`의 변수명 교체**

```bash
A=plugins/korean-report/skills/korean-report-doc/assets
perl -pi -e '
  s/var\(--primary\)/var(--accent)/g;  s/var\(--ink80\)/var(--ink-2)/g;
  s/var\(--ink48\)/var(--ink-3)/g;     s/var\(--canvas\)/var(--surface)/g;
  s/var\(--parchment\)/var(--surface-2)/g; s/var\(--pearl\)/var(--surface-3)/g;
  s/var\(--hairline\)/var(--rule)/g;   s/var\(--divider\)/var(--rule-soft)/g;
  s/var\(--tile1\)/var(--code-bg)/g;   s/var\(--font\)/var(--font-body)/g;
' $A/css/base.css $A/css/paper.css
```

class 이름 `fi-ink48` · `st-ink48`은 `var(--…)` 형태가 아니므로 교체되지 않는다. 그대로 유지한다.

- [ ] **Step 7: `base.css`의 `:root` 블록과 색 리터럴 정리**

`:root{ … }` 블록 전체(현행 9~40행)를 삭제한다. 이어서 다음을 교체한다.

| 현행 | 교체 |
|---|---|
| `a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(0,102,204,.26)}` | `a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--rule);`<br>`border-bottom-color:color-mix(in srgb,var(--accent) 26%,transparent)}` |
| `.bdg.meas{background:var(--accent);color:#fff}` | `.bdg.meas{background:var(--accent);color:var(--on-accent)}` |
| `.bdg.impl{color:var(--accent);border:1px solid rgba(0,102,204,.5)}` | `.bdg.impl{color:var(--accent);border:1px solid var(--accent);`<br>`border-color:color-mix(in srgb,var(--accent) 50%,transparent)}` |
| `th{… border-bottom:1px solid var(--ink);…}` | `border-bottom:1px solid var(--rule-heavy)` |
| `tr.hl td{background:rgba(0,102,204,.045)}` | `tr.hl td{background:var(--surface-3);background:color-mix(in srgb,var(--accent) 4.5%,transparent)}` |
| `.scroll.wide::-webkit-scrollbar-thumb{background:#d5d9de;…}` | `background:var(--scroll-thumb)` |
| `.warn{background:#fff;border:1px solid var(--rule);border-left:3px solid var(--ink)}` | `.warn{background:var(--surface);border:1px solid var(--rule);border-left:3px solid var(--rule-heavy)}` |
| `.finding{background:#fff;border:1px solid rgba(0,102,204,.3);border-left:3px solid var(--accent)}` | `.finding{background:var(--surface);border:1px solid var(--accent);`<br>`border-color:color-mix(in srgb,var(--accent) 30%,transparent);border-left:3px solid var(--accent)}` |
| `pre{…background:var(--code-bg);color:#e6e6e8;…}` | `color:var(--code-ink)` |
| `pre .c{color:#8b8b90}` | `pre .c{color:var(--code-dim)}` |

`.finding`에서 `border-left`는 `border-color` **뒤에** 둔다. 앞에 두면 왼쪽 괘선 색이 30% 로 덮인다.
`color-mix()`를 쓰는 선언은 모두 불투명 fallback 선언을 앞에 둔다(명세 §8).

파일 머리 주석의 「이 파일은 두 모드가 함께 쓰는 토큰과 컴포넌트만 담는다」를
「값은 tokens.css 에 있다. 이 파일은 var() 로만 참조한다」로 교체한다.

- [ ] **Step 8: `paper.css`의 굵은 괘선 교체**

`.paper-head{…border-bottom:1px solid var(--ink)}`와 `h2{…border-bottom:1px solid var(--ink);…}`의
`var(--ink)`를 `var(--rule-heavy)`로 교체한다.

- [ ] **Step 9: `deck.css` 교체**

재매핑 블록은 `tokens.css`로 이전되었다. 다크 surface 위의 `code` · `.note` · `.warn` · `.finding`
재정의는 `--surface-2` · `--surface-3` · `--surface`가 같은 값을 산출하므로 삭제한다. 인쇄 블록의
`.dark .eyebrow` · `.dark table th` · `.dark .bdg.meas` 재정의도 token 복귀로 같은 결과가 되므로 삭제한다.

```css
/* deck.css — 가로·1섹션 1페이지 모드
 * base.css 위에만 얹는다. 공통 규칙을 여기에 다시 쓰지 않는다.
 *
 * 타일은 full-bleed 다. body 에 좌우 패딩을 주지 않는다 —
 * 패딩은 .tile 이 가지고, 폭 제한은 .wrap 이 한다.
 */

:root{ --w:1120px }

body{padding:0}

/* ── tiles ──────────────────────────────────────────────── */
.tile{padding:var(--s-sec) var(--s-lg)}
.tile.light{background:var(--surface)}
.tile.parch{background:var(--surface-2)}
/* dark · black 의 token 재매핑과 인쇄 복귀는 tokens.css 가 담당한다 */
.tile.dark,.tile.black{background:var(--surface);color:var(--ink)}
.wrap{max-width:var(--w);margin:0 auto}

/* ── cover (design.md §3.1) ─────────────────────────────── */
.tile.cover .hero,h1.hero{font-size:clamp(34px,4.6vw,50px);font-weight:600;
 line-height:1.08;letter-spacing:-.028em}
.tile .rule{width:64px;height:1px;background:var(--cover-rule);margin:var(--s-xl) 0}
.tile .meta{font-size:15px;line-height:1.65;color:var(--ink-3)}

/* 종결 표식 (design.md §8) — 표제가 아니라 표식이다 */
.tile .eod{font-size:14px;font-weight:600;letter-spacing:.08em;color:var(--ink-3)}

/* ── sections — 타일이 위계를 나른다. 괘선을 쓰지 않는다 ── */
section{margin:0 auto}
h2{font-size:34px;margin-bottom:26px;display:flex;align-items:baseline;gap:14px}
.tile p{max-width:var(--w)}

@media(max-width:640px){
 .tile{padding:var(--s-xxl) 18px}
 h2{font-size:26px}
}

@media print{
 @page{size:A4 landscape;margin:0}
 .nav{display:none}
 html,body{font-size:11pt;padding:0}
 .tile{height:210mm;padding:14mm 16mm;display:flex;align-items:center;
  page-break-after:always;break-after:page;break-inside:avoid;overflow:hidden}
 .tile:last-child{break-after:auto}
 .wrap{width:100%;max-width:none}
 h1.hero{font-size:34pt} h2{font-size:22pt} h3{font-size:13pt}
 p,li{orphans:3;widows:3}
 table{font-size:9pt} td{padding:7px 6px} th{font-size:8pt}
 table,pre,.note,.warn,.finding,.claim,.quote-box,.rsn,blockquote,
 .katex-display,svg,.figcap,.metric,.gantt{break-inside:avoid}
 svg{break-after:avoid}
 .scroll,.scroll.wide{overflow:visible;margin:14px 0 6px;padding:0}
 pre{font-size:8.5pt;background:var(--surface-2)!important;color:var(--ink)!important}
 .tile .rule{background:var(--rule)}
}
```

`.tile .eod`의 `#8b8b90`은 black surface 의 `--ink-3`과 같은 값이다.

- [ ] **Step 10: template 에 `__TOKENCSS__` 추가**

두 template 모두 `<style>__KATEXCSS__</style>` 다음 줄에 추가한다.

```html
<style>__TOKENCSS__</style>
```

주석 「네 자리 모두 mathbuild.js 가 빌드 시점에 채운다」를 「CSS 자리는 모두 mathbuild.js 가 빌드 시점에 채운다」로 교체한다.

- [ ] **Step 11: `mathbuild.js`의 CSS 삽입 교체**

§5 블록 안 `html = put(html, '__BASECSS__', read('base.css'));` 앞에 추가한다.

```js
  html = put(html, '__TOKENCSS__', read('tokens.css'));
```

바로 아래 잔존 검사 배열을 교체한다.

```js
for (const ph of ['__TOKENCSS__', '__BASECSS__', '__MODECSS__', '__FONTCSS__', '__KATEXCSS__']) {
```

머리 주석 3번 「base.css 와 모드 CSS(paper/deck)를」을 「tokens.css · base.css · 모드 CSS(paper/deck)를」로 교체한다.

- [ ] **Step 12: `qa.py`의 token 검사 교체**

`CHECK_JS`의 `primary:` 줄을 교체한다.

```js
    accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(),
```

`run()`의 대응 검사를 교체한다.

```python
        if r["accent"] != "#0066cc":
            fails.append(f"--accent token 이 걸리지 않았다 (값: {r['accent'] or '없음'}) — CSS 삽입 실패")
```

잔존 marker 목록에 `"__TOKENCSS__"`를 추가한다.

```python
        for marker in ("⟦", "__BODY__", "__TITLE__", "__TOKENCSS__", "__BASECSS__", "__MODECSS__"):
```

- [ ] **Step 13: `figures.py`의 미사용 상수 삭제**

현행 21~28행(`# 팔레트 — …` 주석과 `INK` … `PALE` 7줄)을 삭제한다. `FONT = 'Pretendard'`는 유지한다.
docstring 의 「다크 타일 위에서는 deck.css 가 토큰을 바꾸고」를 「다크 surface 에서는 tokens.css 가 token 을 교체하고」로 교체한다.

- [ ] **Step 14: 기존 test 의 이름과 자리 반영**

`tests/test_consistency.py`:

```python
PLACEHOLDERS = ("__TITLE__", "__BODY__", "__FONTCSS__", "__KATEXCSS__", "__TOKENCSS__",
                "__BASECSS__", "__MODECSS__")
```

`test_figures_palette_matches_css_tokens`를 삭제한다. `figures.py`가 상수를 갖지 않으며,
class 와 CSS 의 연결은 `test_figures_emitted_classes_are_all_defined_in_css`가 이미 검사한다.

`test_mark_pins_its_text_color`를 교체한다. 재정의 금지는 `test_tokens.py`로 이전되었다.

```python
def test_mark_pins_its_text_color():
    """
    `<mark>` 가 글자색을 상속하면 다크 타일에서 노랑 위 흰 글자가 된다.
    typesetting 결과에서 확인한 사고다 — 색을 물려받은 안은 다크에서 읽히지 않았고,
    박아 둔 안만 살아남았다. hex 를 박아 도해가 사라지던 것과 같은 계통이다.
    재정의 금지는 tests/test_tokens.py 가 검사한다.
    """
    tokens = read(CSS / "tokens.css")
    for token in ("--mark:", "--mark-ink:"):
        assert token in tokens, f"tokens.css 에 {token} 토큰이 없다"

    rule = re.search(r"(?<![\w-])mark\{([^}]*)\}", read(CSS / "base.css"))
    assert rule, "base.css 에 mark 규칙이 없다"
    assert "var(--mark-ink)" in rule.group(1), (
        "mark 가 글자색을 고정하지 않는다 — 다크 타일이 --ink 를 흰색으로 뒤집으면 읽히지 않는다"
    )
```

`tests/test_build_e2e.py`의 `leftover` 목록에 `"__TOKENCSS__"`를 추가한다.

`tests/mathbuild.test.js`의 `CSS 네 자리가 모두 채워진다` test 를 교체한다.

```js
test('CSS 자리가 모두 채워진다', () => {
  const r = build('<section><p>본문</p></section>');
  assert.strictEqual(r.status, 0, r.stderr);
  for (const ph of ['__FONTCSS__', '__KATEXCSS__', '__TOKENCSS__', '__BASECSS__', '__MODECSS__']) {
    assert.ok(!r.out.includes(ph), `${ph} 가 남았다`);
  }
  assert.match(r.out, /--accent:#0066cc/, 'tokens.css 가 들어가지 않았다');
});
```

- [ ] **Step 15: 전체 검사 실행**

Run: `npm test && ruff check .`
Expected: 전부 PASS. `test_secondary_text_contrast_is_recorded`는 `--ink-3` 경고를 출력한다.

- [ ] **Step 16: screenshot 동일성 확인**

```bash
python3 examples/build_example.py
for m in paper deck; do node $A/mathbuild.js dist/example_${m}_raw.html dist/example_${m}.html --assets $A; done
python3 scripts/qa.py dist/example_paper.html dist/example_deck.html --shot dist/shots-after
cmp dist/shots-before/example_paper.png dist/shots-after/example_paper.png
cmp dist/shots-before/example_deck.png dist/shots-after/example_deck.png
```

Expected: 두 `cmp` 모두 출력 없이 exit 0. 차이가 있으면 두 이미지를 열어 비교하고, 원인이 된 선언을
찾아 수정한 뒤 이 step 을 반복한다. 인쇄 값의 변경(다크 tile 인쇄 글자색 `#000` → `#1d1d1f`,
인쇄 시 도해 token 복귀)은 screenshot 에 나타나지 않으며 의도한 변경이다.

- [ ] **Step 17: Commit**

```bash
git add scripts/csstokens.py tests/test_tokens.py tests/conftest.py tests/test_consistency.py \
  tests/test_build_e2e.py tests/mathbuild.test.js $A/css $A/*_template.html $A/mathbuild.js $A/qa.py $A/figures.py
git commit -F - <<'EOF'
Move every design value into tokens.css

base.css, paper.css and deck.css now reference role-named tokens
through var() only. Dark-surface remapping and its print reset live in
one place, 1.x aliases keep the old names working, and test_tokens.py
enforces literal placement, definition, print reset and contrast.
Screenshots of both example documents are byte-identical.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
EOF
```

---

### Task 2: 한글 typesetting 규칙

**Files:**
- Modify: `$A/css/base.css`
- Test: `tests/test_tokens.py`

**Interfaces:**
- Consumes: `csstokens.declared` (Task 1)

- [ ] **Step 1: 실패하는 test 추가**

`tests/test_tokens.py` 끝에 추가한다.

```python
def test_korean_typesetting_rules():
    base = COMPONENT["base.css"]
    html = T.declared(base, "html")
    assert html.get("word-break") == "keep-all", "어절 중간에서 줄이 바뀐다"
    assert html.get("overflow-wrap") == "anywhere", "keep-all 과 짝이다 — URL 같은 문자열이 넘친다"
    assert html.get("line-break") == "strict"
    assert T.declared(base, "table").get("font-variant-numeric") == "tabular-nums"
    assert T.declared(base, ".metric .mval").get("font-variant-numeric") == "tabular-nums"
    assert T.declared(base, "h2").get("text-wrap") == "balance"
```

Run: `python3 -m pytest tests/test_tokens.py::test_korean_typesetting_rules -q`
Expected: FAIL — `AssertionError: 어절 중간에서 줄이 바뀐다`

- [ ] **Step 2: 규칙 추가**

`base.css`의 `html{scroll-behavior:smooth}`를 교체한다.

```css
/* 한글 typesetting — 어절 단위로 줄을 바꾼다. overflow-wrap 이 URL 같은
   분절 불가 문자열의 넘침을 방지한다. 둘은 짝이다 */
html{scroll-behavior:smooth;word-break:keep-all;overflow-wrap:anywhere;line-break:strict}
table,.metric .mval,.gantt{font-variant-numeric:tabular-nums}
h1,h2,h3,.hero{text-wrap:balance}
```

- [ ] **Step 3: 검사와 렌더 확인**

```bash
npm test
python3 examples/build_example.py
for m in paper deck; do node $A/mathbuild.js dist/example_${m}_raw.html dist/example_${m}.html --assets $A; done
python3 scripts/qa.py dist/example_paper.html dist/example_deck.html --shot dist/shots-t2
```

Expected: 전부 PASS. `dist/shots-t2/*.png`를 열어 어절 중간 줄바꿈이 없고 표의 숫자 열이 정렬되는지 확인한다.

- [ ] **Step 4: Commit**

```bash
git add $A/css/base.css tests/test_tokens.py
git commit -F - <<'EOF'
Add Korean line breaking, tabular figures and balanced headings

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
EOF
```

---

### Task 3: type scale 과 space token

**Files:**
- Modify: `$A/css/tokens.css`, `$A/css/base.css`, `$A/css/paper.css`, `$A/css/deck.css`
- Test: `tests/test_tokens.py`, `tests/test_consistency.py`

**Interfaces:**
- Produces: `--t-3` … `--t9` · `--lh-3` … `--lh9` · `--tr-3` … `--tr9` (screen px · em, print pt), `--s-1` … `--s-10`

- [ ] **Step 1: 실패하는 test 추가**

`tests/test_tokens.py` 끝에 추가한다.

```python
STEPS = ["-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]


def _px(value: str) -> float:
    assert value.endswith("px"), f"px 값이 아니다: {value}"
    return float(value[:-2])


def test_type_scale_has_every_step():
    missing = [f"--{p}{s}" for s in STEPS for p in ("t", "lh", "tr") if f"--{p}{s}" not in ROOT_T]
    assert not missing, f"type scale 누락: {missing}"


def test_line_heights_and_space_sit_on_the_4px_grid():
    names = [f"--lh{s}" for s in STEPS] + [f"--s-{n}" for n in range(1, 11)]
    off = {n: ROOT_T.get(n) for n in names if n not in ROOT_T or _px(ROOT_T[n]) % 4}
    assert not off, f"4px grid 이탈: {off}"


def test_tracking_tightens_as_size_grows():
    pairs = sorted((_px(ROOT_T[f"--t{s}"]), float(ROOT_T[f"--tr{s}"].removesuffix("em"))) for s in STEPS)
    for (size_a, tr_a), (size_b, tr_b) in zip(pairs, pairs[1:]):
        assert tr_b <= tr_a, f"{size_b}px 의 자간 {tr_b}em 이 {size_a}px 의 {tr_a}em 보다 넓다"


def test_print_scale_is_in_points():
    printed = T.declared(TOKENS, ":root", "@media print")
    bad = [f"--t{s}" for s in STEPS if not printed.get(f"--t{s}", "").endswith("pt")]
    assert not bad, f"인쇄 scale 이 pt 가 아니다: {bad}"


@pytest.mark.parametrize("name", list(COMPONENT))
def test_font_sizes_come_from_the_scale(name):
    """
    font-size 리터럴이 남으면 theme 이 그 자리의 크기를 교체하지 못한다.
    em · % 는 부모 크기에 대한 비율이라 허용한다. gantt 처럼 좌표와 결합된 크기는
    그 component 의 custom property 로 선언한다.
    """
    text = T.strip_comments(COMPONENT[name])
    values = re.findall(r"(?<![\w-])font-size\s*:\s*([^;}]+)", text)
    bad = [v.strip() for v in values
           if "var(--" not in v and not re.fullmatch(r"\s*[\d.]+(em|%)\s*(!important)?\s*", v)]
    assert not bad, f"{name} 의 font-size 리터럴: {bad} — tokens.css 의 --t* 를 참조한다"
```

`tests/test_consistency.py`의 `test_deck_print_keeps_its_own_type_scale`을 교체한다.

```python
def test_deck_print_keeps_its_own_type_scale():
    """deck 인쇄 규칙이 paper 규칙에 덮이지 않는지. 실제로 났던 사고다."""
    deck_print = read(CSS / "deck.css").split("@media print")[1].replace(" ", "")
    assert "height:210mm" in deck_print, "deck 인쇄에 1섹션=1페이지 규칙이 없다"
    assert "--t9:34pt" in deck_print, "deck hero 인쇄 크기 token 이 없다"
    assert "--t6:22pt" in deck_print, \
        "deck h2 는 22pt 여야 한다 — paper 의 인쇄 scale 이 새어 들어왔는지 확인한다"
```

Run: `python3 -m pytest tests/test_tokens.py tests/test_consistency.py -q`
Expected: FAIL — `type scale 누락`, `font-size 리터럴`, `deck hero 인쇄 크기 token 이 없다`

- [ ] **Step 2: `tokens.css`에 scale · space · 인쇄 · 좁은 화면 token 추가**

`:root`의 `/* spacing */` 두 줄을 교체한다.

```css
 /* type scale — 기준 17px / 28px, 비율 1.125, 행간 4px grid.
    자간은 13.5px 이하 0, 15~17px −0.01em, 19px 이상 −0.012em → −0.028em(49px) 선형 */
 --t-3:12px;   --lh-3:16px; --tr-3:0em;
 --t-2:13.5px; --lh-2:20px; --tr-2:0em;
 --t-1:15px;   --lh-1:24px; --tr-1:-.01em;
 --t0:17px;    --lh0:28px;  --tr0:-.01em;
 --t1:19px;    --lh1:28px;  --tr1:-.012em;
 --t2:21.5px;  --lh2:32px;  --tr2:-.013em;
 --t3:24px;    --lh3:32px;  --tr3:-.015em;
 --t4:27px;    --lh4:36px;  --tr4:-.016em;
 --t5:30.5px;  --lh5:40px;  --tr5:-.018em;
 --t6:34.5px;  --lh6:44px;  --tr6:-.020em;
 --t7:38.5px;  --lh7:48px;  --tr7:-.022em;
 --t8:43.5px;  --lh8:52px;  --tr8:-.025em;
 --t9:49px;    --lh9:56px;  --tr9:-.028em;

 /* space — 4px grid */
 --s-1:4px;  --s-2:8px;  --s-3:12px; --s-4:16px; --s-5:24px;
 --s-6:32px; --s-7:48px; --s-8:64px; --s-9:80px; --s-10:96px;
```

alias 블록(`:root,.dark,.black{…}`)의 마지막 줄 뒤에 space alias 를 추가한다.

```css
 --s-xs:var(--s-2); --s-sm:var(--s-3); --s-md:var(--s-4); --s-lg:var(--s-5);
 --s-xl:var(--s-6); --s-xxl:var(--s-7); --s-sec:var(--s-9);
```

`@media print{` 바로 다음, `.dark,.black{` 앞에 인쇄 scale 을 추가한다.

```css
 /* 인쇄 — px × 0.6 을 0.5pt 단위로 반올림 */
 :root{
  --t-3:7pt;   --lh-3:12pt; --t-2:8pt;    --lh-2:12pt; --t-1:9pt;    --lh-1:14pt;
  --t0:10pt;   --lh0:16pt;  --t1:11.5pt;  --lh1:16pt;  --t2:13pt;    --lh2:20pt;
  --t3:14.5pt; --lh3:20pt;  --t4:16pt;    --lh4:24pt;  --t5:18.5pt;  --lh5:24pt;
  --t6:20.5pt; --lh6:28pt;  --t7:23pt;    --lh7:28pt;  --t8:26pt;    --lh8:32pt;
  --t9:29.5pt; --lh9:36pt;
 }
```

파일 끝에 좁은 화면 규칙을 추가한다.

```css
@media(max-width:640px){
 :root{--t0:15px;--lh0:24px}
}
```

- [ ] **Step 3: `base.css` 전체 교체**

```css
/* base.css — paper·deck 공통 레이어
 *
 * 값은 tokens.css 에 있다. 이 파일은 var() 로만 참조한다 — 색 리터럴과
 * font-size 리터럴은 tests/test_tokens.py 가 차단한다.
 * 모드별 크롬(.doc / .tile)과 @media print 는 paper.css · deck.css 가 담당한다.
 * 공통 규칙을 모드 파일에 복사하지 않는다 — 그 중복이 deck 인쇄 규칙이
 * paper 규칙에 덮이는 사고를 만들었다.
 */

*{box-sizing:border-box;margin:0;padding:0}
/* 한글 typesetting — 어절 단위로 줄을 바꾼다. overflow-wrap 이 URL 같은
   분절 불가 문자열의 넘침을 방지한다. 둘은 짝이다 */
html{scroll-behavior:smooth;word-break:keep-all;overflow-wrap:anywhere;line-break:strict}
table,.metric .mval,.gantt{font-variant-numeric:tabular-nums}
h1,h2,h3,.hero{text-wrap:balance}
body{font-family:var(--font-body);color:var(--ink);background:var(--surface);
 font-size:var(--t0);line-height:var(--lh0);letter-spacing:var(--tr0);-webkit-font-smoothing:antialiased}

/* ── typography ─────────────────────────────────────────── */
/* h2 의 크기는 모드가 정한다 — paper t4 · deck t6 */
h2{font-weight:600}
h3{font-size:var(--t3);line-height:var(--lh3);letter-spacing:var(--tr3);font-weight:600;
 margin:var(--s-6) 0 var(--s-3)}
h4{font-size:var(--t1);line-height:var(--lh1);letter-spacing:var(--tr1);font-weight:600;
 margin-bottom:var(--s-2)}
p{margin-bottom:var(--s-4)}
b{font-weight:600}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--rule);
 border-bottom-color:color-mix(in srgb,var(--accent) 26%,transparent)}
a:hover{border-bottom-color:var(--accent)}
code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);
 padding:1px 5px;border-radius:5px;letter-spacing:0}

/* ── 강조 (design.md §4.7) ──────────────────────────────── */
/* 글자색을 --mark-ink 로 박는다. 상속에 맡기면 다크 타일이 --ink 를 흰색으로
   뒤집어 노랑 위 흰 글자가 된다 — typesetting 결과에서 확인한 사고다.
   좌우 여백을 em 으로 두어야 강조 뒤의 구두점이 벌어지지 않는다. */
mark{background:var(--mark);color:var(--mark-ink);
 padding:1px .16em;border-radius:3px}

/* Pretendard 에 italic 자족이 없다. 한글에 걸면 브라우저가 합성한 oblique 이
   나오고 획이 어긋난다. 라틴이라고 밝힌 자리에만 건다 — 변수·학명이 그 자리다.
   밝히지 않으면 아무 일도 일어나지 않는다. 기울어진 한글보다 낫다. */
i,em{font-style:normal}
i[lang="en"],em[lang="en"]{font-style:italic}
.eyebrow{font-size:var(--t-2);line-height:var(--lh-2);font-weight:600;letter-spacing:0;
 color:var(--accent);margin-bottom:var(--s-3)}
.sn{font-size:var(--t-1);font-weight:600;color:var(--accent);flex:none;min-width:20px}
.legend{display:flex;flex-wrap:wrap;gap:var(--s-2) var(--s-5);margin:var(--s-5) 0 var(--s-3);
 font-size:var(--t-2);line-height:var(--lh-2);color:var(--ink-3)}
.srcline{font-size:var(--t-2);line-height:var(--lh-2);color:var(--ink-3);padding-top:var(--s-3);
 border-top:1px solid var(--rule-soft)}

/* ── status badges ──────────────────────────────────────── */
.bdg{display:inline-block;font-size:var(--t-3);line-height:var(--lh-3);font-weight:600;letter-spacing:0;
 padding:1px 7px;border-radius:var(--r-pill);vertical-align:1.5px;white-space:nowrap}
.bdg.meas{background:var(--accent);color:var(--on-accent)}
.bdg.impl{color:var(--accent);border:1px solid var(--accent);
 border-color:color-mix(in srgb,var(--accent) 50%,transparent)}
.bdg.none{color:var(--ink-3);border:1px dashed var(--ink-3)}
.bdg.no{color:var(--ink-3);border:1px solid var(--ink-3)}

/* ── figures ────────────────────────────────────────────── */
.fig{width:100%;height:auto;display:block;margin:var(--s-5) 0 var(--s-2)}
.fig.narrow{max-width:560px;margin-left:auto;margin-right:auto}
.figcap{font-size:var(--t-2);line-height:var(--lh-2);letter-spacing:var(--tr-2);color:var(--ink-3);
 text-align:center;margin:var(--s-2) 0 var(--s-5)}
.plate{display:block;max-width:820px;margin:var(--s-5) auto var(--s-2);width:100%;height:auto;
 border:1px solid var(--rule);border-radius:10px}

/* 도해 색 token — figures.py 가 hex 대신 이 class 를 방출한다.
   덕분에 다크 surface 에서 token 만 바뀌면 도해가 따라온다. */
svg.fig{fill:var(--ink)}
svg.fig .fi-ink{fill:var(--ink)}
svg.fig .fi-ink48{fill:var(--ink-3)}
svg.fig .fi-pri{fill:var(--accent)}
svg.fig .fi-mid{fill:var(--fig-mid)}
svg.fig .fi-line{fill:var(--fig-line)}
svg.fig .fi-soft{fill:var(--fig-soft)}
svg.fig .fi-pale{fill:var(--fig-pale)}
svg.fig .fi-canvas{fill:var(--surface)}
svg.fig .fi-oncard{fill:var(--surface)}   /* 잉크 헤더 바 위의 글자 */
svg.fig .fi-none{fill:none}
svg.fig .st-ink{stroke:var(--ink)}
svg.fig .st-ink48{stroke:var(--ink-3)}
svg.fig .st-pri{stroke:var(--accent)}
svg.fig .st-mid{stroke:var(--fig-mid)}
svg.fig .st-line{stroke:var(--fig-line)}

/* ── gantt (figures.py fig_gantt 가 emit 하는 구조) ──────── */
/* 글자 크기는 막대 · marker 좌표와 짝이라 type scale 을 따르지 않는다.
   figures.py 의 SVG label 크기를 유지하는 것과 같은 이유다.
   트랙 원점은 라벨 폭 + 라벨·트랙 gap 이다. 둘 중 하나만 더하면 마커가 막대와 어긋난다. */
.gantt{--glabel-w:132px;--gtrack-x:calc(var(--glabel-w) + var(--s-3));
 --g-label:12.5px;--g-mark:10.5px;
 position:relative;margin:var(--s-5) 0 var(--s-2);padding:22px 0 26px}
.gantt .gmarks{position:absolute;left:var(--gtrack-x);right:0;top:22px;bottom:26px;pointer-events:none}
.gantt .gmark{position:absolute;top:0;bottom:0;width:0;border-left:1.4px solid var(--ink)}
.gantt .gmark.meet{border-left-style:solid}
.gantt .gmark.gate{border-left-style:dashed;border-left-color:var(--ink-3)}
.gantt .gmark.pilot{border-left-style:dotted;border-left-color:var(--accent)}
.gantt .gmark span{position:absolute;top:-19px;left:5px;font-size:var(--g-mark);
 font-weight:600;color:var(--ink);white-space:nowrap}
.gantt .gmark.gate span{color:var(--ink-3)}
.gantt .gmark.pilot span{color:var(--accent)}
.gantt .grow{display:flex;align-items:center;gap:var(--s-3);margin-bottom:7px}
.gantt .glabel{flex:0 0 var(--glabel-w);font-size:var(--g-label);color:var(--ink-2);
 text-align:right;letter-spacing:-.18px}
.gantt .gtrack{position:relative;flex:1;height:19px;background:var(--rule-soft);border-radius:4px}
/* 막대 색은 kind 가 정한다. 인라인 style 은 위치만 나른다 — figures.py 와 짝이다. */
.gantt .gbar{position:absolute;top:0;height:19px;border-radius:4px;min-width:2px}
.gantt .gbar.done{background:var(--fig-soft)}
.gantt .gbar.wbs{background:var(--fig-mid)}
.gantt .gbar.key{background:var(--ink)}
.gantt .gbar.plan{background:transparent;border:1.5px dashed var(--accent)}
.gantt .gaxis{position:relative;height:18px;margin-left:var(--gtrack-x);
 border-top:1px solid var(--rule)}
.gantt .gline{position:absolute;top:0;width:0;border-left:1px solid var(--rule);height:5px}
.gantt .gline span{position:absolute;top:6px;left:3px;font-size:var(--g-mark);color:var(--ink-3);
 white-space:nowrap}

/* ── metric cards (design.md §4.4) ──────────────────────── */
.metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--s-4);margin:var(--s-5) 0}
.metric{border:1px solid var(--rule);border-radius:var(--r-lg);padding:var(--s-6)}
.metric .mlabel{font-size:var(--t-1);line-height:var(--lh-1);color:var(--ink-3)}
.metric .mval{font-size:clamp(var(--t5),3.6vw,var(--t8));font-weight:600;
 letter-spacing:var(--tr8);line-height:1.05;margin:var(--s-2) 0}
.metric .mnote{font-size:var(--t-1);line-height:var(--lh-1);color:var(--ink-3)}
.metric.gap{background:var(--surface-3);border-style:dashed}
.metric.gap .mval{color:var(--ink-3)}

/* ── tables ─────────────────────────────────────────────── */
table{width:100%;border-collapse:collapse;margin:var(--s-5) 0 var(--s-2);
 font-size:var(--t-1);line-height:var(--lh-1);letter-spacing:var(--tr-1)}
th{text-align:left;font-size:var(--t-2);line-height:var(--lh-2);font-weight:600;color:var(--ink-3);
 padding:0 10px 9px;border-bottom:1px solid var(--rule-heavy);white-space:nowrap}
td{padding:11px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
td:first-child,th:first-child{padding-left:0}
td:last-child,th:last-child{padding-right:0}
tr.hl td{background:var(--surface-3);background:color-mix(in srgb,var(--accent) 4.5%,transparent)}
table.num td:not(:first-child),table.num th:not(:first-child){text-align:right;white-space:nowrap}
table.num td .katex{font-size:.94em}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.scroll.wide{margin:var(--s-5) calc(-1 * var(--s-5)) var(--s-2);padding:0 var(--s-5)}
.scroll.wide table{margin-top:0}
.scroll.wide::-webkit-scrollbar{height:6px}
.scroll.wide::-webkit-scrollbar-thumb{background:var(--scroll-thumb);border-radius:3px}

/* ── callouts ───────────────────────────────────────────── */
.note,.warn,.finding,.claim{border-radius:var(--r-md);padding:18px 22px;margin:var(--s-5) 0}
.note{background:var(--surface-3);border:1px solid var(--rule-soft)}
.warn{background:var(--surface);border:1px solid var(--rule);border-left:3px solid var(--rule-heavy)}
.finding{background:var(--surface);border:1px solid var(--accent);
 border-color:color-mix(in srgb,var(--accent) 30%,transparent);border-left:3px solid var(--accent)}
.claim{background:var(--surface-2);border:0;font-size:var(--t0);line-height:var(--lh0)}
.note p:last-child,.warn p:last-child,.finding p:last-child,.claim p:last-child{margin-bottom:0}
.note p,.warn p,.finding p{font-size:var(--t-1);line-height:var(--lh-1);color:var(--ink-2)}
.cav{font-size:var(--t-2)!important;line-height:var(--lh-2);color:var(--ink-3)!important;padding-top:10px;
 border-top:1px solid var(--rule-soft);margin-top:var(--s-3)!important}
blockquote{margin:var(--s-3) 0;padding:var(--s-3) 18px;background:var(--surface-2);
 border-radius:var(--r-sm);font-size:var(--t-1);line-height:var(--lh-1);color:var(--ink-2)}
.quote-box{border:1px solid var(--rule);border-radius:var(--r-md);padding:22px 26px;margin:var(--s-5) 0}
.quote-box p{font-size:var(--t0);line-height:var(--lh0);margin:0}
.rsn{border:1px solid var(--rule);border-radius:var(--r-md);padding:18px 20px;margin-bottom:var(--s-3)}
.rsn-no{font-size:var(--t-3);line-height:var(--lh-3);font-weight:600;color:var(--accent);margin-bottom:5px}
.rsn p{font-size:var(--t-1);line-height:var(--lh-1);color:var(--ink-2);margin:4px 0 0}

/* ── lists ──────────────────────────────────────────────── */
ul.plain,ol.concl{margin:var(--s-4) 0 var(--s-2);padding:0;list-style:none;counter-reset:c}
ul.plain li,ol.concl li{font-size:var(--t-1);line-height:var(--lh-1);color:var(--ink-2);
 padding:11px 0 11px 30px;position:relative;border-top:1px solid var(--rule)}
ul.plain li:last-child,ol.concl li:last-child{border-bottom:1px solid var(--rule)}
/* 점의 top = 위 padding 11 + 행간 24 / 2 − 점 반지름 2.5 */
ul.plain li::before{content:"";position:absolute;left:var(--s-2);top:20px;width:5px;height:5px;
 border-radius:50%;background:var(--accent)}
ol.concl li{counter-increment:c}
ol.concl li::before{content:counter(c);position:absolute;left:0;top:11px;
 font-size:var(--t-2);line-height:var(--lh-1);font-weight:600;color:var(--accent)}

/* ── code ───────────────────────────────────────────────── */
pre{margin:var(--s-5) 0;background:var(--code-bg);color:var(--code-ink);border-radius:var(--r-md);
 padding:var(--s-5);overflow-x:auto;font-family:var(--mono);
 font-size:var(--t-2);line-height:var(--lh-1);letter-spacing:0}
pre .c{color:var(--code-dim)}

/* ── katex ──────────────────────────────────────────────── */
.katex-display{margin:var(--s-5) 0;overflow-x:auto;overflow-y:hidden;padding:2px 0}
.katex{font-size:1.02em}

/* 좁은 화면의 본문 크기는 tokens.css 가 --t0 으로 정한다 */
@media(max-width:640px){
 table{font-size:var(--t-2);line-height:var(--lh-2)} td{padding:9px 6px} th{padding:0 6px 7px}
 .katex-display{font-size:.92em}
 .metrics{grid-template-columns:1fr}
 .gantt{--glabel-w:92px}
}

/* 인쇄 시 배경을 지우지 않게 한다. 두 모드 모두에 필요하다. */
@media print{ *{-webkit-print-color-adjust:exact;print-color-adjust:exact} }
```

- [ ] **Step 4: `paper.css` 전체 교체**

```css
/* paper.css — 세로·연속 흐름 모드
 * base.css 위에만 얹는다. 공통 규칙을 여기에 다시 쓰지 않는다.
 * 인쇄 크기는 tokens.css 의 인쇄 scale 이 정한다. 여기에는 쪽 나눔과 여백만 둔다.
 */

:root{ --w:720px }

body{padding:0 var(--s-5) 120px}
.doc{max-width:var(--w);margin:0 auto}

/* masthead */
.paper-head{max-width:var(--w);margin:0 auto;padding:var(--s-10) 0 var(--s-7);
 border-bottom:1px solid var(--rule-heavy)}
.paper-head h1{font-size:clamp(var(--t5),4.4vw,var(--t8));font-weight:600;line-height:1.2;
 letter-spacing:var(--tr8)}
.subtitle{font-size:var(--t1);line-height:var(--lh1);letter-spacing:var(--tr1);color:var(--ink-3);
 margin-top:var(--s-3)}
.byline{display:flex;gap:var(--s-5);margin-top:var(--s-5);font-size:var(--t-1);line-height:var(--lh-1);
 color:var(--ink-3)}
.byline span+span::before{content:"·";margin-right:var(--s-5)}

/* abstract */
.abstract{max-width:var(--w);margin:0 auto;padding:var(--s-6) 0 var(--s-2);border-bottom:1px solid var(--rule)}
.abstract h2{font-size:var(--t-2);line-height:var(--lh-2);font-weight:600;letter-spacing:.06em;
 color:var(--ink-3);text-transform:uppercase;margin-bottom:var(--s-3);border:0;padding:0}
.abstract p{font-size:var(--t0);line-height:var(--lh0);color:var(--ink-2);margin-bottom:var(--s-3)}

/* sections — 괘선과 번호가 위계를 나른다 */
section{max-width:var(--w);margin:0 auto;padding-top:var(--s-8)}
h2{font-size:var(--t4);line-height:var(--lh4);letter-spacing:var(--tr4);padding-bottom:var(--s-3);
 border-bottom:1px solid var(--rule-heavy);margin-bottom:var(--s-5);display:flex;align-items:baseline;
 gap:14px}

footer.eod{max-width:var(--w);margin:var(--s-9) auto 0;padding-top:var(--s-5);
 border-top:1px solid var(--rule);font-size:var(--t-3);line-height:var(--lh-3);letter-spacing:.08em;
 color:var(--ink-3)}

@media(max-width:640px){
 body{padding:0 18px 80px}
 .paper-head{padding-top:56px}
}

@media print{
 @page{size:A4;margin:18mm 16mm}
 body{padding:0}
 .doc,section,.paper-head,.abstract,footer.eod{max-width:none}
 .paper-head{padding-top:0}
 section{padding-top:22px;break-inside:auto}
 h2,h3,h4{break-after:avoid}
 p,li{orphans:3;widows:3}
 table,pre,.note,.warn,.finding,.claim,.quote-box,.rsn,blockquote,
 .katex-display,svg,.figcap,.metric,.gantt{break-inside:avoid}
 svg{break-after:avoid}
 table{margin:14px 0 6px} td{padding:6px 5px} th{padding:0 5px 5px}
 .scroll,.scroll.wide{overflow:visible;margin:14px 0 6px;padding:0}
 .scroll.wide table,.scroll.wide th{font-size:var(--t-3)}
 .scroll.wide td{padding:5px 4px} .scroll.wide th{padding:0 4px 4px}
 pre{background:var(--surface-2)!important;color:var(--ink)!important;padding:var(--s-3) var(--s-4)}
 .bdg{padding:0 5px}
 .figcap{margin-bottom:16px}
}
```

- [ ] **Step 5: `deck.css` 전체 교체**

```css
/* deck.css — 가로·1섹션 1페이지 모드
 * base.css 위에만 얹는다. 공통 규칙을 여기에 다시 쓰지 않는다.
 *
 * 타일은 full-bleed 다. body 에 좌우 패딩을 주지 않는다 —
 * 패딩은 .tile 이 가지고, 폭 제한은 .wrap 이 한다.
 */

:root{ --w:1120px }

body{padding:0}

/* ── tiles ──────────────────────────────────────────────── */
.tile{padding:var(--s-9) var(--s-5)}
.tile.light{background:var(--surface)}
.tile.parch{background:var(--surface-2)}
/* dark · black 의 token 재매핑과 인쇄 복귀는 tokens.css 가 담당한다 */
.tile.dark,.tile.black{background:var(--surface);color:var(--ink)}
.wrap{max-width:var(--w);margin:0 auto}

/* ── cover (design.md §3.1) ─────────────────────────────── */
.tile.cover .hero,h1.hero{font-size:clamp(var(--t6),4.6vw,var(--t9));font-weight:600;
 line-height:1.14;letter-spacing:var(--tr9)}
.tile .rule{width:64px;height:1px;background:var(--cover-rule);margin:var(--s-6) 0}
.tile .meta{font-size:var(--t-1);line-height:var(--lh-1);color:var(--ink-3)}

/* 종결 표식 (design.md §8) — 표제가 아니라 표식이다 */
.tile .eod{font-size:var(--t-2);line-height:var(--lh-2);font-weight:600;letter-spacing:.08em;
 color:var(--ink-3)}

/* ── sections — 타일이 위계를 나른다. 괘선을 쓰지 않는다 ── */
section{margin:0 auto}
h2{font-size:var(--t6);line-height:var(--lh6);letter-spacing:var(--tr6);margin-bottom:var(--s-5);
 display:flex;align-items:baseline;gap:14px}
.tile p{max-width:var(--w)}

@media(max-width:640px){
 .tile{padding:var(--s-7) 18px}
 h2{font-size:var(--t4);line-height:var(--lh4)}
}

@media print{
 /* deck 은 가로 A4 라 paper 보다 큰 인쇄 scale 을 쓴다. paper 의 인쇄 scale 이
    새어 들어오면 h2 가 20.5pt 로 줄어든다 — 모드 CSS 가 섞이던 때 실제로 났던 사고다 */
 :root{--t0:11pt;--lh0:18pt;--t6:22pt;--lh6:28pt;--t9:34pt;--lh9:40pt}
 @page{size:A4 landscape;margin:0}
 .nav{display:none}
 html,body{padding:0}
 .tile{height:210mm;padding:14mm 16mm;display:flex;align-items:center;
  page-break-after:always;break-after:page;break-inside:avoid;overflow:hidden}
 .tile:last-child{break-after:auto}
 .wrap{width:100%;max-width:none}
 p,li{orphans:3;widows:3}
 td{padding:7px 6px}
 table,pre,.note,.warn,.finding,.claim,.quote-box,.rsn,blockquote,
 .katex-display,svg,.figcap,.metric,.gantt{break-inside:avoid}
 svg{break-after:avoid}
 .scroll,.scroll.wide{overflow:visible;margin:14px 0 6px;padding:0}
 pre{background:var(--surface-2)!important;color:var(--ink)!important}
 .tile .rule{background:var(--rule)}
}
```

`tokens.css`의 `:root{--s-xs…}` 원래 줄이 Step 2 에서 삭제되었는지 확인한다. `--s-md`는 alias 로만 남고 값은 16px 이다.

- [ ] **Step 6: 검사 실행**

Run: `npm test && ruff check .`
Expected: 전부 PASS

- [ ] **Step 7: 렌더 확인**

```bash
python3 examples/build_example.py
for m in paper deck; do node $A/mathbuild.js dist/example_${m}_raw.html dist/example_${m}.html --assets $A; done
python3 scripts/qa.py dist/example_paper.html dist/example_deck.html --pdf --shot dist/shots-t3
```

Expected: FAIL 없음. screenshot 과 PDF 를 열어 다음을 확인한다. macOS 에서는
`qlmanage -t -s 1400 -o dist/shots-t3 dist/example_paper.pdf`로 PDF 첫 쪽을 PNG 로 변환하여 볼 수 있다.

- h3(24px)가 h2(27px)와 구분되는지
- deck 인쇄에서 타일이 한 쪽에 들어가는지(`qa.py`가 넘침을 실패로 보고한다)
- gantt 라벨과 막대가 어긋나지 않는지

- [ ] **Step 8: Commit**

```bash
git add $A/css tests/test_tokens.py tests/test_consistency.py
git commit -F - <<'EOF'
Adopt a 13-step type scale and a 4px spacing grid

Body text moves to 17/28px with a 1.125 ratio and tracking that
tightens monotonically with size. Print sizes are token overrides in
points, so per-rule pt values are gone; deck keeps its larger print
scale by overriding three steps. Gantt label sizes stay tied to its
geometry as component-local properties.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
EOF
```

---

### Task 4: Pretendard 동봉과 기본 내장

**Files:**
- Create: `$A/fonts/Pretendard-Regular.subset.woff2`, `$A/fonts/Pretendard-SemiBold.subset.woff2`, `$A/fonts/Pretendard-Light.subset.woff2`, `$A/fonts/LICENSE.txt`, `$A/fonts/subset_glyphs.txt`, `tests/test_fonts.py`
- Modify: `$A/mathbuild.js`, `tests/mathbuild.test.js`, `.gitignore`, `scripts/package-smoke.js`

**Interfaces:**
- Produces: `mathbuild.js`가 `--font` 없이 `<assets>/fonts/`의 Regular(400) · SemiBold(600)를 내장한다. Light 는 동봉만 하고 ②단계 theme 이 사용한다

- [ ] **Step 1: 공식 파일 수령**

```bash
F=plugins/korean-report/skills/korean-report-doc/assets/fonts
B=https://cdn.jsdelivr.net/npm/pretendard@1.3.9
mkdir -p $F
for w in Regular SemiBold Light; do
  curl -sfL -o $F/Pretendard-$w.subset.woff2 $B/dist/web/static/woff2-subset/Pretendard-$w.subset.woff2
done
curl -sfL -o $F/LICENSE.txt $B/dist/LICENSE.txt
curl -sfL -o $F/subset_glyphs.txt $B/subset_glyphs.txt
shasum -a 256 $F/*.woff2
```

Expected:

```
5486efe3cef8e887da8af6c07b48b4a78e18afa63d00894fde383eda44103a0b  …/Pretendard-Light.subset.woff2
01dd73155fdfab7ce9b25224523e85a96927e21aef97f21957d41f1bfa7e3878  …/Pretendard-Regular.subset.woff2
4247dc5e260b92640c2cbd0e75091154647b71e1d5884116655e2903468c54cc  …/Pretendard-SemiBold.subset.woff2
```

hash 가 다르면 중단하고 사용자에게 보고한다.

- [ ] **Step 2: `.gitignore` 예외 추가**

`# 폰트 — 저장소에 담지 않는다 (INSTALL.md 절차로 받는다)` 블록을 교체한다.

```gitignore
# 폰트 — 저장소에 담지 않는다. 예외는 스킬이 동봉하는 Pretendard 공식 subset 이다
*.woff2
*.woff
*.ttf
*.otf
!plugins/korean-report/skills/korean-report-doc/assets/fonts/*.woff2
```

Run: `git status --short plugins/korean-report/skills/korean-report-doc/assets/fonts`
Expected: woff2 3개 · `LICENSE.txt` · `subset_glyphs.txt`가 `??`로 표시된다

- [ ] **Step 3: 실패하는 test 작성**

`tests/test_fonts.py`:

```python
# -*- coding: utf-8 -*-
"""
동봉 font 가 공식 배포본 그대로인지 검사한다.

Pretendard 의 OFL 은 Reserved Font Name 을 선언한다. 변경한 파일은 Pretendard 라는
이름을 쓸 수 없으므로, 저장소가 subset 을 직접 생성하거나 최적화하면 안 된다.
"""
import hashlib

import pytest
from conftest import ASSETS, read

FONTS = ASSETS / "fonts"
OFFICIAL = {  # pretendard@1.3.9 dist/web/static/woff2-subset/
    "Pretendard-Regular.subset.woff2": "01dd73155fdfab7ce9b25224523e85a96927e21aef97f21957d41f1bfa7e3878",
    "Pretendard-SemiBold.subset.woff2": "4247dc5e260b92640c2cbd0e75091154647b71e1d5884116655e2903468c54cc",
    "Pretendard-Light.subset.woff2": "5486efe3cef8e887da8af6c07b48b4a78e18afa63d00894fde383eda44103a0b",
}


@pytest.mark.parametrize("name,digest", OFFICIAL.items())
def test_bundled_font_is_the_official_file(name, digest):
    assert hashlib.sha256((FONTS / name).read_bytes()).hexdigest() == digest, \
        f"{name} 이 공식 배포본과 다르다 — Reserved Font Name 조항상 변경본은 이 이름을 쓸 수 없다"


def test_font_license_travels_with_the_fonts():
    text = read(FONTS / "LICENSE.txt")
    assert "Reserved Font Name Pretendard" in text
    assert "SIL Open Font License" in text


def test_glyph_list_covers_ks_x_1001():
    """subset 밖 한글 경고가 이 목록에 의존한다. 목록이 비면 경고가 전부 사라진다."""
    hangul = {c for c in read(FONTS / "subset_glyphs.txt") if 0xAC00 <= ord(c) <= 0xD7A3}
    assert len(hangul) >= 2350
```

`tests/mathbuild.test.js`에서 `폰트를 주지 않으면 경고만 하고 통과한다`와 `내장한 글꼴의 라이선스를 문서가 스스로 고지한다`를 삭제하고 다음을 추가한다.

```js
test('--font 가 없으면 동봉 Pretendard 를 내장한다', () => {
  const r = build('<section><p>x</p></section>');
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.out, /@font-face\{font-family:'Pretendard';font-style:normal;font-weight:400/);
  assert.match(r.out, /font-weight:600/);
  assert.ok(!(r.stderr + r.stdout).includes('Pretendard 미내장'));
  assert.match(r.out, /Pretendard 본문 글꼴 — SIL Open Font License 1\.1/);
});

test('동봉 font 가 없는 assets 이면 경고만 하고 통과한다', () => {
  const d = tmpdir();
  const assets = path.join(d, 'assets');
  fs.cpSync(ASSETS, assets, { recursive: true });
  fs.rmSync(path.join(assets, 'fonts'), { recursive: true });
  const inFile = path.join(d, 'raw.html');
  fs.writeFileSync(inFile, template('paper').replace('__BODY__', '<p>x</p>').replace('__TITLE__', 'T'));
  const r = spawnSync(process.execPath, [BUILD, inFile, path.join(d, 'out.html'), '--assets', assets],
                      { encoding: 'utf8' });
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.stderr + r.stdout, /Pretendard 미내장/);
});

test('subset 밖의 한글은 경고한다', () => {
  const r = build('<section><p>갃 은 KS X 1001 밖의 음절이다</p></section>');
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.stderr + r.stdout, /subset 에 없는 한글 1자.*갃/);
});

test('파일명의 .subset 을 굵기로 오인하지 않는다', () => {
  const d = tmpdir();
  const fake = path.join(d, 'Pretendard-SemiBold.subset.woff2');
  fs.writeFileSync(fake, Buffer.from('wOF2fake-payload'));
  const r = build('<section><p>x</p></section>', { args: ['--font', fake] });
  assert.strictEqual(r.status, 0, r.stderr);
  assert.match(r.out, /font-weight:600/);
});
```

Run: `npm run test:node && python3 -m pytest tests/test_fonts.py -q`
Expected: node test 3건 FAIL(`Pretendard 미내장` 경고 · 경고 부재 · weight 400), pytest PASS

- [ ] **Step 4: `mathbuild.js` 수정**

§4 블록 머리를 교체한다. `const WEIGHTS = …` 앞에 추가한다.

```js
// ── 4. 본문 폰트 (Pretendard) 내장 ─────────────────────────
// --font 가 없으면 스킬이 동봉한 공식 subset 을 내장한다. 공식 파일을 변경 없이 쓴다 —
// Pretendard 의 OFL 은 Reserved Font Name 을 선언하므로 직접 만든 subset 은 그 이름을 쓸 수 없다.
const FONT_DIR = path.join(assetsDir, 'fonts');
const BUNDLED = [['Pretendard-Regular.subset.woff2', 400], ['Pretendard-SemiBold.subset.woff2', 600]];
const usingBundled = !fonts.length;
if (usingBundled) {
  for (const [file, weight] of BUNDLED) {
    const p = path.join(FONT_DIR, file);
    if (fs.existsSync(p)) fonts.push(`${p}:${weight}`);
  }
}
```

weight 추출 줄을 교체한다. `Regular.subset`의 `.subset`이 weight 이름으로 읽히면 400 으로 떨어진다.

```js
    const suffix = (stem.split('-')[1] || 'Regular').split('.')[0].toLowerCase();
```

`console.log(\`본문 폰트 — 내장 …\`)` 줄 다음에 subset 범위 검사를 추가한다.

```js
  // subset 밖의 한글 음절은 system font 로 표시된다. 실패로 처리하지 않고 알린다.
  const glyphFile = path.join(FONT_DIR, 'subset_glyphs.txt');
  if (usingBundled && fs.existsSync(glyphFile)) {
    const covered = new Set(fs.readFileSync(glyphFile, 'utf8'));
    const text = html.replace(/<style[\s\S]*?<\/style>|<[^>]+>/g, '');
    const missing = [...new Set(text.match(/[가-힣]/g) || [])].filter(c => !covered.has(c));
    if (missing.length) {
      warn.push(`Pretendard subset 에 없는 한글 ${missing.length}자 — system font 로 표시된다: ` +
                missing.slice(0, 10).join(''));
    }
  }
```

`else` 경고 문구를 교체한다.

```js
  warn.push('Pretendard 미내장 — assets/fonts/ 가 없다. 시스템 폰트로 폴백하며 기기마다 ' +
            'typesetting 결과가 달라진다. --font 로 woff2 를 지정한다.');
```

머리 주석 4번을 「동봉 Pretendard subset 을(또는 --font 로 준 woff2 를) @font-face 로 내장한다」로 교체한다.

- [ ] **Step 5: 배포 목록에 font 추가**

`scripts/package-smoke.js`의 `required` 배열에서 `figures.py` 줄 다음에 추가한다.

```js
  'plugins/korean-report/skills/korean-report-doc/assets/fonts/Pretendard-Regular.subset.woff2',
  'plugins/korean-report/skills/korean-report-doc/assets/fonts/Pretendard-SemiBold.subset.woff2',
  'plugins/korean-report/skills/korean-report-doc/assets/fonts/LICENSE.txt',
  'plugins/korean-report/skills/korean-report-doc/assets/fonts/subset_glyphs.txt',
```

- [ ] **Step 6: 검사 실행**

Run: `npm test && ruff check .`
Expected: 전부 PASS

- [ ] **Step 7: 크기 실측**

```bash
du -sh plugins/korean-report
python3 examples/build_example.py
for m in paper deck; do node $A/mathbuild.js dist/example_${m}_raw.html dist/example_${m}.html --assets $A; done
ls -l dist/example_paper.html dist/example_deck.html
python3 scripts/qa.py dist/example_paper.html dist/example_deck.html --shot dist/shots-t4
```

Expected: 빌드 log 에 `본문 폰트 — 내장 2`. plugin 크기와 두 HTML 크기를 기록해 두고 Task 7 의 CHANGELOG 에 기재한다.
screenshot 에서 본문이 Pretendard 로 렌더되는지 확인한다.

- [ ] **Step 8: Commit**

```bash
git add .gitignore $A/fonts $A/mathbuild.js tests/test_fonts.py tests/mathbuild.test.js scripts/package-smoke.js
git commit -F - <<'EOF'
Bundle the official Pretendard subset and embed it by default

The three woff2 files are pretendard@1.3.9 as published; the font
declares a Reserved Font Name, so a subset we cut ourselves could not
be called Pretendard. test_fonts.py pins their hashes. mathbuild.js
embeds Regular and SemiBold when --font is absent, warns about Hangul
syllables outside the subset, and no longer reads ".subset" as a
weight name.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
EOF
```

---

### Task 5: paper PDF running footer

**Files:**
- Modify: `$A/qa.py`
- Test: `tests/test_qa_pdf.py`

**Interfaces:**
- Produces: `qa.footer_template(title: str) -> str`

명세 §4.5 는 날짜도 인쇄하도록 정하였다. 현행 template 과 generator 에는 문서 날짜를 담는 자리가 없다.
이 task 는 제목과 쪽번호만 인쇄한다. 날짜는 ③ 장르 단계에서 masthead 의 날짜 자리가 정해질 때 추가한다.

- [ ] **Step 1: 실패하는 test 작성**

`tests/test_qa_pdf.py`:

```python
# -*- coding: utf-8 -*-
"""paper PDF 는 쪽 하단에 제목과 쪽번호를 인쇄한다. deck 은 full-bleed 라 인쇄하지 않는다."""
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
    assert "1 / " in text and "2 / " in text
```

Run: `python3 -m pytest tests/test_qa_pdf.py -q`
Expected: FAIL — `AttributeError: module 'qa' has no attribute 'footer_template'`

- [ ] **Step 2: `qa.py` 수정**

`import argparse` 다음에 `import html`을 추가한다(알파벳 순서). `CHECK_JS` 정의 다음에 추가한다.

```python
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
```

`if pdf:` 블록을 교체한다.

```python
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
```

- [ ] **Step 3: 검사 실행**

Run: `python3 -m pytest tests/test_qa_pdf.py tests/test_build_e2e.py -q && ruff check .`
Expected: PASS. `pdftotext`가 없는 환경에서는 e2e 1건이 skip 된다.

- [ ] **Step 4: PDF 육안 확인**

```bash
python3 scripts/qa.py dist/example_paper.html --pdf
qlmanage -t -s 1400 -o dist/shots-t5 dist/example_paper.pdf
```

Expected: 첫 쪽 하단 왼쪽에 제목, 오른쪽에 `1 / N`. 본문과 footer 가 겹치지 않는다.

- [ ] **Step 5: Commit**

```bash
git add $A/qa.py tests/test_qa_pdf.py
git commit -F - <<'EOF'
Print the title and page numbers at the foot of paper PDFs

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
EOF
```

---

### Task 6: styleguide 와 CI

**Files:**
- Create: `examples/build_styleguide.py`
- Modify: `tests/test_build_e2e.py`, `.github/workflows/ci.yml`, `package.json`

**Interfaces:**
- Consumes: `csstokens.declared`, `csstokens.contrast` (Task 1), `figures.*`
- Produces: `dist/styleguide_{paper,deck}_raw.html`

- [ ] **Step 1: 실패하는 e2e test 추가**

`tests/test_build_e2e.py` 끝에 추가한다.

```python
@pytest.fixture(scope="module")
def styleguide(tmp_path_factory):
    out = tmp_path_factory.mktemp("styleguide")
    subprocess.run([sys.executable, str(ROOT / "examples" / "build_styleguide.py"), *MODES],
                   cwd=ROOT, check=True, capture_output=True)
    node = shutil.which("node")
    if not node:
        pytest.skip("node 가 없다")
    results = {}
    for m in MODES:
        dst = out / f"styleguide_{m}.html"
        r = subprocess.run(
            [node, str(ASSETS / "mathbuild.js"), str(ROOT / "dist" / f"styleguide_{m}_raw.html"), str(dst),
             "--assets", str(ASSETS)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, f"{m} styleguide 빌드 실패:\n{r.stdout}\n{r.stderr}"
        results[m] = dst
    return results


@pytest.mark.skipif(not have_chromium(), reason="chromium 없음")
@pytest.mark.parametrize("mode", MODES)
def test_styleguide_passes_qa(styleguide, mode):
    """styleguide 는 실제 문서와 같은 경로를 통과한다. 통과하지 못하면 규칙 자체가 깨진 것이다."""
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "qa.py"), str(styleguide[mode])],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"styleguide QA 실패:\n{r.stdout}\n{r.stderr}"
```

Run: `python3 -m pytest tests/test_build_e2e.py -q -k styleguide`
Expected: FAIL — `examples/build_styleguide.py` 없음

- [ ] **Step 2: `examples/build_styleguide.py` 작성**

```python
# -*- coding: utf-8 -*-
"""
build_styleguide.py — token 과 component 를 한 문서에 늘어놓는 styleguide.

    python examples/build_styleguide.py            paper · deck 둘 다
    python examples/build_styleguide.py paper

dist/styleguide_<mode>_raw.html 을 생성한다. 이어서 실제 문서와 같은 mathbuild.js 를
통과시킨다 — 별도 렌더 경로를 두면 styleguide 만 통과하고 문서는 깨지는 일이 생긴다.

각 절은 <section data-sg="<id>"> 로 구분한다. 내용은 가상 사례에서 가져온다.
"""
import itertools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "plugins" / "korean-report" / "skills" / "korean-report-doc" / "assets"
sys.path.insert(0, str(ASSETS))
sys.path.insert(0, str(ROOT / "scripts"))

import csstokens as T  # noqa: E402
from figures import (  # noqa: E402
    BADGE_IMPL,
    BADGE_MEAS,
    BADGE_NO,
    BADGE_NONE,
    fig_cards,
    fig_compare,
    fig_flow,
    fig_gantt,
    fig_numberline,
    fig_scatter,
    fig_timeline,
    figcap,
    tbl,
    tblcap,
)

TOKENS = (ASSETS / "css" / "tokens.css").read_text(encoding="utf-8")
ROOT_T = T.declared(TOKENS, ":root")
DARK_T = T.declared(TOKENS, ".dark")
BLACK_T = T.declared(TOKENS, ".black")
STEPS = ["-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
SAMPLE = f"A사 인라인 계측 3,240 m² · 검사 SDK v2.1 — 위치 오차 ±0.35 m, 갱신 주기 12 ms {BADGE_MEAS}"
SHORT = "계측 3,240 m² · ±0.35 m"
COLOR_TOKENS = ["--ink", "--ink-2", "--ink-3", "--accent", "--surface", "--surface-2", "--surface-3",
                "--rule", "--rule-soft", "--mark", "--fig-line", "--fig-soft", "--fig-pale", "--fig-mid"]
# (이름, class, 배경) — paper 에서는 div 로, deck 에서는 tile 로 surface 를 재현한다
SURFACES = [("light", "", "var(--surface)"), ("parch", "", "var(--surface-2)"),
            ("dark", "dark", "var(--surface)"), ("black", "black", "var(--surface)")]
_fig_no = itertools.count(1)


def section(sg, n, title, body):
    return f'<section id="sg-{sg}" data-sg="{sg}"><h2><span class="sn">{n}</span>{title}</h2>\n{body}\n</section>'


def surface_box(cls, bg, inner):
    return (f'<div class="{cls}" style="background:{bg};color:var(--ink);padding:24px;'
            f'border-radius:12px;margin:16px 0">{inner}</div>')


def ratio(fg, bg):
    ok = fg.startswith("#") and bg.startswith("#")
    return f"{T.contrast(fg, bg):.2f}" if ok else "—"


def color_section():
    rows = []
    for name in COLOR_TOKENS:
        light, dark = ROOT_T[name], DARK_T.get(name, ROOT_T[name])
        chip = (f'<span style="display:inline-block;width:40px;height:16px;background:var({name});'
                'border:1px solid var(--rule)"></span>')
        rows.append([f"<code>{name}</code>", chip, light, ratio(light, ROOT_T["--surface"]),
                     ratio(light, ROOT_T["--surface-2"]), dark, ratio(dark, DARK_T["--surface"]),
                     ratio(dark, BLACK_T["--surface"])])
    head = ["token", "", "light", "대 surface", "대 surface-2", "dark", "대 dark", "대 black"]
    return tbl(head, rows, cls="num") + tblcap(1, "색 token 과 WCAG 대비비")


def type_section(sample):
    out = []
    for s in STEPS:
        t, lh, tr = (ROOT_T[f"--{p}{s}"] for p in ("t", "lh", "tr"))
        out.append(f'<p class="srcline">t{s} · {t} / {lh} · {tr}</p>'
                   f'<p style="font-size:var(--t{s});line-height:var(--lh{s});letter-spacing:var(--tr{s})">'
                   f'{sample}</p>')
    return "\n".join(out)


def space_section():
    return "\n".join(
        f'<div style="display:flex;align-items:center;gap:12px;margin:4px 0"><code>--s-{n}</code>'
        f'<span style="display:inline-block;height:12px;width:var(--s-{n});background:var(--accent)"></span>'
        f'{ROOT_T[f"--s-{n}"]}</div>' for n in range(1, 11))


def components():
    table = tbl(["항목", "개선 전", "개선 후", "상태"],
                [["계측 시간", "900초", "590초", BADGE_MEAS],
                 {"c": "hl", "v": ["유효 검출률", "4/7", "5/7", BADGE_MEAS]},
                 ["오버레이", "—", "—", BADGE_NONE]], cls="num")
    return f'''<p class="eyebrow">eyebrow</p>
<p>본문 — {SAMPLE}. <mark>강조는 독자 층위다.</mark> <a href="#sg-tokens-color">링크</a> · <code>retryLimit</code></p>
<div class="legend">{BADGE_MEAS} 실측 · {BADGE_IMPL} 구현됨 · {BADGE_NONE} 미측정 · {BADGE_NO} 해당 없음</div>
{table}
<div class="note"><p>note — 보충 설명.</p></div>
<div class="warn"><p>warn — 주의가 필요한 전제.</p></div>
<div class="finding"><p>finding — 이 문서의 주장.</p><p class="cav">cav — 그 주장의 한계.</p></div>
<div class="claim">claim — 한 문장 요지.</div>
<div class="metrics"><div class="metric"><div class="mlabel">계측 시간</div><div class="mval">590초</div>
<div class="mnote">웨이퍼당 · 실측</div></div>
<div class="metric gap"><div class="mlabel">오버레이</div><div class="mval">—</div><div class="mnote">미측정</div></div></div>
<ul class="plain"><li>plain 목록 항목</li><li>두 번째 항목</li></ul>
<ol class="concl"><li>결론 목록 항목</li><li>두 번째 결론</li></ol>
<blockquote>blockquote — 인용한 원문.</blockquote>
<div class="quote-box"><p>quote-box — 강조 인용.</p></div>
<div class="rsn"><div class="rsn-no">근거 1</div><p>rsn — 근거 카드.</p></div>
<pre><span class="c"># code block</span>
retryLimit = 3</pre>
<p class="srcline">출처 — A사 계측 기록(가상) · 2026-08-31</p>'''


def figure_set():
    figs = [
        fig_timeline([("2026-08-10", "08-10", "계측 규격 초안", True), ("2026-10-22", "10-22", "인증 시험", False)],
                     "2026-08-01", "2026-11-01", note="남은 82일"),
        fig_cards([(1, "검사–빈닝 연결", "판정 기준 정정"), (2, "양산 조건 벤치", "수율 재측정")]),
        fig_flow([("검사", "결함 좌표"), ("빈닝", "판정"), ("분석", "수율")], highlight=1),
        fig_numberline([("개선 후", 590.0), ("개선 전", 900.0)], 0, 1000),
        fig_compare([("계측 시간", 590, 900, "590초", "900초")], 1000),
        fig_scatter([(1, 2, "L1"), (2, 3, "L2"), (3, 1.5, "L3")], 0, 4),
    ]
    out = [f + figcap(next(_fig_no), "도해 견본") for f in figs]
    out.append(fig_gantt([("검사 레시피 정비", "2026-08-01", "2026-08-25", "done"),
                          ("오버레이 계측 보강", "2026-08-20", "2026-09-20", "plan"),
                          ("인증 시험", "2026-10-01", "2026-10-25", "key")],
                         "2026-08-01", "2026-11-01", markers=[("2026-08-31", "품질보고", "gate")]))
    return "\n".join(out)


def math_section():
    table = tbl(["기호", "의미"], [["⟦I⟧D_0⟦/I⟧", "결함 밀도"], ["⟦I⟧A⟦/I⟧", "다이 면적"]])
    return (r"<p>수율 ⟦I⟧Y⟦/I⟧ 는 다음과 같다.</p>"
            r"⟦D⟧Y = \left(1 + \frac{D_0 A}{\alpha}\right)^{-\alpha}⟦/D⟧" + table)


KEEPALL = ("<p>인라인계측장비의 교정주기재산정 결과를 양산조건기준수율벤치에 반영하였다. "
           "어절 단위 줄바꿈이 적용되면 「교정주기재산정」 같은 긴 어절이 중간에서 잘리지 않는다. "
           "분절할 수 없는 문자열은 overflow-wrap 이 처리한다 — "
           "https://example.com/very/long/path/that/cannot/break/at/any/space</p>")

PUNCT = ("<ul class=\"plain\"><li>중간점 — 그림 3 · 제목</li><li>줄표 — K — 핵심이자 약점</li>"
         "<li>범위 — 600–900 ms</li><li>단위 — 0.35 m · 12 ms · 4.8%</li><li>인용 — 「계측 규격 초안」</li></ul>")


def tnum_section():
    rows = [["1111", "0.35", "12,340"], ["8888", "10.07", "3,240"], ["1010", "0.08", "999"]]
    return tbl(["정수", "소수", "천 단위"], rows, cls="num") + tblcap(2, "tabular-nums — 자릿수가 세로로 정렬된다")


def breaks_section():
    long = tbl(["회차", "계측 시간", "검출률"],
               [[f"{i}", f"{900 - i * 10}초", f"{i % 7}/7"] for i in range(1, 25)], cls="num")
    return "\n".join([long, tblcap(3, "쪽 경계에 걸리는 긴 표"),
                      '<div class="finding"><p>표 다음 callout — 쪽 경계에서 잘리지 않아야 한다.</p></div>',
                      figure_set()])


def paper():
    parts = [
        '<header class="paper-head"><p class="eyebrow">styleguide · paper</p>'
        '<h1>korean-report-doc styleguide</h1><p class="subtitle">token · component · 도해 · typesetting 검사</p>'
        '<div class="byline"><span>가상 사례 A사</span><span>2026-09-19</span></div></header>',
        section("tokens-color", 1, "색 token 과 대비", color_section()),
        section("tokens-type", 2, "type scale 13단계", type_section(SAMPLE)),
        section("tokens-space", 3, "space token", space_section()),
        *[section(f"comp-{name}", 4 + i, f"component — {name}", surface_box(cls, bg, components()))
          for i, (name, cls, bg) in enumerate(SURFACES)],
        section("fig-light", 8, "도해 — light", figure_set()),
        section("fig-dark", 9, "도해 — dark", surface_box("dark", "var(--surface)", figure_set())),
        section("math", 10, "수식", math_section()),
        section("check-keepall", 11, "어절 단위 줄바꿈", KEEPALL),
        section("check-tnum", 12, "숫자 폭 정렬", tnum_section()),
        section("check-punct", 13, "문장부호와 단위", PUNCT),
        section("check-breaks", 14, "쪽 경계", breaks_section()),
    ]
    return "\n".join(parts)


def tile(bg, sg, n, title, body):
    return (f'<section class="tile {bg}" data-sg="{sg}"><div class="wrap">'
            f'<h2><span class="sn">{n}</span>{title}</h2>\n{body}\n</div></section>')


def deck_components():
    table = tbl(["항목", "개선 전", "개선 후"],
                [["계측 시간", "900초", "590초"], {"c": "hl", "v": ["유효 검출률", "4/7", "5/7"]}], cls="num")
    return f'''<div class="legend">{BADGE_MEAS} 실측 · {BADGE_IMPL} 구현됨 · {BADGE_NONE} 미측정</div>
{table}
<div class="finding"><p>finding — 이 문서의 주장. <mark>강조</mark> · <code>retryLimit</code></p>
<p class="cav">cav — 한계.</p></div>
<div class="metrics"><div class="metric"><div class="mlabel">계측 시간</div><div class="mval">590초</div></div>
<div class="metric gap"><div class="mlabel">오버레이</div><div class="mval">—</div></div></div>'''


def deck():
    # 인접 tile 은 배경을 공유하지 않는다. black 은 표지와 EOD 에만 쓴다(design.md §2.1)
    cover = ('<section class="tile black cover" data-sg="cover"><div class="wrap">'
             '<h1 class="hero">styleguide · deck</h1><div class="rule"></div>'
             '<div class="meta">가상 사례 A사<br>2026-09-19</div></div></section>')
    cards = fig_cards([(1, "검사–빈닝 연결", "판정 기준 정정"), (2, "양산 조건 벤치", "수율 재측정")])
    compare = fig_compare([("계측 시간", 590, 900, "590초", "900초")], 1000)
    return "\n".join([
        cover,
        tile("light", "tokens-type", 1, "type scale", type_section(SHORT)),
        tile("parch", "comp-parch", 2, "component — parch", deck_components()),
        tile("dark", "comp-dark", 3, "component — dark", deck_components()),
        tile("light", "comp-light", 4, "component — light", deck_components()),
        tile("parch", "fig-parch", 5, "도해 — parch", cards + figcap(1, "도해 견본")),
        tile("dark", "fig-dark", 6, "도해 — dark", compare + figcap(2, "도해 견본")),
    ])


def build(mode):
    body = paper() if mode == "paper" else deck()
    tpl = (ASSETS / f"{mode}_template.html").read_text(encoding="utf-8")
    html = tpl.replace("__BODY__", body).replace("__TITLE__", f"styleguide {mode}")
    out = ROOT / "dist" / f"styleguide_{mode}_raw.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    for m in sys.argv[1:] or ["paper", "deck"]:
        if m not in ("paper", "deck"):
            raise SystemExit(f"모드는 paper 또는 deck 이다 — 받은 값: {m}")
        print(build(m))
```

`figures.py`의 도해 함수 signature 가 위 호출과 다르면 `tests/test_consistency.py`의 `emitted_classes()`에 있는 호출 형태를 기준으로 인자를 교체한다.

- [ ] **Step 3: build 와 QA 확인**

```bash
python3 examples/build_styleguide.py
for m in paper deck; do node $A/mathbuild.js dist/styleguide_${m}_raw.html dist/styleguide_${m}.html --assets $A; done
python3 scripts/qa.py dist/styleguide_paper.html dist/styleguide_deck.html --pdf --shot dist/shots-sg
```

Expected: FAIL 없음. deck 에서 「한 쪽을 넘는다」가 보고되면 그 tile 의 내용을 두 tile 로 분리한다.
screenshot 에서 다음을 확인한다.

- `check-keepall` 절에 어절 중간 줄바꿈이 없다
- `check-tnum` 절의 숫자가 자릿수 단위로 정렬된다
- dark · black surface 에서 모든 글자와 도해가 읽힌다
- PDF 에서 dark 절이 밝은 값으로 인쇄된다

- [ ] **Step 4: CI 와 npm script 추가**

`package.json`의 `"build:example"` 다음 줄에 추가한다.

```json
    "build:styleguide": "node scripts/run-python.js examples/build_styleguide.py",
```

`.github/workflows/ci.yml`의 `README 전후 대비 자산 빌드` step 앞에 추가한다.

```yaml
      - name: styleguide 빌드
        if: runner.os == 'Linux'
        run: |
          python examples/build_styleguide.py
          for m in paper deck; do
            node plugins/korean-report/skills/korean-report-doc/assets/mathbuild.js \
              "dist/styleguide_${m}_raw.html" "dist/styleguide_${m}.html" \
              --assets plugins/korean-report/skills/korean-report-doc/assets
          done
          python scripts/qa.py dist/styleguide_paper.html dist/styleguide_deck.html --pdf --shot dist/shots
```

`example-documents` artifact 의 `path`에 두 줄을 추가한다.

```yaml
            dist/styleguide_*.html
            dist/styleguide_*.pdf
```

- [ ] **Step 5: 검사 실행**

Run: `npm test && ruff check .`
Expected: 전부 PASS

- [ ] **Step 6: Commit**

```bash
git add examples/build_styleguide.py tests/test_build_e2e.py .github/workflows/ci.yml package.json
git commit -F - <<'EOF'
Add a styleguide built through the same pipeline as documents

It lays out colour tokens with their contrast ratios, the type scale,
spacing, every component on four surfaces, the figures on light and
dark, maths, and check sections for line breaking, tabular figures,
punctuation and page breaks. CI builds and QA-checks it on Linux.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
EOF
```

---

### Task 7: 문서 갱신

**Files:**
- Modify: `plugins/korean-report/skills/korean-report-doc/SKILL.md`, `references/design.md`, `references/figures.md`, `README.md`, `INSTALL.md`, `NOTICE`, `CHANGELOG.md`, `scripts/new-document.py`

- [ ] **Step 1: `SKILL.md`**

| 위치 | 교체 |
|---|---|
| frontmatter `description`의 `optional body-font embedding` | `a bundled Pretendard body font` |
| 머리 목록 「본문 글꼴은 `--font`로 지정한 경우에만 내장된다.」 | 「본문 글꼴은 동봉한 Pretendard 공식 subset 을 기본으로 내장한다. `--font`는 교체할 때만 쓴다.」 |
| 머리 목록 「두 출력 모드는 공통 디자인 token과 모드별 CSS를 사용한다.」 | 「값은 `assets/css/tokens.css` 한 곳에 있고, 공통 CSS 와 모드별 CSS 는 그 token 만 참조한다.」 |
| §1.3 「본문 글꼴을 내장하려면 사용 권한이 있는 WOFF2 파일을 준비한다.」 | 「본문 글꼴은 `assets/fonts/`에 동봉되어 있다. 다른 글꼴을 쓰려면 사용 권한이 있는 WOFF2 파일을 준비한다.」 |
| §2 그림 `· base.css + 모드 CSS 삽입` | `· tokens.css + base.css + 모드 CSS 삽입` |
| §2 그림 `· 지정한 본문 글꼴 · KaTeX woff2 base64 내장` | `· 본문 글꼴(동봉 또는 --font) · KaTeX woff2 base64 내장` |
| §2 표 두 번째 행의 자리 목록 | `` `__FONTCSS__` · `__KATEXCSS__` · `__TOKENCSS__` · `__BASECSS__` · `__MODECSS__` `` |
| §2 「공통은 `css/base.css`, 모드별은 …」 문장 | 앞에 「값은 `css/tokens.css` 한 곳에만 둔다.」 추가 |
| §2.2 명령 예시 | `--font …` 줄 삭제 |
| §2.2 「`--font` 를 생략하면 경고만 내고 진행한다. … 배포본에는 반드시 내장한다.」 | 「`--font` 를 생략하면 동봉한 Pretendard subset 을 내장한다. 본문에 subset 밖의 한글 음절이 있으면 경고하고, 그 글자는 system font 로 표시된다.」 |
| §2.3 명령 예시 다음 | 「paper PDF 는 쪽 하단에 제목과 쪽번호를 인쇄한다.」 추가 |
| §7 목록 | `` `assets/css/tokens.css` `` 를 CSS 줄 앞에, `` `assets/fonts/` — Pretendard 공식 subset 과 license `` 를 마지막에 추가 |

- [ ] **Step 2: `references/design.md`**

§1.1 의 CSS 코드 블록을 다음으로 교체한다. 아래의 **Rules** 목록은 유지하고 `--primary`를 `--accent`로,
`--primary-dark`를 「the dark-surface value of `--accent`」로 교체한다.

````markdown
Values live in `assets/css/tokens.css`; this section names the roles only.

| Role | Token |
|---|---|
| Accent — the only chromatic value | `--accent` (dark surfaces redefine it) |
| Text on accent | `--on-accent` |
| Ink — body · secondary · captions | `--ink` · `--ink-2` · `--ink-3` |
| Surfaces — canvas · alternating · callout fill | `--surface` · `--surface-2` · `--surface-3` |
| Rules — heavy · hairline · divider | `--rule-heavy` · `--rule` · `--rule-soft` |
| Highlight — a reading layer (§4.7) | `--mark` · `--mark-ink` (fixed) |
| Figure palette | `--fig-line` · `--fig-soft` · `--fig-pale` · `--fig-mid` |

`.dark` and `.black` redefine these tokens for dark surfaces, and `@media print` restores the
light values. The pre-1.x names (`--primary`, `--ink48`, `--parchment`, …) remain as aliases
until 2.0.
````

§1.2 의 font 내장 명령 예시와 그 다음 문단을 교체한다.

```markdown
The build embeds the bundled Pretendard subset (`assets/fonts/`) by default; `--font` replaces
it. Characters outside the subset fall back to the stack above and the build warns about them.
```

§1.2 의 role 표를 다음 문장과 표로 교체한다.

```markdown
Sizes come from the 13-step scale in `tokens.css` — base 17/28px, ratio 1.125, line heights on
a 4px grid, tracking tightening monotonically with size. Print overrides the same tokens in points.

| Role | Step |
|---|---|
| Hero (deck) | `--t9` |
| h1 (paper) · metric value | `--t8` |
| h2 — deck · paper | `--t6` · `--t4` |
| h3 | `--t3` |
| Lead | `--t2` |
| Subtitle · h4 | `--t1` |
| Body | `--t0` |
| Table · lists · callout text | `--t-1` |
| Caption · eyebrow · table header | `--t-2` |
| Badge · EOD | `--t-3` |
```

§1.3 의 CSS 코드 블록을 다음으로 교체한다.

```markdown
Spacing is `--s-1` … `--s-10` (4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 80 · 96px); radius is
`--r-sm` · `--r-md` · `--r-lg` · `--r-pill`. Values are in `tokens.css`.
```

「Section padding is `--s-sec` in deck mode」를 「Section padding is `--s-9` in deck mode」로 교체한다.

§7.3 의 CSS 코드 블록을 다음으로 교체한다.

```markdown
`tokens.css` restores every dark-surface token to its light value inside `@media print`, so
dark tiles print as light pages without per-component overrides.
```

나머지 절의 변수명을 일괄 교체한다.

```bash
perl -pi -e '
  s/--primary-dark/--accent/g; s/--primary\b/--accent/g; s/--ink80\b/--ink-2/g; s/--ink48\b/--ink-3/g;
  s/--canvas\b/--surface/g; s/--parchment\b/--surface-2/g; s/--pearl\b/--surface-3/g;
  s/--hairline\b/--rule/g; s/--divider\b/--rule-soft/g; s/--tile1\b/--code-bg/g;
' plugins/korean-report/skills/korean-report-doc/references/design.md
```

교체 뒤 §1.1 의 alias 문장이 옛 이름을 그대로 보여 주는지 확인한다. `--primary` 등이 `--accent`로 바뀌었으면 원래 이름으로 되돌린다.

- [ ] **Step 3: `references/figures.md`**

§1 의 상수 표를 교체한다.

```markdown
| token | 채움 class | 선 class |
|---|---|---|
| `--ink` | `fi-ink` | `st-ink` |
| `--ink-3` | `fi-ink48` | `st-ink48` |
| `--accent` | `fi-pri` | `st-pri` |
| `--fig-mid` | `fi-mid` | `st-mid` |
| `--fig-line` | `fi-line` | `st-line` |
| `--fig-soft` | `fi-soft` | — |
| `--fig-pale` | `fi-pale` | — |

class 이름은 1.x 호환을 위해 유지한다. 값은 `assets/css/tokens.css`에 있다.
```

「클래스를 쓰면 `deck.css` 가 토큰을 뒤집을 때」를 「class 를 쓰면 `tokens.css` 가 다크 surface 의 token 을 교체할 때」로 교체한다.

- [ ] **Step 4: `README.md` · `INSTALL.md` · `NOTICE`**

README 「본문 글꼴은 사용 권한이 있는 WOFF2 파일을 `--font`로 지정한 경우에만 HTML에 …」 문단을 교체한다.

```markdown
본문 글꼴은 동봉한 Pretendard 공식 subset(OFL 1.1)을 기본으로 HTML에 내장합니다. 다른 글꼴을
쓰려면 사용 권한이 있는 WOFF2 파일을 `--font`로 지정합니다. subset에 없는 한글 음절은 시스템
글꼴로 표시되며 빌드가 해당 글자를 알립니다.
```

README 「본문 글꼴을 HTML에 내장하려면 실행할 때 WOFF2 경로를 지정합니다.」를
「다른 본문 글꼴을 쓰려면 실행할 때 WOFF2 경로를 지정합니다.」로 교체한다.

INSTALL.md 「기준 HTML에는 CSS와 KaTeX 수식 글꼴이 내장됩니다. …」 문단을 교체하고, 이어지는 명령 예시에서 `--font` 두 줄을 삭제한다.

```markdown
기준 HTML에는 CSS, KaTeX 수식 글꼴, 동봉한 Pretendard 본문 글꼴이 내장됩니다. 다른 본문 글꼴을
쓰려면 사용 권한이 있는 WOFF2 파일을 `mathbuild.js`의 `--font` 인자로 지정합니다.
```

NOTICE 에서 Pretendard 항목을 「빌드 시점에 사용하는 제3자 자산」 목록에서 삭제하고, 그 목록 앞에 새 절을 추가한다.

```
이 저장소가 동봉하는 제3자 자산:

  Pretendard 1.3.9 — SIL Open Font License 1.1
    https://github.com/orioncactus/pretendard
    plugins/korean-report/skills/korean-report-doc/assets/fonts/
    공식 배포본의 subset woff2 를 변경 없이 동봉한다. 라이선스 원문은 같은 디렉터리의
    LICENSE.txt 다. Reserved Font Name 조항이 있어 변경본은 Pretendard 라는 이름을 쓸 수 없다.
```

- [ ] **Step 5: `scripts/new-document.py`의 안내 문구**

사용법 문자열의 `python {stem}.py [--font <woff2>]...` 다음 줄에 「`--font` 는 동봉 Pretendard 를 교체할 때만 쓴다.」를 추가한다.
완료 안내의 `print(f"  python {out} --font Pretendard-Regular.woff2   # 글꼴 내장")`을 교체한다.

```python
    print(f"  python {out} --font 다른글꼴.woff2   # 동봉 Pretendard 교체")
```

- [ ] **Step 6: `CHANGELOG.md`**

`## [Unreleased]` 아래에 추가한다. 크기 수치는 Task 4 Step 7 의 실측값으로 채운다.

```markdown
### 더해짐

- **`tokens.css` — 값의 단일 원천.** 색 · type scale · space · surface 재매핑 · 인쇄 복귀가 한 파일에
  모였다. `base.css` · `paper.css` · `deck.css`는 `var()`로만 참조하고 `tests/test_tokens.py`가 색
  리터럴의 위치, 미정의 token, 인쇄 복귀, 본문 대비 4.5:1 을 검사한다. 옛 변수명은 2.0 까지 alias 로 남는다.
- **Pretendard 공식 subset 동봉과 기본 내장.** `--font` 없이도 본문 글꼴이 내장된다. subset 밖의
  한글 음절은 경고한다. plugin 크기 ○○ KB → ○○ KB, 예시 paper 문서 ○○ KB → ○○ KB.
- **styleguide.** `examples/build_styleguide.py`가 token · component · 도해를 surface 4종에서 한 문서로 산출한다.
- **paper PDF footer.** 쪽 하단에 제목과 쪽번호를 인쇄한다.

### 바뀜

- **type scale.** 본문 16.5px → 17px, 행간 28px, 13단계 비율 1.125. 가장 큰 변화는 h3(18.5px → 24px)다.
  모든 문서의 인상이 달라진다.
- **한글 typesetting.** 어절 단위 줄바꿈(`keep-all`), 표와 수치의 `tabular-nums`, 제목의 `text-wrap:balance`.
- **인쇄.** 다크 tile 의 글자색이 `#000`에서 `--ink`로, 도해 token 도 밝은 값으로 복귀한다.

### 고쳐짐

- `mathbuild.js`가 `Pretendard-SemiBold.subset.woff2`처럼 이름에 `.subset`이 붙은 파일의 굵기를 400 으로 읽었다.
```

- [ ] **Step 7: 검사 실행**

Run: `npm test && ruff check . && python3 plugins/korean-report/skills/korean-report-style/assets/lint.py README.md INSTALL.md plugins/korean-report/skills/korean-report-doc/SKILL.md`
Expected: 전부 PASS, lint 「문체 규약 위반 없음」

- [ ] **Step 8: Commit**

```bash
git add plugins/korean-report/skills/korean-report-doc/SKILL.md plugins/korean-report/skills/korean-report-doc/references \
  README.md INSTALL.md NOTICE CHANGELOG.md scripts/new-document.py
git commit -F - <<'EOF'
Document tokens.css, the bundled font and the new type scale

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018HEzkQuN3CAXtPLVnRRmg6
EOF
```

---

### Task 8: 전체 검증과 README 이미지

**Files:** 없음(검증), 이후 `docs/assets/*.png`

- [ ] **Step 1: 클린 checkout 검증**

```bash
git stash list   # 비어 있어야 한다
rm -rf dist node_modules
npm ci
npm test
ruff check .
python3 examples/build_example.py
for m in paper deck; do node $A/mathbuild.js dist/example_${m}_raw.html dist/example_${m}.html --assets $A; done
python3 scripts/qa.py dist/example_paper.html dist/example_deck.html --pdf --shot dist/shots
```

Expected: 전부 PASS, `mathbuild.js` 출력에 WARN 없음(명세 §4.9 완료 기준 1)

- [ ] **Step 2: 명세 완료 기준 대조**

| 기준 | 확인 방법 |
|---|---|
| `assets/css/`와 template 에 색 리터럴 없음 | `test_color_literals_live_only_in_tokens` |
| `test_tokens.py` 통과, 본문 대비 실패 0 | `test_body_text_contrast` |
| styleguide 가 surface 4종 × 전 component 렌더 | `dist/shots-sg/styleguide_paper.png` 육안 |
| `SKILL.md`가 참조하는 파일 실재 | `test_referenced_files_exist` |

- [ ] **Step 3: push 와 README 이미지 — 사용자 승인 후**

push 와 PR 생성은 사용자에게 확인한 뒤 진행한다. CI 의 「README 자산 재생성과 대조」 step 은 이번 변경으로
반드시 실패한다(type scale 과 font 가 바뀌었다). 저장소의 기존 절차를 따른다.

1. CI 실행의 `shots-regenerated` artifact 를 내려받는다 — `gh run download <run-id> -n shots-regenerated -D dist/shots-regenerated`
2. `docs/assets/`의 PNG 5종을 교체하고 commit 한다
3. 로컬(macOS) 재생성은 글꼴 렌더가 달라 다시 어긋나므로 쓰지 않는다

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

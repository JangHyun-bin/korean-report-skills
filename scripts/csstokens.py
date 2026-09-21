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
    assert round(contrast("#7a7a7a", "#fff"), 1) == 4.3
    sample = ":root{--a:#fff}\n.dark,.black{--a:#000}\n@media print{.dark,.black{--a:#fff}}"
    assert declared(sample, ".dark") == {"--a": "#000"}
    assert declared(sample, ".black", "@media print") == {"--a": "#fff"}
    print("ok")

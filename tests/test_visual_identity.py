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

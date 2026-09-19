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

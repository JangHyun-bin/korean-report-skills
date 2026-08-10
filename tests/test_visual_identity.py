# -*- coding: utf-8 -*-
"""
첫 화면 자산의 규격.

로고와 배너는 사람이 눈으로 볼 때만 문제가 드러나는 자산이라, 기계가 잡을 수 있는
것이라도 잡아 둔다 — 규격, 색 하드코딩, 참조 실재.
판단 근거는 docs/design/2026-08-10-visual-identity.md 에 있다.
"""
import os
import pathlib
import re
import struct
import subprocess
import sys

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

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_size(path: pathlib.Path) -> tuple[int, int]:
    """
    PNG 의 IHDR 청크에서 폭·높이만 읽는다. 서명 8바이트 + 청크 길이 4바이트 +
    "IHDR" 4바이트 뒤에 빅엔디언 부호 없는 32비트 정수 두 개(폭, 높이)가 온다.
    서명과 청크 타입도 함께 확인해 엉뚱한 파일을 조용히 통과시키지 않는다.
    """
    with open(path, "rb") as f:
        header = f.read(24)
    assert header[:8] == PNG_SIGNATURE, f"{path.name} 이 PNG 시그니처로 시작하지 않는다"
    assert header[12:16] == b"IHDR", f"{path.name} 의 첫 청크가 IHDR 이 아니다"
    return struct.unpack(">II", header[16:24])


@pytest.mark.parametrize("name", BANNERS)
def test_banner_exists_with_expected_size(name):
    """
    배너 규격이 흔들리면 README 에서 높이가 튄다.
    2240×600 은 1120×300 을 2배 밀도로 찍은 것이다.
    """
    path = ROOT / "docs" / "assets" / name
    assert path.exists(), f"{name} 이 없다 — python scripts/build-banner.py 로 생성한다"
    size = _png_size(path)
    assert size == (2240, 600), f"{name} 의 크기가 {size} 다"


def test_readme_header_carries_logo_and_banner():
    """첫 화면의 시각 앵커. 빠지면 스펙이 규정한 구조가 무너진다."""
    readme = read(ROOT / "README.md")
    assert "docs/assets/logo.svg" in readme, "README 에 로고가 없다"
    for name in BANNERS:
        assert f"docs/assets/{name}" in readme, f"README 에 {name} 참조가 없다"


def test_readme_banner_switches_by_theme():
    """
    다크에서 라이트 배너가 뜨면 첫 화면이 튄다.
    `<picture>` 의 source 가 다크를 먼저 잡아야 한다 — 그러려면 `<source>` 가
    `<img>` 보다 마크업 순서상 앞에 와야 브라우저가 다크를 먼저 매칭한다.
    """
    readme = read(ROOT / "README.md")
    m = re.search(r"<picture>.*?</picture>", readme, re.S)
    assert m, "README 에 <picture> 블록이 없다"
    block = m.group(0)
    assert "prefers-color-scheme: dark" in block, "다크 source 가 없다"
    assert "banner-dark.png" in block and "banner-light.png" in block

    source_pos = block.find("<source")
    img_pos = block.find("<img")
    assert source_pos != -1 and img_pos != -1, "<source> 또는 <img> 태그가 없다"
    assert source_pos < img_pos, (
        "<source> 가 <img> 보다 뒤에 있다 — 다크 소스가 매칭되지 않고 항상 라이트가 뜬다"
    )


def test_readme_badges_are_present():
    """뱃지 행은 신뢰 신호다. 넷을 유지한다."""
    readme = read(ROOT / "README.md")
    for label in ("tests", "release", "plugin", "license"):
        assert f"img.shields.io/badge/{label}" in readme, f"{label} 뱃지가 없다"


def _count_python_tests() -> int:
    """
    pytest 를 별도 프로세스로 collect-only 실행해 전체 개수를 센다.

    이 파일도 pytest 세션 안에서 돌고 있으므로 `request.session` 을 쓰면
    호출 범위(파일 하나만 지정해 돌리는 경우 등)에 따라 개수가 달라진다.
    별도 프로세스로 전체 스위트를 다시 수집해야 어떻게 호출하든 같은 값이
    나온다. 실패를 삼키지 않는다 — 셀 수 없으면 이 검사도 실패해야 한다.
    """
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env,
    )
    assert result.returncode == 0, (
        f"pytest 수집이 실패했다 (returncode={result.returncode}):\n"
        f"{result.stdout}\n{result.stderr}"
    )
    m = re.search(r"(\d+) tests? collected", result.stdout)
    assert m, f"pytest 수집 출력에서 개수를 찾지 못했다:\n{result.stdout}"
    return int(m.group(1))


def _count_node_tests() -> int:
    """`node scripts/run-node-tests.js` 출력의 `# tests N` 줄에서 개수를 읽는다."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        ["node", "scripts/run-node-tests.js"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env,
    )
    assert result.returncode == 0, (
        f"node 검사가 실패했다 (returncode={result.returncode}):\n"
        f"{result.stdout}\n{result.stderr}"
    )
    m = re.search(r"^# tests (\d+)$", result.stdout, re.M)
    assert m, f"node 검사 출력에서 개수를 찾지 못했다:\n{result.stdout}"
    return int(m.group(1))


def test_readme_badge_test_count_matches_reality():
    """
    뱃지의 숫자는 실제 값에 대한 주장이다. 아무도 강제하지 않으면 검사를
    추가하거나 지울 때마다 조용히 거짓말이 된다 — 치환표를 저장소 자신의
    산문에 적용하는 검사(test_own_prose.py)와 같은 원칙이다.

    뱃지가 「passing」이 아니라 개수를 말하는 이유는 여기서 세는 것이
    수집된 검사의 수이기 때문이다. chromium 이 없는 환경에서는 일부가
    건너뛰어지므로 통과 수가 이보다 적을 수 있다 — 뱃지가 말할 수 없는 것을
    말하지 않게 한다.
    """
    readme = read(ROOT / "README.md")
    m = re.search(r"tests-(\d+)%20tests", readme)
    assert m, "README 뱃지에서 tests 개수를 찾지 못했다"
    claimed = int(m.group(1))

    actual = _count_python_tests() + _count_node_tests()
    assert claimed == actual, (
        f"README 뱃지는 tests-{claimed}%20tests 라고 적혀 있지만 "
        f"실제 개수는 {actual}(python+node) 다. 뱃지 숫자를 고쳐라."
    )


def test_ci_regenerates_banner_and_fails_on_drift():
    """
    배너는 실제 예시 문서에서 잘라낸 자산이라 문서가 바뀌면 낡는다. CI 가 매번
    다시 만들어 커밋된 것과 대조하지 않으면 스크린샷을 손으로 갱신하는
    저장소가 되어 반드시 어긋난다 (docs/design/2026-08-10-visual-identity.md).
    """
    workflow = read(ROOT / ".github" / "workflows" / "ci.yml")
    assert "python scripts/build-banner.py" in workflow, "CI 가 배너를 재생성하지 않는다"
    assert "git diff --exit-code" in workflow, "CI 가 재생성한 배너를 커밋된 것과 대조하지 않는다"
    for name in BANNERS:
        assert name in workflow, f"배너 대조 단계에 {name} 참조가 없다"
    assert "continue-on-error" not in workflow, "배너 대조 단계가 continue-on-error 로 실패를 삼키고 있다"
    assert "|| true" not in workflow, "배너 대조 단계가 || true 로 실패를 삼키고 있다"

    # 대조는 예시 문서 조각이 준비된 뒤(README 전후 대비 자산 빌드), 스킬 패키징보다 앞서야 한다.
    build_pos = workflow.find("README 전후 대비 자산 빌드")
    banner_pos = workflow.find("배너 재생성과 대조")
    pack_pos = workflow.find("스킬 패키징")
    assert build_pos != -1 and banner_pos != -1 and pack_pos != -1, (
        "필요한 단계 이름을 워크플로에서 찾지 못했다"
    )
    assert build_pos < banner_pos < pack_pos, "배너 재생성 단계의 위치가 브리프가 지정한 순서와 어긋난다"

# -*- coding: utf-8 -*-
"""
파이프라인 전체를 한 번 돌려 본다 — 생성기 → mathbuild → 렌더 QA.

단위 검사가 전부 통과해도 조립이 깨질 수 있다. 실제로 그랬다.
브라우저가 없으면 렌더 단계만 건너뛰고 빌드까지는 확인한다.
"""
import shutil
import subprocess
import sys

import pytest
from conftest import ASSETS, ROOT

pytestmark = pytest.mark.e2e

MODES = ["paper", "deck"]


def have_chromium() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("build")
    subprocess.run([sys.executable, str(ROOT / "examples" / "build_example.py"), *MODES],
                   cwd=ROOT, check=True, capture_output=True)
    node = shutil.which("node")
    if not node:
        pytest.skip("node 가 없다")
    results = {}
    for m in MODES:
        raw = ROOT / "dist" / f"example_{m}_raw.html"
        assert raw.exists(), f"생성기가 {raw} 를 만들지 않았다"
        dst = out / f"example_{m}.html"
        r = subprocess.run(
            [node, str(ASSETS / "mathbuild.js"), str(raw), str(dst), "--assets", str(ASSETS)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, f"{m} 빌드 실패:\n{r.stdout}\n{r.stderr}"
        results[m] = dst
    return results


@pytest.mark.parametrize("mode", MODES)
def test_built_document_is_self_contained(built, mode):
    """
    자원을 실제로 가져오는 참조만 본다.
    KaTeX 가 MathML 에 넣는 xmlns URI 는 네임스페이스 식별자일 뿐 요청이 아니다.
    """
    import re

    html = built[mode].read_text(encoding="utf-8")
    fetching = re.findall(
        r'(?:\bsrc|\bhref)\s*=\s*["\']https?://[^"\']+|url\(\s*["\']?https?://[^)]+|@import[^;]*https?://',
        html)
    assert not fetching, f"런타임에 외부 자원을 부른다: {fetching[:3]}"
    for leftover in ("__BODY__", "__TITLE__", "__BASECSS__", "__MODECSS__",
                     "__FONTCSS__", "__KATEXCSS__", "⟦"):
        assert leftover not in html, f"{leftover} 가 남아 있다"


@pytest.mark.parametrize("mode", MODES)
def test_built_document_carries_its_mode_css(built, mode):
    html = built[mode].read_text(encoding="utf-8")
    if mode == "paper":
        assert "--w:720px" in html and "height:210mm" not in html
    else:
        assert "--w:1120px" in html and "height:210mm" in html


@pytest.mark.skipif(not have_chromium(), reason="chromium 없음 — playwright install chromium")
@pytest.mark.parametrize("mode", MODES)
def test_rendered_document_passes_qa(built, mode):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "qa.py"), str(built[mode])],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"QA 실패:\n{r.stdout}\n{r.stderr}"


@pytest.mark.skipif(not have_chromium(), reason="chromium 없음")
@pytest.mark.parametrize("mode", MODES)
def test_scaffold_produces_a_document_that_passes_qa(tmp_path, mode):
    """
    스캐폴드는 처음 쓰는 사람이 가장 먼저 실행하는 것이다.
    그것이 자기 QA 를 통과하지 못하면 첫인상이 실패로 시작한다.
    (실제로 deck 쪽 치환 자리 수가 어긋나 캡션이 밀린 적이 있다.)
    """
    if not shutil.which("node"):
        pytest.skip("node 가 없다")

    gen = tmp_path / f"{mode}.py"
    made = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "new-document.py"),
         "--title", f"검증 {mode}", "--mode", mode, "--out", str(gen)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert made.returncode == 0, made.stderr
    assert gen.exists()

    run = subprocess.run([sys.executable, str(gen)], cwd=tmp_path,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, f"스캐폴드 산출물이 QA 를 통과하지 못한다:\n{run.stdout}\n{run.stderr}"
    assert (tmp_path / f"{mode}.html").exists()


def test_scaffold_refuses_to_overwrite(tmp_path):
    """이미 있는 파일을 덮어쓰면 작업 중인 문서가 날아간다."""
    gen = tmp_path / "x.py"
    gen.write_text("# 기존 내용", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "new-document.py"),
         "--title", "T", "--out", str(gen)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 1
    assert gen.read_text(encoding="utf-8") == "# 기존 내용"


@pytest.mark.skipif(not have_chromium(), reason="chromium 없음")
def test_qa_catches_a_tile_that_overflows_its_page(tmp_path):
    """
    design.md §7.1 — deck 은 1 섹션 = 1 페이지다. 넘친 내용은 `overflow:hidden` 에
    조용히 잘린다. deck 에서 가장 흔한 실패인데 오래 검사가 없던 자리다.
    검사가 실제로 잡는지 확인한다.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("node 가 없다")

    tpl = (ASSETS / "deck_template.html").read_text(encoding="utf-8")
    filler = "<p>한 페이지에 담기지 않을 만큼 긴 문단을 반복한다.</p>\n" * 25
    body = f'<section class="tile light"><div class="wrap"><h2>과밀 타일</h2>{filler}</div></section>'
    raw = tmp_path / "raw.html"
    raw.write_text(tpl.replace("__BODY__", body).replace("__TITLE__", "T"), encoding="utf-8")

    out = tmp_path / "out.html"
    build = subprocess.run(
        [node, str(ASSETS / "mathbuild.js"), str(raw), str(out), "--assets", str(ASSETS)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert build.returncode == 0, build.stderr

    qa = subprocess.run([sys.executable, str(ROOT / "scripts" / "qa.py"), str(out)],
                        cwd=ROOT, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    assert qa.returncode == 1, f"한 쪽을 넘는 타일을 통과시켰다:\n{qa.stdout}"
    assert "한 쪽을 넘는다" in qa.stdout


@pytest.mark.skipif(not have_chromium(), reason="chromium 없음")
def test_deck_prints_one_page_per_tile(built, tmp_path):
    """design.md §7.1 — 1 섹션 = 1 페이지. 인쇄 규칙이 덮이면 여기서 깨진다."""
    import re

    from playwright.sync_api import sync_playwright

    pdf = tmp_path / "deck.pdf"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(built["deck"].resolve().as_uri())
        pg.wait_for_timeout(2000)
        tiles = len(pg.query_selector_all("section.tile"))
        pg.pdf(path=str(pdf), format="A4", landscape=True, print_background=True)
        b.close()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))
    assert pages == tiles, f"타일 {tiles}개인데 {pages}쪽이다 — 인쇄 규칙이 덮였는지 확인한다"

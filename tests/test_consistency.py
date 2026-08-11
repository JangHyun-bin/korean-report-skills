# -*- coding: utf-8 -*-
"""
문서와 자산이 서로 다른 말을 하지 않는지 검사한다.

이 저장소에서 실제로 났던 사고가 전부 이 범주였다.
 · figures.md 가 "템플릿에 .gantt CSS 가 있다"고 적었으나 없었다
 · design.md 가 %%D%% 마커를 적었으나 빌더는 ⟦D⟧ 만 인식했다
 · style/SKILL.md 가 존재하지 않는 DOCUMENT.md 를 가리켰다
 · deck 템플릿이 CDN 폰트를 불러 "자립형" 주장을 위반했다
문서를 고칠 때 자산을 함께 고치게 만드는 것이 이 파일의 목적이다.
"""
import re

import pytest
from conftest import ASSETS, CSS, DOC, ROOT, SKILLS, STYLE, STYLE_ASSETS, all_markdown, css_bundle, read

TEMPLATES = {m: ASSETS / f"{m}_template.html" for m in ("paper", "deck")}
PLACEHOLDERS = ("__TITLE__", "__BODY__", "__FONTCSS__", "__KATEXCSS__", "__BASECSS__", "__MODECSS__")


def defined_classes() -> set[str]:
    return set(re.findall(r"\.([A-Za-z][\w-]*)", css_bundle()))


def emitted_classes() -> set[str]:
    """figures.py 를 실제로 호출해 산출물에서 클래스를 뽑는다."""
    import figures as F

    out = [
        F.fig_timeline([("2026-08-10", "a", "b", True), ("2026-08-20", "c", "d", False)],
                       "2026-08-01", "2026-09-01",
                       bands=[("2026-08-05", "2026-08-25", "band", True),
                              ("2026-08-26", "2026-08-30", "band2", False)]),
        F.fig_gantt([("t", "2026-08-01", "2026-08-20", k) for k in ("done", "plan", "wbs", "key")],
                    "2026-08-01", "2026-11-01",
                    markers=[("2026-09-01", "m", k) for k in ("meet", "gate", "pilot")]),
        F.fig_cards([(i, f"t{i}", "x\ny") for i in range(1, 5)], title="T", sub="S"),
        F.fig_flow([("a", "1"), ("b", "2")], highlight=0),
        F.fig_numberline([("p", 1.0), ("q", 2.0)], 0, 3, marker=(1.5, "m")),
        F.fig_compare([("r", 3, 8, "3", "8")], 10, title="T", sub="S", note="N"),
        F.fig_scatter([(1, 2, "l")], 0, 4),
        F.wide(F.tbl(["h"], [["v"], {"c": "hl", "v": ["w"]}], cls="num")),
        F.BADGE_MEAS + F.BADGE_IMPL + F.BADGE_NONE + F.BADGE_NO,
        F.figcap(1, "c"), F.tblcap(1, "c"),
    ]
    got: set[str] = set()
    for html in out:
        for attr in re.findall(r'class="([^"]*)"', html):
            got |= {t for t in attr.split() if t}
    return got


def test_figures_emitted_classes_are_all_defined_in_css():
    missing = sorted(emitted_classes() - defined_classes())
    assert not missing, (
        f"figures.py 가 방출하지만 CSS 에 없는 클래스: {missing}\n"
        "figures.md 는 '템플릿에 이미 있다'고 적혀 있다. 둘 중 하나를 고쳐야 한다."
    )


@pytest.mark.parametrize("cls", [
    # design.md 가 규정하는 컴포넌트. 문서에 있으면 CSS 에도 있어야 한다.
    "metric", "mlabel", "mval", "mnote",      # §4.4 메트릭 카드
    "note", "warn", "finding", "claim", "cav",  # §4.3 콜아웃
    "bdg", "meas", "impl", "none", "no",      # §4.1 상태 배지
    "figcap", "fig", "narrow",                # §5.4 캡션
    "gantt", "gbar", "gmark", "gaxis",        # figures.md §3 간트
    "hero", "rule", "meta", "cover",          # §3.1 덱 표지
    "paper-head", "abstract", "eyebrow", "byline", "subtitle",  # §3.2 페이퍼 머리
    "tile", "wrap", "dark", "black", "parch", "light",          # §2.1 타일
    "plain", "concl", "scroll", "wide", "hl", "num", "eod",
])
def test_documented_component_class_exists(cls):
    assert cls in defined_classes(), f"design.md 가 규정한 .{cls} 가 CSS 에 없다"


@pytest.mark.parametrize("mode", ["paper", "deck"])
def test_template_has_each_placeholder_exactly_once(mode):
    html = read(TEMPLATES[mode])
    for ph in PLACEHOLDERS:
        n = html.count(ph)
        assert n == 1, (
            f"{mode}_template.html 의 {ph} 등장 횟수 {n} (1이어야 한다). "
            "주석에 토큰을 적으면 str.replace 가 전부 치환해 본문이 중복된다."
        )


@pytest.mark.parametrize("mode", ["paper", "deck"])
def test_template_declares_its_mode(mode):
    assert re.search(rf'<html[^>]*\bdata-mode="{mode}"', read(TEMPLATES[mode])), \
        f"{mode}_template.html 에 data-mode 가 없다 — mathbuild.js 가 모드 CSS 를 고를 수 없다"


@pytest.mark.parametrize("mode", ["paper", "deck"])
def test_template_has_no_runtime_network_dependency(mode):
    """design.md §0.2 · §11 — 런타임에 외부에서 무엇도 불러오지 않는다."""
    html = read(TEMPLATES[mode])
    bad = re.findall(r'(?:href|src)\s*=\s*"(https?://[^"]+)"', html)
    assert not bad, f"{mode}_template.html 이 런타임에 외부 자원을 부른다: {bad}"


@pytest.mark.parametrize("mode", ["paper", "deck"])
def test_template_style_blocks_are_not_duplicated(mode):
    """같은 CSS 블록이 두 번 들어가 뒤엣것이 이기던 사고의 회귀 방지."""
    html = read(TEMPLATES[mode])
    assert html.count(":root{") == 0, \
        f"{mode}_template.html 이 토큰을 직접 정의한다 — css/ 레이어로 옮긴다"
    assert html.count("@media print") == 0, \
        f"{mode}_template.html 이 인쇄 규칙을 직접 담는다 — css/ 레이어로 옮긴다"


def test_print_rules_live_in_exactly_one_place_per_mode():
    """paper.css 와 deck.css 각각 @media print 를 하나씩만 가진다."""
    for f in ("paper.css", "deck.css"):
        n = read(CSS / f).count("@media print")
        assert n == 1, f"{f} 의 @media print 블록이 {n}개다 — 하나여야 한다"


def test_deck_print_keeps_its_own_type_scale():
    """deck 인쇄 규칙이 paper 규칙에 덮이지 않는지. 실제로 났던 사고다."""
    deck_print = read(CSS / "deck.css").split("@media print")[1]
    assert "height:210mm" in deck_print, "deck 인쇄에 1섹션=1페이지 규칙이 없다"
    assert "h1.hero{font-size:34pt}" in deck_print.replace(" ", ""), "deck hero 크기 규칙이 없다"
    assert "h2{font-size:22pt}" in deck_print.replace(" ", ""), \
        "deck h2 는 22pt 여야 한다 — paper 의 14pt 가 새어 들어왔는지 확인한다"


def test_no_legacy_ascii_math_markers_in_code_examples():
    """
    구버전 %%I%% 마커는 빌더가 인식하지 않는다. **코드 예시**에 남으면 따라 쓴 사람이 당한다.
    산문에서 "쓰지 말라"고 언급하는 것은 오히려 필요하므로 코드 펜스만 본다.
    """
    offenders = []
    for p in all_markdown():
        for block in re.findall(r"```[^\n]*\n(.*?)```", read(p), re.S):
            if re.search(r"%%\\?/?[ID]%%", block):
                offenders.append(str(p.relative_to(ROOT)))
                break
    assert not offenders, f"코드 예시에 구버전 ASCII 수식 마커가 있다: {offenders} — ⟦I⟧ · ⟦D⟧ 를 쓴다"


def test_builder_guards_against_legacy_markers():
    """빌더가 구버전 마커를 실제로 검출하는지. 검출이 사라지면 조용히 새어 나간다."""
    js = read(ASSETS / "mathbuild.js")
    assert re.search(r"%%.{0,6}\[ID\].{0,4}%%", js), "mathbuild.js 에 구버전 마커 가드가 없다"
    assert "process.exit(1)" in js, "mathbuild.js 가 실패해도 exit 0 이다 — SKILL.md §2.2 와 어긋난다"


# 실재해서는 안 되는 이름들. 검사에서 뺀다.
ILLUSTRATIVE = {
    "korean-report-doc/korean-report-doc/SKILL.md",  # INSTALL.md 의 "이렇게 하면 인식 안 됨" 예시
    "DOCUMENT.md",                                   # CHANGELOG 가 기록한, 애초에 없던 참조 대상
}


def test_referenced_files_exist():
    """
    문서가 백틱으로 가리키는 저장소 파일이 실재하는지.

    설계 문서(`docs/design/`)는 제외한다. 아직 만들지 않은 파일을 규정하는 것이
    그 장르의 목적이므로, 여기서 실재를 요구하면 설계를 쓸 수 없다.
    구현이 끝나면 그 파일들은 다른 문서에서도 언급되고 그때 검사에 걸린다.
    """
    exts = (".md", ".py", ".js", ".html", ".css", ".sh", ".yml")
    roots = [ROOT, SKILLS, DOC, STYLE, ASSETS, CSS, ROOT / "scripts", ROOT / "plugins",
             DOC / "references", STYLE / "references", STYLE_ASSETS,
             ROOT / "tests", ROOT / "examples"]
    missing = []
    for p in all_markdown():
        if "design" in p.parts:
            continue
        for tok in re.findall(r"`([^`\s]+)`", read(p)):
            if not tok.endswith(exts) or tok.startswith(("http", "-", "/", "~")):
                continue
            if "*" in tok or "{" in tok or tok in ILLUSTRATIVE:
                continue
            # `.py` · `.md` 처럼 확장자만 적은 것은 경로가 아니라 파일 종류를 가리킨다
            if tok.startswith("."):
                continue
            if any((r / tok).exists() for r in roots):
                continue
            missing.append(f"{p.relative_to(ROOT)} → {tok}")
    assert not missing, "문서가 없는 파일을 가리킨다:\n  " + "\n  ".join(missing)


def test_figures_palette_matches_css_tokens():
    """figures.py 의 상수와 base.css 의 토큰이 어긋나면 도해만 다른 색이 된다."""
    import figures as F

    base = read(CSS / "base.css")
    pairs = {
        "--ink:": F.INK, "--ink48:": F.INK48, "--primary:": F.PRI,
        "--fig-mid:": F.MID, "--fig-line:": F.LINE,
        "--fig-soft:": F.SOFT, "--fig-pale:": F.PALE,
    }
    for token, want in pairs.items():
        m = re.search(re.escape(token) + r"\s*(#[0-9a-fA-F]{3,8})", base)
        assert m, f"base.css 에 {token} 토큰이 없다"
        assert m.group(1).lower() == want.lower(), \
            f"{token} 이 base.css 에서 {m.group(1)}, figures.py 에서 {want} 다"


def count_substitution_rows() -> int:
    """
    치환쌍만 센다. §9 는 「용어 · 흔한 오역 · 무엇이 틀리는가」라 치환쌍이 아니므로 제외한다.
    표의 헤더가 「쓰지 않는다」 또는 「찾기」인 표만 치환표로 본다.
    """
    n, in_table = 0, False
    for ln in read(STYLE / "references" / "substitutions.md").splitlines():
        if not ln.startswith("|"):
            in_table = False
            continue
        if "쓰지 않는다" in ln or "찾기" in ln or "| 광의 " in ln:
            in_table = True
            continue
        if in_table and not re.match(r"^\|\s*-", ln):
            n += 1
    return n


def test_readme_substitution_count_is_accurate():
    """README 가 치환 목록 건수를 과장하지 않는지. style 스킬 §3 이 요구하는 정확성이다."""
    actual = count_substitution_rows()
    claimed = re.search(r"치환 목록\s*(\d+)\s*건", read(ROOT / "README.md"))
    assert claimed, "README 에 치환 목록 건수 표기가 없다"
    assert int(claimed.group(1)) == actual, \
        f"README 는 {claimed.group(1)}건이라 하는데 실제는 {actual}건이다"


def test_install_script_targets_match_install_doc():
    """INSTALL.md 표에 있는 도구를 install.sh 가 실제로 지원하는지."""
    sh = read(ROOT / "scripts" / "install.sh")
    doc = read(ROOT / "INSTALL.md")
    for tool in ("claude", "codex", "cursor"):
        in_doc = f".{tool}/skills" in doc
        in_sh = tool in sh
        assert in_doc == in_sh, \
            f"{tool} — INSTALL.md 기재 {in_doc}, install.sh 지원 {in_sh}. 둘을 맞춘다"


def test_version_is_the_same_in_every_place():
    """
    버전이 세 곳에 흩어져 있다. 지금까지 우연히 맞아 있었을 뿐 검사가 없었다.
    릴리스 태그는 package.json 을 따르므로 어긋나면 잘못된 버전이 배포된다.
    """
    import json

    pkg = json.loads(read(ROOT / "package.json"))["version"]
    pyproject = re.search(r'^version\s*=\s*"([^"]+)"',
                          read(ROOT / "pyproject.toml"), re.M).group(1)
    changelog = re.search(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\]",
                          read(ROOT / "CHANGELOG.md"), re.M).group(1)
    badge = re.search(r"release-v([0-9]+\.[0-9]+\.[0-9]+)-", read(ROOT / "README.md")).group(1)
    assert pkg == pyproject == changelog == badge, (
        f"버전이 어긋난다 — package.json {pkg} · pyproject.toml {pyproject} · "
        f"CHANGELOG 최신 항목 {changelog} · README 뱃지 {badge}"
    )


def test_repository_hygiene_files_exist():
    """공개 저장소가 갖춰야 하는 최소 문서."""
    required = [
        "LICENSE", "NOTICE", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug.yml",
        ".github/ISSUE_TEMPLATE/rule.yml",
    ]
    missing = [f for f in required if not (ROOT / f).exists()]
    assert not missing, f"없는 파일: {missing}"


def test_skill_frontmatter_is_wellformed():
    for skill in (DOC, STYLE):
        body = read(skill / "SKILL.md")
        assert body.startswith("---\n"), f"{skill.name}/SKILL.md 에 frontmatter 가 없다"
        fm = body.split("---", 2)[1]
        assert re.search(r"^name:\s*\S+", fm, re.M), f"{skill.name} — name 누락"
        assert re.search(r"^description:\s*\S+", fm, re.M), f"{skill.name} — description 누락"
        name = re.search(r"^name:\s*(\S+)", fm, re.M).group(1)
        assert name == skill.name, f"frontmatter name({name}) 과 폴더명({skill.name})이 다르다"


def test_plugin_manifests_are_wellformed():
    """
    Claude Code 플러그인 규격. `/plugin marketplace add` 가 읽는 파일이므로
    깨지면 설치 경로 하나가 통째로 죽는다. 사람이 알아채기 어렵다.
    """
    import json

    market = json.loads(read(ROOT / ".claude-plugin" / "marketplace.json"))
    assert market["name"] and market["owner"]["name"], "marketplace 에 name·owner 가 필요하다"
    assert market["plugins"], "등재된 플러그인이 없다"

    for entry in market["plugins"]:
        src = ROOT / entry["source"]
        assert src.is_dir(), f"플러그인 경로가 없다: {entry['source']}"

        manifest = json.loads(read(src / ".claude-plugin" / "plugin.json"))
        assert manifest["name"] == entry["name"], (
            f"marketplace 의 {entry['name']} 과 plugin.json 의 {manifest['name']} 이 다르다"
        )
        assert manifest.get("version"), "version 이 없으면 사용자가 갱신을 받지 못한다"

        skills = src / "skills"
        assert skills.is_dir(), f"{entry['name']} 에 skills/ 가 없다"
        found = sorted(d.name for d in skills.iterdir() if (d / "SKILL.md").exists())
        assert found, f"{entry['name']} 의 skills/ 에 SKILL.md 가 없다"


def test_plugin_version_matches_package_version():
    """플러그인 version 이 낡으면 사용자가 갱신을 받지 못한다."""
    import json

    pkg = json.loads(read(ROOT / "package.json"))["version"]
    manifest = json.loads(
        read(ROOT / "plugins" / "korean-report" / ".claude-plugin" / "plugin.json"))["version"]
    market = json.loads(read(ROOT / ".claude-plugin" / "marketplace.json"))
    assert manifest == pkg, f"plugin.json {manifest} · package.json {pkg}"
    assert market["metadata"]["version"] == pkg, "marketplace metadata.version 이 어긋난다"


def test_mark_pins_its_text_color():
    """
    `<mark>` 가 글자색을 상속하면 다크 타일에서 노랑 위 흰 글자가 된다.
    조판해서 확인한 사고다 — 색을 물려받은 안은 다크에서 읽히지 않았고,
    박아 둔 안만 살아남았다. hex 를 박아 도해가 사라지던 것과 같은 계통이다.
    """
    base = read(CSS / "base.css")
    for token in ("--mark:", "--mark-ink:"):
        assert token in base, f"base.css 에 {token} 토큰이 없다"

    rule = re.search(r"(?<![\w-])mark\{([^}]*)\}", base)
    assert rule, "base.css 에 mark 규칙이 없다"
    assert "var(--mark-ink)" in rule.group(1), (
        "mark 가 글자색을 고정하지 않는다 — 다크 타일이 --ink 를 흰색으로 뒤집으면 읽히지 않는다"
    )

    # 다크 타일이 토큰을 뒤집으면 고정한 의미가 없어진다. 인쇄 블록은 되돌리는 자리라 제외한다.
    deck_screen = read(CSS / "deck.css").split("@media print")[0]
    assert "--mark-ink:" not in deck_screen, \
        "deck.css 가 --mark-ink 를 다시 정의한다 — 고정이어야 한다"


def test_italic_is_limited_to_declared_latin():
    """
    Pretendard 에 italic 자족이 없다. 한글에 걸면 합성 oblique 이라 획이 어긋난다.
    라틴이라고 밝힌 자리에만 걸리는지 확인한다.
    """
    base = read(CSS / "base.css")
    assert re.search(r"(?<![\w-])i,\s*em\{[^}]*font-style:\s*normal", base), \
        "i · em 의 기본이 normal 이 아니다 — 한글이 기울어진다"
    assert re.search(r'i\[lang="en"\],\s*em\[lang="en"\]\{[^}]*font-style:\s*italic', base), \
        'lang="en" 을 밝힌 자리에 italic 이 걸리지 않는다'


def test_no_accidental_setext_headings():
    """
    `---` 바로 위에 글이 붙으면 가로줄이 아니라 **setext 제목**이 된다.
    캡션 아래 구분선을 넣으려다 빈 줄을 지우면 그 캡션이 h2 로 부풀어 오른다.
    README 에서 실제로 났다 — GitHub 이 `<h2>` 로 렌더하는 것을 확인하였다.

    이 저장소는 제목을 전부 `#` 로 쓰므로 setext 는 언제나 사고다.
    """
    bad = []
    for p in all_markdown():
        lines = read(p).splitlines()
        # 스킬 문서는 YAML 프론트매터로 시작한다. 그 닫는 `---` 는 제목이 아니다.
        start = 0
        if lines and lines[0].strip() == "---":
            close = next((n for n, x in enumerate(lines[1:], 1) if x.strip() == "---"), 0)
            start = close + 1
        fence = False
        for i, ln in enumerate(lines):
            if i < start:
                continue
            if ln.strip().startswith("```"):
                fence = not fence
                continue
            if fence or i == 0:
                continue
            if re.fullmatch(r"\s*(?:-{3,}|={3,})\s*", ln) and lines[i - 1].strip():
                bad.append(f"{p.relative_to(ROOT)}:{i + 1}  ← 윗줄이 제목이 된다")
    assert not bad, (
        "구분선 위에 빈 줄이 없다:\n  " + "\n  ".join(bad)
        + "\n\n빈 줄을 넣거나, 제목이 의도라면 # 로 쓴다."
    )

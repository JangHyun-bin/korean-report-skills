# 문서 디자인 시스템 — token 단일 원천 · theme · 장르

- **일자** — 2026-09-19
- **상태** — 구현 전 명세
- **입력** — 저장소 밖의 내부 roadmap 초안과 Phase 1 명세 초안. 이 문서는 두 초안을 현행 code 와
  대조하여 범위를 조정한 결과다
- **영향 범위** — `korean-report-doc`의 CSS · template · `mathbuild.js` · `figures.py` · `qa.py`,
  `scripts/new-document.py`, `SKILL.md` · `references/`, 예제, CI
- **구현 제외** — 12컬럼 grid 와 sidenote, 새 도해 타입, pixel 단위 visual regression,
  component 명세의 전면 개정

> **이후 변경 (2026-09-19)** — §4.1 이 적은 `--font-head`와 §5.1 의 theme knob token 은
> ① 단계 구현에서 제외한다. 제목 서체를 theme 마다 다르게 여는 것은 ② theme 단계의 범위이고,
> ①은 값 하나짜리 `--font-body`만 정의한다. §4.5 가 요구하는 PDF footer 의 날짜도 제외한다 —
> `<meta name="krdoc-date">`를 읽는 자리가 template · generator 어디에도 아직 없고, 날짜
> 필드를 여는 일은 장르마다 다른 stamp 관행을 다루는 ③ 단계의 범위다. ①의 footer 는 제목과
> 쪽번호만 인쇄한다.

## 1. 목표

현행 `korean-report-doc`은 시각 규약 하나를 산출한다. 품질은 높으나 진행현황 · 기술보고 · 제안서 ·
회의 자료 · 연구노트가 같은 골격(masthead → 초록 → 번호 절 → EOD)과 같은 인상으로 산출된다.

이 명세는 **장르 · theme · mode 조합에 따라 서로 다른 문서를 같은 품질로 산출하는 구조**를 정의한다.
고정의 단위가 달라진다. 지금은 스킨 하나가 고정되어 있고, 전환 후에는 token 구조 · 검사 규칙 ·
build 경로가 고정되며 그 위의 값과 조합이 변한다.

### 1.1 유지하는 원칙

| 원칙 | 내용 |
|---|---|
| 자립형 | 단일 HTML. font · 수식 · 도해를 내장하고 runtime network 를 요청하지 않는다 |
| 인쇄 1급 | 모든 규칙에 `@media print` 대응. deck 은 1 section = 1 page |
| data → 도해 | 좌표는 generator 가 계산한다. 수치를 손으로 입력하지 않는다 |
| 실패 시 중단 | 수식 오류 · 미치환 token · 넘침 · 없는 theme 은 exit 1 |
| 유채색 절제 | theme 마다 유채색 hue 는 accent 하나. `--mark` 는 독자 층위라 별도 |
| 문장 규약 분리 | 산문은 `korean-report-style`이 담당한다. 이 명세는 제작에 한정한다 |

## 2. 초안과 현행 code 의 대조

초안의 진단 중 일부는 현행 code 와 다르다. 조치는 확인 결과를 기준으로 정하였다.

| 초안의 진단 | 확인 결과 | 조치 |
|---|---|---|
| `figures.py` L22~28 hex 상수와 `base.css`의 이중 정의 | 상수는 code 에서 참조되지 않는다. SVG 는 `fi-*` · `st-*` class 만 방출한다. 두 값의 일치는 `tests/test_consistency.py:208`이 이미 검사한다 | 상수를 삭제하고, 검사를 class binding 검사로 대체한다 |
| `scripts/qa.py` · `examples/build_example.py` 미동봉 | 둘 다 존재한다. `scripts/qa.py`는 `assets/qa.py`의 호환 진입점이다 | 조치 없음 |
| KaTeX 의존성 절차 미정 | `package.json` · `package-lock.json`에 `katex`가 있다 | 조치 없음 |
| 본문 font 미동봉 | 확인. `.gitignore`가 `*.woff2`를 제외하고 NOTICE 가 「저장소에 포함되지 않으며」로 명시한다 | 정책을 개정하여 공식 subset 을 동봉한다(§4.4) |
| `keep-all` · `tabular-nums` 미설정 | 확인. `assets/css/`에 0건 | §4.3 |
| dark 재매핑이 `deck.css`의 `.dark`와 `@media print` 두 곳에 반복 | 확인 | `tokens.css` 한 곳으로 이전 |
| 글자 크기 · 행간 · 자간이 개별 상수이고 자간이 크기에 대해 비단조 | 확인. 본문 16.5px × 1.72 | §4.2 type scale |
| `design.md` 741줄 | 확인 | token 값을 나열하는 절만 `tokens.css` 참조로 대체한다. 전면 축약은 범위 밖 |

## 3. 결정 사항

| 항목 | 결정 | 근거 |
|---|---|---|
| 순서 | ① typesetting 기반 → ② theme → ③ 장르. 단계마다 PR 하나 | 장르 표가 장르별 기본 theme 을 지정하므로 theme 이 선행한다 |
| token 원천 | `tokens.css`를 손으로 관리하는 단일 원천으로 둔다. generator 는 두지 않는다 | CSS custom property 가 이미 token 체계다. 규칙은 pytest 가 강제한다 |
| 검증 | styleguide 와 `test_tokens.py`. pixel diff 는 제외 | 초기에는 값이 자주 변하여 baseline 갱신 비용이 크다. CI 의 windows 에서는 font 렌더가 달라 비교할 수 없다 |
| surface | `.dark` · `.black` class 를 유지한다 | `data-surface` 속성 전환은 기능 변화 없이 변경량만 증가시킨다 |
| `figures.py` 글자 크기 | 속성값을 유지한다 | label 좌표가 그 크기를 전제로 계산된다. theme 의 scale 을 따르면 label 이 넘친다 |
| 본문 font | Pretendard 공식 subset 을 repo 에 동봉한다 | 추가 code 가 없고 offline 에서도 결과가 결정적이다 |
| journal 본문 | Pretendard Light. serif 는 styleguide 비교 후 결정 | 추가 용량과 license 검토가 없다. theme 은 CSS 한 장이라 서체만 교체하기 쉽다 |
| 변수명 | 역할 기준으로 개편하고 기존 이름은 1.x 동안 alias 로 유지 | theme 이 `--parchment` 같은 색 이름의 값을 덮어쓰면 이름이 값을 오도한다 |
| 아젠다와 회의록 | 한 장르 `meeting` | 결정 칸이 비면 아젠다, 채워지면 회의록이다 |
| 벤치마크 | `report` 장르에 포함 | 골격(설정 → 결과 → 위협 요인 → 한계)이 같다 |
| `spec` theme 의 표 세로 괘선 | theme 단위 예외로 허용 | 현행 anti-pattern 은 editorial 기준이다. `design.md`에 예외 범위를 명시한다 |

## 4. ① typesetting 기반

### 4.1 `tokens.css`

`assets/css/tokens.css`를 신설한다. 삽입 순서는 `__FONTCSS__` → `__KATEXCSS__` → `__TOKENCSS__` →
`__THEMECSS__` → `__BASECSS__` → `__MODECSS__`이다.

- **색** — 역할 기준 이름. `--ink` · `--ink-2` · `--ink-3` · `--surface` · `--surface-2` · `--surface-3` ·
  `--rule-heavy` · `--rule` · `--rule-soft` · `--accent` · `--mark` · `--mark-ink` · `--fig-*`
- **투명도** — `rgba(0,102,204,.26)` 같은 리터럴을 `color-mix(in srgb, var(--accent) 26%, transparent)`로
  대체한다. theme 이 accent 를 교체하면 투명도 사용처도 따라간다. 미지원 browser 를 위해
  불투명 fallback 선언을 앞 줄에 둔다
- **type scale** — §4.2의 13단계. `--t-3` … `--t9`와 대응하는 `--lh*` · `--tr*`
- **space** — `--s-1` … `--s-10` = 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 80 · 96px
- **radius · font stack** — 현행 값 유지. font stack 은 `--font-body` · `--font-head` · `--mono`로 구분한다
- **surface 재매핑** — `.dark` · `.black`의 재정의를 `deck.css`에서 이전한다. paper 에서도 쓸 수 있다
- **print** — `@media print{:root{…}}`에서 scale 을 pt 로 일괄 재정의하고 dark · black 을 light 로 되돌린다.
  `paper.css` · `deck.css`의 규칙별 pt 값은 대부분 삭제한다
- **alias** — `--ink48` → `--ink-3`, `--primary` → `--accent`, `--parchment` → `--surface-2` 등. 1.x 동안 유지한다.
  저장소 안에서 기존 이름을 참조하는 곳은 `design.md`뿐이나, 사용자 generator 의 inline `var()`를 보호한다

**hex 리터럴은 `tokens.css`와 `themes/`에만 존재한다.** `base.css`의 `#fff` · `#e6e6e8` · `#8b8b90` ·
`#d5d9de`, `deck.css`의 `#5a5a60` · `#8b8b90`은 token 으로 이전한다.

### 4.2 type scale

기준 17px, 행간 28px, 비율 1.125, baseline 4px. 인쇄는 px × 0.6 을 0.5pt 단위로 반올림한다.
자간은 13.5px 이하에서 0, 15~17px 에서 −0.01em, 19px 이상에서 −0.012em 부터 −0.028em(49px)까지 선형이다.

| 단계 | px | 행간 | 자간 | 인쇄 pt / 행간 | 역할 |
|---|---|---|---|---|---|
| t-3 | 12 | 16 | 0 | 7 / 12 | 배지 · gantt 축과 marker label · EOD |
| t-2 | 13.5 | 20 | 0 | 8 / 12 | 캡션 · eyebrow · 표 머리 · `.cav` |
| t-1 | 15 | 24 | −0.01em | 9 / 14 | 표 본문 · 목록 · callout 본문 · 메타 |
| t0 | 17 | 28 | −0.01em | 10 / 16 | 본문 · `.claim` |
| t1 | 19 | 28 | −0.012em | 11.5 / 16 | 부제 · h4 |
| t2 | 21.5 | 32 | −0.013em | 13 / 20 | lead |
| t3 | 24 | 32 | −0.015em | 14.5 / 20 | h3 |
| t4 | 27 | 36 | −0.016em | 16 / 24 | h2 (paper) |
| t5 | 30.5 | 40 | −0.018em | 18.5 / 24 | 예비 |
| t6 | 34.5 | 44 | −0.020em | 20.5 / 28 | h2 (deck) · metric 수치(소) |
| t7 | 38.5 | 48 | −0.022em | 23 / 28 | 예비 |
| t8 | 43.5 | 52 | −0.025em | 26 / 32 | h1 (paper) · metric 수치 |
| t9 | 49 | 56 | −0.028em | 29.5 / 36 | hero (deck) |

현행 값과의 차이 중 가장 큰 것은 h3(18.5 → 24px)이다. **모든 문서의 인상이 달라지므로**
CHANGELOG 에 명시하고 minor version 을 올린다. `clamp()`를 쓰는 masthead 와 metric 은 양 끝을
scale token 으로 대체한다.

### 4.3 한글 typesetting 규칙

```css
html{word-break:keep-all;overflow-wrap:anywhere;line-break:strict}
table,.metric .mval,.gantt,.kv{font-variant-numeric:tabular-nums}
h1,h2,h3,.hero{text-wrap:balance}
```

`keep-all`은 어절 내부 줄바꿈을 금지하고 `overflow-wrap:anywhere`는 URL 같은 분절 불가 문자열의
넘침을 방지한다. 둘은 짝이다. `text-wrap:balance`는 Chromium 114 이상에서 적용되고 미지원 환경에서는
무시된다.

### 4.4 본문 font

- `assets/fonts/`에 Pretendard 1.3.9 **공식 배포본의 subset woff2** 3종(Regular · SemiBold · Light, 각 약
  267 KB)과 `LICENSE.txt`, 수록 글자 목록 `subset_glyphs.txt`를 동봉한다
- Pretendard 의 OFL 은 `Reserved Font Name 'Pretendard'`를 선언한다. 저장소가 subset 을 직접 생성하면
  수정본이 되어 그 이름을 쓸 수 없다. **공식 파일을 변경 없이 사용한다**
- `.gitignore`의 `*.woff2` 제외 규칙에 `assets/fonts/` 예외를 추가하고, NOTICE 의 「저장소에 포함되지
  않으며」를 개정한다
- `mathbuild.js`는 동봉 font 를 **기본으로 내장**한다. `--font`는 교체할 때만 쓴다. 내장 시 license 고지를
  싣는 현행 동작은 유지한다
- 본문에 `subset_glyphs.txt` 밖의 글자가 있으면 build 가 경고한다. 실패로 처리하지 않는다.
  font stack 의 system font 가 그 글자를 대신 표시한다
- plugin 크기와 산출 HTML 크기의 증가를 구현 시 실측하여 CHANGELOG 에 기록한다

### 4.5 PDF running footer

paper PDF 에 한하여 쪽번호/총쪽수 · 제목 · 날짜를 인쇄한다. `qa.py --pdf`가 Playwright 의
`display_header_footer` template 으로 처리한다. 제목과 날짜는 raw HTML 의 `<title>`과
`<meta name="krdoc-date">`에서 읽는다. deck 은 full-bleed tile 이므로 적용하지 않는다.

### 4.6 `figures.py`

- L22~28 의 hex 상수 7개를 삭제한다
- 글자 크기 속성값은 유지한다(§3)
- `tests/test_consistency.py:208`의 상수 대조 검사는 「`figures.py`가 방출하는 모든 `fi-*` · `st-*` class 에
  CSS binding 이 존재한다」로 대체한다

### 4.7 styleguide

`examples/build_styleguide.py`가 `dist/styleguide_{paper,deck}.html`을 생성한다. 실제 문서와 같은
`mathbuild.js` 경로를 통과하므로 styleguide 가 통과하면 문서도 같은 규칙으로 산출된다.
각 절은 `<section data-sg="<id>">`로 구분한다.

| id | 내용 |
|---|---|
| `tokens-color` | 색 swatch 와 surface 4종(light · parch · dark · black)에서의 대비비 |
| `tokens-type` | 13단계 각각에 한글 · 라틴 · 숫자 혼용 표준 문장 |
| `tokens-space` | space token 막대 |
| `comp-*` | 현행 component 전체 × surface 4종 |
| `fig-*` | 도해 7종 × light · dark |
| `math` | inline · display · 표 셀 안의 수식 |
| `check-keepall` | 긴 어절이 포함된 문단. 어절 중간 줄바꿈 0건 확인 |
| `check-tnum` | `1111` · `8888` · `0.35` · `12,340` 행. 자릿수 정렬 확인 |
| `check-punct` | 중간점 · 줄표 · 따옴표 · 단위 공백 견본 |
| `check-breaks` | 표 · 도해 · callout 이 page 경계에 걸리도록 배치한 검사 page |

표준 문장은 가상 사례에서 가져온다 — `A사 인라인 계측 3,240 m² · 검사 SDK v2.1 — 위치 오차 ±0.35 m,
갱신 주기 12 ms (실측)`. CI 는 Linux 에서 예제와 함께 styleguide 를 build 하고 `qa.py`로 검사한다.

### 4.8 `tests/test_tokens.py`

| 검사 | 판정 |
|---|---|
| hex 리터럴이 `assets/css/`와 template 중 `tokens.css` · `themes/` 밖에 존재. SVG 출력은 `test_figures.py`가 기존대로 검사한다 | 실패 |
| 사용된 `var()`가 정의되지 않음 | 실패 |
| alias 의 대상이 존재하지 않음 | 실패 |
| `--ink` · `--ink-2`와 surface 4종의 대비 < 4.5:1 | 실패 |
| `--ink-3`과 surface 의 대비 < 4.5:1 | 경고와 수치 기록. 값 조정은 §9 |
| `--accent`와 surface 의 대비 < 3:1 | 실패 |
| space · 행간 token 이 4 의 배수가 아님 | 실패 |
| 자간이 글자 크기에 대해 단조 감소가 아님 | 실패 |
| `figures.py`의 class 에 CSS binding 이 없음 | 실패 |

### 4.9 commit 순서와 완료 기준

1. 값 불변 이관 — `tokens.css` 분리와 alias. 이관 전후 예제 screenshot 의 PNG hash 가 동일해야 한다
2. 한글 typesetting 규칙
3. type scale 값
4. font 동봉과 기본 내장
5. `figures.py` 정리와 `test_tokens.py`
6. PDF running footer
7. styleguide 와 CI

완료 기준은 다음과 같다.

- 클린 checkout 에서 `examples/build_example.py` → `mathbuild.js` → `qa.py --pdf`가 경고 없이 통과한다
- `assets/css/`와 template 에서 hex 리터럴이 `tokens.css` 외에 존재하지 않는다
- `test_tokens.py`가 통과하고 본문 역할의 대비 실패가 0건이다
- styleguide 가 surface 4종 × 전 component 를 렌더한다
- `SKILL.md`가 참조하는 파일이 전부 실재한다

## 5. ② theme

### 5.1 원칙

**theme 은 token 만 덮어쓴다.** `themes/<name>.css`는 `[data-theme=<name>]{…}` block 하나로 구성되고
component 규칙을 포함하지 않는다. theme 이 조정해야 하는 형태는 ①에서 **knob token** 으로 미리 열어 둔다.

| knob | 기본값 | 역할 |
|---|---|---|
| `--measure` | 720px | paper 본문 폭 |
| `--rule-w-heavy` | 1px | 제목 · 표 머리 괘선 두께 |
| `--table-col-rule` | `none` | 표 세로 괘선 |
| `--metric-t` | `var(--t8)` | metric 수치 크기 |
| `--weight-body` | 400 | 본문 weight |

editorial 은 파일을 두지 않는다. ① 의 `tokens.css`가 곧 editorial 이다.

### 5.2 선택 흐름

- generator 가 `<html data-theme="…">`을 지정한다. `new-document.py`에 `--theme`을 추가한다
- `mathbuild.js`는 raw HTML 의 `data-theme`을 읽어 **그 theme 의 CSS 와 font 만** 내장한다
- 존재하지 않는 theme 이름은 exit 1
- 4 theme × 2 mode 가 모두 동작해야 한다. dark · black 재매핑은 공용이며 필요한 theme 만 추가로 재정의한다

### 5.3 theme 3종

| theme | 재정의하는 token | 용도 |
|---|---|---|
| `journal` | 본문 Pretendard Light, `--measure` 640px, 본문 행간 32px, 자간 0, 괘선 가늘게, accent 채도 하향 | 기술보고 · 연구노트 |
| `brief` | 본문 15/24px, space 한 단계씩 축소, radius 0, `--rule-w-heavy` 2px, `--metric-t` 확대, surface-2 비중 증가 | 진행현황 · 의사결정 요청 |
| `spec` | `--mono`를 code · key-value 의 key · 표 수치에 적용, `--table-col-rule` 허용, radius 축소 | SDK · API · interface 정의 |

### 5.4 font

- `journal`은 ① 의 Pretendard Light 를 사용한다. 추가 font 는 없다
- `spec`은 JetBrains Mono 공식 woff2 를 변경 없이 동봉한다. 한글은 Pretendard 로 fallback 된다.
  동봉 전에 license 원문과 Reserved Font Name 조항을 확인한다
- 현행 `--mono`는 system font stack 이라 기기마다 다르게 렌더된다. `spec`에서는 이 차이가 없어진다

### 5.5 검사와 완료 기준

`test_tokens.py`에 다음을 추가한다.

- theme 은 `:root`에 존재하는 key 만 재정의한다. 신설하면 실패
- theme 마다 §4.8 의 대비 검사를 surface 4종에 반복한다
- theme 마다 유채색 hue 가 accent 하나를 초과하면 실패. `--mark`는 제외한다
- theme 이 참조하는 font 파일이 실재한다

완료 기준은 `styleguide_{paper,deck}_{theme}.html` 8건과 `example_{paper,deck}_{theme}.html` 8건이
CI 에서 build 되고 `qa.py`를 통과하는 것이다. 같은 예제를 4 theme 으로 나란히 비교한다.

## 6. ③ 장르

### 6.1 장르 5종

| id | 문서 | 도입 block | 골격 | 기본 theme · mode |
|---|---|---|---|---|
| `status` | 진행현황 · 중간보고 | BLUF | 기간 대비 → 항목별 결과(수치 선행) → 리스크와 대응 → 다음 기간 → 요청 결정 | brief · paper |
| `report` | 기술보고 · 벤치마크 | 초록 | 설정 → 결과 → 위협 요인 → 한계 → 표기법 | journal · paper |
| `proposal` | 제안서 | 핵심 수치 masthead | 배경 → 제안 → 일정(gantt) → 비용 → 결정 매트릭스 | editorial · paper |
| `meeting` | 협의 아젠다 · 회의록 | 안건 목록 | 안건별 배경 · 논점 · 결정 → 액션 아이템 | editorial · deck |
| `note` | 연구노트 | 날짜 stamp | 가설 · 실험 · 관찰 entry 의 누적. 실패도 기록 | journal · paper |

theme 과 mode 는 사용자가 재지정할 수 있다.

### 6.2 추가 component

장르 골격이 실제로 사용하는 것만 추가한다. 모두 ① 의 token 만 참조하므로 theme 을 따른다.

| component | 구성 | 사용 장르 |
|---|---|---|
| `.bluf` | 한 줄 결론 · 수치 3개 · 요청 결정 | status |
| `.lead` | h2 아래 한 줄 요지 | 전체 |
| `.kv` | key-value block | report · proposal |
| `.entry` | 날짜 stamp · 가설 · 실험 · 관찰 label | note |
| `table.decisions` | 안건 · 결정 · 담당 · 기한 | meeting |
| `table.risk` | 리스크 · 영향 · 가능성 · 대응. 수준은 ●◐○ 형태로 부호화 | status |
| `table.revisions` | 개정 이력 | 전체(부록) |

HTML 구조가 단순하지 않은 `bluf` · `kv` · `entry`에만 `figures.py` helper 를 추가한다. 표 변형은 기존
`tbl(…, cls=)`로 생성한다.

### 6.3 파일 배치

- `assets/genres/<id>.html` — 장르별 skeleton body. 현행 `new-document.py`의 `PAPER_BODY`와
  `DECK_BODY`는 각각 `report`와 `meeting`으로 이전한다
- `references/genres.md` — 장르마다 필수 절 · 선택 절 · 사용 component · 기본 조합 · 금기를 한 문서에 정리한다
- `SKILL.md` §1 결정표 — 「mode 선택」을 「장르 → 기본 theme · mode, 사용자 재지정」으로 개정한다
- `new-document.py --genre <id> [--theme] [--mode]` — `--genre` 없이 `--mode`만 지정하면 현행처럼
  `report`(paper) 또는 `meeting`(deck)을 생성한다. 기존 사용법은 유지된다

### 6.4 예제와 완료 기준

`examples/build_genres.py`가 기존 가상 사례 「A사 — 인라인 계측 체계 확립과 수율 개선」 하나로
5 장르를 모두 산출한다. 같은 사안이 장르에 따라 다른 구조로 산출되는지 나란히 비교하는 것이
완료 기준이다. CI 는 Linux 에서 5건을 build 하고 `qa.py`로 검사한다.

### 6.5 검사

- `genres.md`의 장르 표와 `assets/genres/`의 파일 목록이 일치한다
- 장르 skeleton 이 모두 build 된다(`e2e` marker)
- skeleton 의 안내 문구가 `korean-report-style` lint 를 통과한다. `test_own_prose.py`의 대상에 포함한다
- 새 component 가 styleguide 에 등장한다

## 7. 범위 밖

| 항목 | 보류 사유 |
|---|---|
| 12컬럼 grid · sidenote · 마진 캡션 | journal 의 각주 문화는 이 grid 가 선행되어야 한다 |
| 새 도해 타입 · 도해 primitive | 장르가 요구하는 도해는 현행 7종으로 충족된다 |
| pixel 단위 visual regression | §3 |
| 전 component 명세 파일 · 목차 · 2D 리스크 매트릭스 · 커버 변형 · 서명 block | 장르 5종이 필수로 요구하지 않는다 |
| `fmt()` 숫자 표기 helper | 장르 구현 중 필요가 확인되면 추가한다 |
| `design.md` 전면 축약과 한국어화 | 이번 변경은 token 값을 나열하는 절의 대체로 한정한다 |

## 8. 리스크와 대응

| 리스크 | 대응 |
|---|---|
| Reserved Font Name 조항 | 공식 subset 을 변경 없이 사용한다. JetBrains Mono 도 동봉 전에 같은 조항을 확인한다 |
| subset 밖의 한글 | build 경고. system font 가 그 글자를 대신 표시한다 |
| 산출 HTML 크기 증가(font 내장 기본화) | 구현 시 실측한다. 과도하면 문서별 glyph subset 을 후속으로 검토한다 |
| `color-mix()` · `text-wrap:balance` 미지원 browser | 불투명 fallback 선언을 앞 줄에 둔다. balance 는 무시되어도 결과에 해가 없다 |
| `keep-all`로 좁은 표 셀의 넘침 | `overflow-wrap:anywhere`와 `qa.py`의 넘침 검사 |
| 값 변경으로 기존 사용자 문서의 인상 변화 | CHANGELOG 명시와 minor version 상향. alias 로 변수명 호환 유지 |
| theme 증가에 따른 CSS 총량 | `mathbuild.js`가 선택된 theme 만 내장한다 |

## 9. 미결 사항

- **비율 1.125 와 1.2** — 1.125 로 구현하고 styleguide 확인 후 확정한다
- **journal 의 serif 채택** — styleguide 에서 editorial 과의 차이가 부족하면 후속으로 검토한다
- **`--ink-3` 대비** — 흰 바탕에서 약 4.3:1 로 추정된다. ① 은 현행 값을 유지하고 경고를 기록하며,
  값 조정은 theme 단계에서 surface 별로 결정한다


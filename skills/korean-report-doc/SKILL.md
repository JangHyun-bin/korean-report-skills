---
name: korean-report-doc
description: Produce publication-grade Korean technical documents as self-contained HTML (and PDF) — progress reports, technical reports, research notes, meeting decks, benchmark write-ups. Use this whenever the user asks for a 보고서 · 진행현황 · 기술보고 · 연구노트 · 협의 자료 · 중간보고 · 제안서 as a document artifact rather than a chat answer, or says the Word/PowerPoint output looks bad, or asks for a "제대로 된 문서" / "HTML로 만들어줘" / "PDF로 뽑아줘". Ships a fixed design system, reusable paper and deck templates, native SVG figure builders, build-time KaTeX and font embedding, and a render-and-inspect QA loop. Pair with the korean-report-style skill for prose conventions.
---

# 한국어 기술 문서 제작

워드프로세서로는 나오지 않는 품질의 문서를, 자립형 HTML 한 파일로 제작한다.

**결과물의 조건 세 가지.**
디자인 시스템이 고정되어 매번 같은 품질이 나온다.
수치와 도해가 데이터에서 나오고 손으로 타이핑되지 않는다.
네트워크 없이 열어도, 인쇄해도 동일하게 보인다.

문장 규약은 `korean-report-style` 스킬이 담당한다. 이 스킬의 범위는 **제작**에 한정한다.

---

## 1. 시작 전 결정

### 1.1 모드

| | **paper** | **deck** |
|---|---|---|
| 용도 | 분석 · 벤치마크 · 기술보고 · 진행현황 | 회의 · 아젠다 · 의사결정 요청 |
| 방향 | 세로 | 가로 |
| 페이지 | 연속 흐름 | 1 섹션 = 1 페이지 |
| 본문 폭 | 720px | 1120px |
| 밀도 | 산문 전체 | 한 페이지에 한 가지 |
| 템플릿 | `assets/paper_template.html` | `assets/deck_template.html` |
| 본문 구조 | `<div class="doc">` 안의 `<section>` | `<section class="tile ...">` 나열 |

**섞지 않는다.** 문단이 긴 deck 은 잘못 조판된 보고서로 읽히고,
타일 배경을 쓴 paper 는 슬라이드를 잘못 인쇄한 것으로 읽힌다.

### 1.2 산출물 필요 여부

문서 산출물을 요청받았을 때만 작성한다. 설명·요약·분석은 대화로 답한다.
`보고서 만들어줘` · `PDF로 뽑아줘` · `문서로 정리해줘` 가 신호다.

---

## 2. 빌드 파이프라인

```
데이터 ──▶ 생성기(Python) ──▶ raw HTML (수식 마커 + 치환 토큰)
                                     │
                                     ▼
                       후처리(Node + KaTeX) — mathbuild.js
                       · ⟦I⟧ / ⟦D⟧ 렌더
                       · base.css + 모드 CSS 삽입
                       · Pretendard · KaTeX woff2 base64 내장
                                     │
                                     ▼
                          단일 .html ──▶ headless print ──▶ .pdf
```

템플릿은 치환 토큰만 담은 얇은 껍데기다. 실제 규칙은 `assets/css/` 에 있다.

| 토큰 | 채우는 주체 |
|---|---|
| `__TITLE__` · `__BODY__` | 생성기 |
| `__FONTCSS__` · `__KATEXCSS__` · `__BASECSS__` · `__MODECSS__` | `mathbuild.js` |

**CSS 를 템플릿에 직접 쓰지 않는다.** 두 템플릿이 규칙을 각자 복사해 두었다가
deck 의 인쇄 규칙이 paper 의 것에 덮인 사고가 있었다. 공통은 `css/base.css`,
모드별은 `css/paper.css` · `css/deck.css` 한 곳에만 둔다.

### 2.1 생성기 작성

```python
import sys; sys.path.insert(0, "<스킬경로>/assets")
from figures import tbl, wide, fig_gantt, fig_flow, figcap, esc, BADGE_MEAS

def I(t): return "⟦I⟧" + t + "⟦/I⟧"   # 인라인 수식
def D(t): return "⟦D⟧" + t + "⟦/D⟧"   # 디스플레이 수식

def sub(tpl, *args):
    """%s 를 순서대로 치환하고 %% 를 % 로 되돌린다"""
    out, i, ai = [], 0, 0
    while True:
        j = tpl.find("%s", i)
        if j < 0:
            out.append(tpl[i:]); break
        out.append(tpl[i:j]); out.append(str(args[ai])); ai += 1; i = j + 2
    return "".join(out).replace("%%", "%")

BODY = sub('''<section id="s1"><h2><span class="sn">1</span>제목</h2>
%s
</section>''', tbl(...))

TPL = open("paper_template.html", encoding="utf-8").read()
out = TPL.replace("__BODY__", BODY).replace("__TITLE__", "문서 제목")
open("raw.html", "w", encoding="utf-8").write(out)
```

**수식 구분자는 반드시 `⟦I⟧`·`⟦D⟧` 를 쓴다.** `%%I%%` 같은 ASCII 구분자는
`I(r"D")` 처럼 한 글자 수식에서 `%%D%%` 를 우연히 만들어 파서가 오인식한다.
실제로 겪은 버그다. 빌드가 구버전 마커를 발견하면 실패한다.

**치환 토큰을 주석이나 본문에 적지 않는다.** 파이썬 `str.replace` 는 모든 등장을
바꾸므로, 주석에 `__BODY__` 를 적어 두면 본문이 두 번 들어간다. 이것도 실제로 겪었다.

동작하는 전체 예시는 저장소의 `examples/build_example.py` 에 있다.

### 2.2 후처리

```bash
node mathbuild.js raw.html out.html \
     --assets <스킬경로>/assets \
     --font Pretendard-Regular.woff2 --font Pretendard-SemiBold.woff2
```

빌드 시점에 KaTeX 로 렌더하고, 렌더 결과가 참조하는 woff2 만 골라 base64 로 삽입한다.
전체 폰트는 1.2 MB, 실제 필요한 것은 160 KB 정도다.

**실패하면 exit 1 이다.** 수식 오류, 치환되지 않은 토큰, 구버전 마커,
없는 폰트 경로가 모두 빌드를 세운다. 조용히 잘못 렌더된 수식이 수식 없는 것보다 나쁘다.

`--font` 를 생략하면 경고만 내고 진행한다. 이때 문서는 읽는 사람의 시스템 폰트로
폴백되므로 조판이 기기마다 달라진다. 배포본에는 반드시 내장한다.

### 2.3 PDF

```bash
python scripts/qa.py out.html --pdf --shot shots/
```

직접 부르려면:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto('file:///abs/path/out.html'); pg.wait_for_timeout(2500)
    pg.pdf(path='out.pdf', format='A4', print_background=True)   # deck 은 landscape=True
    b.close()
```

`wait_for_timeout` 을 충분히 준다. 폰트·이미지 로드 전에 인쇄하면 깨진다.

---

## 3. 도해

**모든 도해는 인라인 SVG 다.** matplotlib PNG 를 만들지 않는다.
확대해도 선명하고, 토큰을 상속하고, 텍스트가 검색되고, 파일이 커지지 않는다.

`assets/figures.py` 에 7종이 준비되어 있다 — 타임라인 · 간트 · 카드그리드 ·
플로우 · 수직선 · 대비막대 · 산점. 좌표는 Python 에서 계산해 SVG 에 리터럴로 박는다.
브라우저 JS 로 계산하면 PDF 출력 시 동일하게 실행되지 않는다.

**색은 hex 가 아니라 클래스로 나간다**(`fi-*` 채움 · `st-*` 선). `base.css` 가
그 클래스를 CSS 변수에 연결하므로, 다크 타일 위에서 토큰만 바뀌면 도해가 따라간다.
hex 를 박으면 `#1d1d1f` 글자가 `#272729` 타일 위에서 사라진다.

상세 규약은 `references/figures.md` 참조.

### 3.1 래스터 예외

실제 도면·점군 위에 측정 데이터를 얹은 시각화는 SVG 로 손으로 그릴 수 없다.
이 경우에 한해 래스터를 허용하되 세 조건을 지킨다.

1. **base64 data URI 로 내장** — 상대 경로 참조는 파일이 이동하면 깨진다
2. **테두리를 두른다** — `.plate` 클래스를 쓴다 (1px hairline, 10px 반경, 최대 820px)
3. **수치는 네이티브로 병기** — 래스터가 판단 근거를 단독으로 나르지 않게

---

## 4. QA — 렌더 후 검사

**소스를 믿지 않는다.** 반드시 브라우저로 렌더해 검사한다.

```bash
python scripts/qa.py out.html --shot shots/
```

수식 마커·치환 토큰 잔존, 가로 넘침, 컨테이너를 넘는 표, CSS 삽입 실패,
viewBox 밖으로 나간 도해, 캡션 없는 도해를 검사하고 실패하면 exit 1 이다.

**deck 은 인쇄 레이아웃까지 검사한다.** 타일이 한 쪽(A4 가로 210mm)을 넘으면
실패하고 어느 타일이 몇 px 넘쳤는지 알린다. `.tile` 은 인쇄 시 `overflow:hidden`
이라 넘친 내용이 **조용히 잘린다** — deck 에서 가장 흔한 실패다.
넘치면 타입을 줄이지 말고 **섹션을 쪼갠다**(design.md §7.1).

### 4.1 사람이 봐야 하는 항목

기계가 못 잡는 것은 스크린샷과 PDF 로 확인한다.

**인쇄**
- [ ] 페이지 수가 의도와 맞음 (deck: 섹션 수 = 페이지 수)
- [ ] 표 · 수식 · 콜아웃이 페이지 경계에서 잘리지 않음
- [ ] 절반 이상 빈 페이지 없음
- [ ] 제목이 페이지 끝에 홀로 남지 않음
- [ ] 다크 타일이 인쇄 시 반전됨

**번호**
- [ ] 그림 · 표 · 절 · 리스크 번호가 연속
- [ ] 본문 참조(`§5.2`, `그림 8`)가 실재 대상을 가리킴

편집을 여러 번 하였다면 **매번** 돌린다. 항목 하나를 지우면 번호와 참조가 줄줄이 어긋난다.

---

## 5. 편집 요청 처리

문서 수정 요청은 텍스트 치환이 아니라 **구조 연산**으로 처리한다.

| 요청 | 함께 해야 할 것 |
|---|---|
| 항목 삭제 | 이후 번호 재정렬 · 본문 참조 갱신 · 요약문 검토 · 미사용 정의 제거 |
| 절 삭제 | 인자 목록 수 맞춤 · 도해 함수 미사용 여부 · 하위 절 번호 |
| 표 열 삭제 | 열이 사라져 무의미해진 도입 문장 · 남은 열의 정합 |
| 문구 완화 | 같은 표현이 도해 라벨 · 캡션 · 표 셀에도 있는지 전역 확인 |

**연쇄를 발견하면 알린다.** "S3 를 지우면 아래 요약문이 S4 를 참조하는데 함께 고칠까요"
처럼 묻는다. 조용히 고치면 사용자가 무엇이 바뀌었는지 모른다.

---

## 6. 판단이 필요한 지점

- **한계 서술 삭제** — 임의 기준 · 미측정 항목을 지우면 수치가 검증된 것처럼 읽힌다.
  삭제 요청을 받아도 한 줄로 옮겨 남길지 물어본다.
- **정정 고지** — 이전 공유 수치와 산출 기준이 달라졌다면, 톤을 낮추더라도 사실은 남긴다.
- **분석과 조판의 경계** — 데이터에서 관계를 찾아내는 것은 이 스킬의 범위 밖이지만,
  문서의 가치를 크게 좌우한다. 수치가 주어지면 정합성을 검증하고 이상이 있으면 알린다.

---

## 7. 참고 파일

- `references/design.md` — 색 · 타이포 · 컴포넌트 · 인쇄 규약 전체
- `references/figures.md` — 도해 7종의 사용법과 좌표 규약
- `assets/paper_template.html` · `assets/deck_template.html`
- `assets/css/base.css` · `assets/css/paper.css` · `assets/css/deck.css`
- `assets/figures.py` · `assets/mathbuild.js`

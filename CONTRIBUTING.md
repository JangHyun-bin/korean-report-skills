# 기여 안내

## 이 저장소의 실패 방식

여기서 난 사고는 거의 전부 한 가지 모양이었습니다. **문서는 X 라고 적혀 있는데
자산은 X 를 하지 않습니다.** 몇 가지 실례:

| 문서의 주장 | 실제 |
|---|---|
| "템플릿에 `.gantt` CSS 가 이미 있습니다" | 없었습니다. 간트가 스타일 없는 div 로 나왔습니다 |
| "`throwOnError:true` 로 빌드가 실패합니다" | catch 로 삼키고 exit 0 이었습니다 |
| "수식 마커는 `%%D%%`" | 빌더는 `⟦D⟧` 만 인식했습니다 |
| "도해가 색 토큰을 상속합니다" | hex 가 박혀 다크 타일에서 글자가 사라졌습니다 |
| "자립형 — 네트워크 없이 열립니다" | 템플릿이 CDN 에서 폰트를 불렀습니다 |
| "1 섹션 = 1 페이지" | 중복된 CSS 블록이 인쇄 규칙을 덮었습니다 |

`tests/test_consistency.py` 는 이 범주를 잡으려고 존재합니다.
**문서를 고쳤는데 검사가 실패하면, 대개 자산을 함께 고쳐야 한다는 뜻입니다.**

## 준비

```bash
npm install
pip install pytest playwright ruff
playwright install chromium
```

## 검사

```bash
npm test                # node + python 전부
npm run test:node       # mathbuild.js 의 실패 계약
pytest -q               # 정합성 · 기하 · 파이프라인
pytest -q -m "not e2e"  # 빠르게 (조립 검사 제외)
ruff check .
```

전부 통과해야 머지합니다. CI 가 같은 것을 돌립니다.

## 눈으로 봐야 하는 것

기계는 "가로로 넘쳤는가"는 잡지만 "읽히는가"는 못 잡습니다. 시각을 건드렸으면
직접 렌더해서 봅니다.

```bash
python examples/build_example.py
node plugins/korean-report/skills/korean-report-doc/assets/mathbuild.js \
     dist/example_deck_raw.html dist/example_deck.html \
     --assets plugins/korean-report/skills/korean-report-doc/assets
python scripts/qa.py dist/example_deck.html --pdf --shot dist/shots
```

`examples/build_example.py` 는 도해 7종·표·배지·콜아웃·메트릭·수식을 한 번씩
전부 씁니다. 새 컴포넌트를 넣었으면 여기에도 추가해 회귀 화면에 나오게 합니다.

특히 확인할 것:

- **다크 타일** — deck 4번째 타일. 도해 글자가 읽힙니다
- **인쇄** — deck 은 타일 수 = 쪽수여야 합니다
- **표·수식** — 페이지 경계에서 잘리지 않습니다

## 규칙

### CSS

**공통 규칙을 모드 파일에 복사하지 않습니다.** `css/base.css` 에 한 번만 씁니다.
`css/paper.css` · `css/deck.css` 는 그 모드에만 해당하는 것과 `@media print`
한 블록씩만 가집니다. 이 규칙이 깨져서 deck 인쇄가 paper 규칙에 덮였습니다.

**템플릿에 CSS 를 쓰지 않습니다.** 템플릿은 치환 토큰만 담은 껍데기입니다.

### 도해

**색은 클래스로 방출한다** — `fi-*`(채움) · `st-*`(선). hex 를 박으면
다크 타일에서 사라집니다. `figures.py` 의 팔레트 상수와 `base.css` 의 토큰은
검사로 묶여 있으므로 한쪽만 바꾸면 실패합니다.

**좌표는 y 가 아래로 증가합니다.** matplotlib 감각으로 쓰면 행이 뒤집힙니다.

**이상한 입력은 `ValueError` 로 즉시 실패시킵니다.** 폭이 음수인 사각형은
브라우저가 조용히 지운다 — 그게 제일 나쁩니다.

### 빌더

**실패하면 `exit 1`.** 수식 오류·미치환 토큰·구버전 마커·없는 폰트가 모두
빌드를 세웁니다. 경고로 낮추지 않습니다.

### 예시 — 실제 데이터를 넣지 않는다

이 저장소의 예시는 전부 가상 사례 「A사 — 인라인 계측 체계 확립과 수율 개선」입니다.
편의상 실제 프로젝트의 수치·일정·사고를 예시로 넣지 않습니다. 한 번 공개되면
이력을 재작성해도 옛 커밋 객체는 SHA 로 남습니다.

`tests/test_no_real_data.py` 가 막습니다 — 실재 조직·개인명, 이전 도메인 잔재,
스킬 산문의 구체 날짜, 치환표의 소수점 백분율(소수점이 붙으면 실측으로 읽힙니다).

새 예시가 필요하면 같은 가상 시나리오 안에서 만듭니다. 도메인 자체를 바꾸려면
치환표 전체가 따라 움직이므로 먼저 이슈로 논의합니다.

### 문서는 자기 규약을 지킨다

`tests/test_own_prose.py` 가 **치환표를 저장소 산문에 그대로 돌립니다.**
규칙 목록을 따로 만들지 않으므로 `substitutions.md` 를 고치면 검사도 함께 바뀝니다.

| | |
|---|---|
| 검사 대상 | `skills/**/*.md` · `docs/design/*.md` |
| 대상 아님 | README · INSTALL · CONTRIBUTING · SECURITY · CHANGELOG |

**대상이 아닌 문서가 있는 이유** — 규약은 보고서·협의 자료의 장르 규칙이고,
README 는 처음 온 사람이 자기 문제를 알아보게 하는 글입니다. 장르가 다르면 규칙도
다르다는 것 자체가 `korean-report-style` §7 이 규정하는 판단입니다. 그 사실은
README 에도 명시되어 있습니다.

검사가 보는 것은 둘입니다.

- **치환표 좌변**이 산문과 일반 표 셀에 등장하는가 — 코드 블록·인용문·백틱·「」 안은
  제외한다. 교육용 표는 알려진 헤더나 `<!-- style-teaching -->` 표식으로 명시한다.
- **절 제목이 명사구인가**(§1.1) — 서술형·의문형과 관형절형(`~하는 방법`·`~할 때`)을 잡습니다.

인용이 꼭 필요한데 위 예외로 안 되면 줄 끝에 `<!-- style-exempt -->` 를 단다.
§1.8 판정법처럼 그 단어를 반복해야 규칙이 성립하는 자리에만 씁니다.

### 문서

**없는 파일을 가리키지 않습니다.** 백틱으로 적은 경로는 검사가 실재를 확인합니다.

**건수·수치를 과장하지 않습니다.** README 의 치환 목록 건수는 실제 표 행 수와
대조됩니다. `korean-report-style` §3 이 요구하는 정확성을 저장소 자신에게도 적용합니다.

**코드 예시에 구버전 마커를 쓰지 않습니다.** 산문에서 "쓰지 말라"고 언급하는 것은 괜찮습니다.

## 커밋

제목은 명사구로 짧게, 본문에 이유를 적습니다. 무엇을 바꿨는지는 diff 가 말하므로
**왜 바꿨는지**를 적습니다.

```
deck 인쇄 규칙이 paper 규칙에 덮이던 문제 수정

deck_template.html 이 같은 <style> 블록을 두 번 담고 있었고,
뒤 블록이 paper 의 @media print 였다. 뒤가 이겨 hero 34pt 옆에
h2 14pt 가 붙었다. CSS 를 base/paper/deck 세 레이어로 분리해
중복이 구조적으로 불가능하게 만들었다.
```

## 릴리스

`v*` 태그를 밀면 CI 가 npm 패키지를 먼저 게시하고 `.skill` 두 개를 GitHub Release에
첨부합니다. tag는 `package.json`의 version과 정확히 같아야 합니다.

```bash
git tag v1.14.2 && git push origin v1.14.2
```

`package.json` · `package-lock.json` · `pyproject.toml` · plugin manifest 두 곳 · README
뱃지 · `INSTALL.md`의 version pin · `CHANGELOG.md`를 먼저 갱신합니다. 파일 간 version은
검사에서, tag와 version은 릴리스 job에서 대조합니다.

### npm trusted publisher — 최초 1회 설정

npmjs.com의 `korean-report-skills` 패키지 설정에서 GitHub Actions trusted publisher를
다음과 같이 등록합니다.

| 항목 | 값 |
|---|---|
| Organization or user | `JangHyun-bin` |
| Repository | `korean-report-skills` |
| Workflow filename | ci.yml |
| Allowed action | `npm publish` |

릴리스 job은 GitHub OIDC의 단기 자격을 사용하므로 `NPM_TOKEN` secret은 두지 않습니다.
이 설정이 없으면 npm 게시 단계에서 중단되고 GitHub Release는 생성되지 않습니다.
Trusted publishing과 tarball integrity 재현을 위해 릴리스 runner는 Node 24와 npm 11.6.2를
사용합니다.

npm 게시 뒤 GitHub Release 생성만 실패한 경우에는 같은 tag workflow를 재실행합니다.
registry의 tarball integrity가 현재 tag와 같으면 npm 게시는 건너뛰고 `.skill` 첨부를
계속합니다. 같은 version의 내용이 다르면 릴리스를 중단합니다.

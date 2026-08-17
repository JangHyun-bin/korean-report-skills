<img src="docs/assets/logo.svg" width="30" align="middle" alt=""> <b>korean-report-skills</b>

[![tests](https://img.shields.io/badge/tests-270%20tests-3fb950)](../../actions)
[![release](https://img.shields.io/badge/release-v1.14.1-0066cc)](../../releases)
[![plugin](https://img.shields.io/badge/plugin-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20OpenCode-8957e5)](INSTALL.md)
[![license](https://img.shields.io/badge/license-Apache--2.0-d29922)](LICENSE)

# 한국어 기술·사업 문서용 Agent Skills

`korean-report-skills`는 한국어 기술·사업 문서의 제작과 편집을 지원한다. 문서 산출물 제작과
편집 규약을 서로 다른 두 스킬로 제공하며, Claude Code, Codex, Cursor, OpenCode에서 사용할 수 있다.

## 제품 구성

| 스킬 | 역할 | 주요 요청 | 결과 |
|---|---|---|---|
| `korean-report-style` | 문체, 프레이밍, 용어 정확성, 상태·근거 표기, 편집 후 정합성 | 문단 수정, 보고 문체 교정, 기존 문서 검토 | 수정 원고와 검사 결과 |
| `korean-report-doc` | 디자인 시스템, paper·deck 조판, 도해, 수식, 빌드, 렌더 QA | 보고서·협의자료·제안서 등의 문서 산출물 제작 | 자립형 HTML과 선택적 PDF |

Claude Code·Codex `marketplace`의 플러그인 식별자는 `korean-report`이고, OpenCode npm
패키지 식별자는 `korean-report-skills`이다. 두 배포 경로 모두 위 두 스킬을 로드한다. 문체와
프레이밍 검토에는 `korean-report-style`만 적용할 수 있다. 문서 산출물 제작에는 `korean-report-doc`이
`korean-report-style`을 함께 참조한다.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.png">
  <img src="docs/assets/banner-light.png" alt="paper 보고서와 deck 협의자료 — 스킬이 생성한 문서 세 장">
</picture>

## 지원 범위

### 작업 유형

| 요청 | 적용 스킬 | 산출물 |
|---|---|---|
| 문장·문단 교정, 말투 조정, 기존 문서 검토 | `korean-report-style` | 대화 안의 수정 원고 또는 lint 결과 |
| 보고서·협의자료·제안서 파일 제작 | `korean-report-doc` + `korean-report-style` | 자립형 HTML, 필요 시 PDF |
| 설명·요약·분석만 요청 | 필요 시 `korean-report-style` | 대화 응답. 별도 문서 파일은 생성하지 않음 |

### 문서 장르

문서 제작 범위에는 진행현황, 중간보고, 기술보고, 연구노트, 벤치마크 보고, 협의자료,
회의 아젠다, 제안서가 포함된다. 문체 규약은 여기에 코드베이스 인수인계, 아키텍처 문서,
runbook, API reference, 모델 평가, 회의록, 컨소시엄 산출물을 추가로 포함한다.

문서 장르와 출력 모드는 별개다. 같은 진행현황도 분석과 기록이 중심이면 `paper`, 회의에서
의사결정 항목을 제시하면 `deck`을 선택한다.

### 출력 모드

| 항목 | `paper` | `deck` |
|---|---|---|
| 용도 | 분석, 벤치마크, 기술보고, 진행현황 | 회의, 아젠다, 의사결정 요청 |
| 방향 | 세로 | 가로 |
| 페이지 구조 | 연속 흐름 | 한 섹션을 한 페이지로 배치 |

두 모드의 구조와 인쇄 규칙은 서로 다르므로 한 문서에서 혼합하지 않는다.

### 제약

- 한국어 기술·사업 문서를 대상으로 한다. 다른 언어의 문체·조판 규약은 포함하지 않는다.
- 입력 자료에서 관계를 도출하는 데이터 분석은 별도 작업이다. 스킬은 제공된 수치와 서술의
  정합성을 검사하지만, 자료에 없는 사실이나 근거를 확정하지 않는다.
- 네이티브 `.docx`와 `.pptx` 파일은 생성하지 않는다. 정본 형식은 자립형 HTML이다.
- 법률·규제 적합성이나 외부 사실의 정확성을 보증하지 않는다. 기한·의무·책임이 포함된 서술은
  사용자가 제공한 근거 문서와 대조해야 한다.

## 산출물 계약

빌드 파이프라인은 다음 순서로 구성된다.

```text
자료·원고
  → Python 생성기와 문서 구조
  → 원시 HTML
  → Node와 KaTeX로 수식 렌더링, CSS 삽입, 자산 내장
  → 자립형 HTML 정본
  → 브라우저 렌더 QA
  → 선택적 PDF와 검사용 스크린샷
```

정본은 CSS, KaTeX CSS와 사용된 KaTeX 글꼴을 포함한 HTML 한 파일이다. 실행 시점에
외부 자원을 요청하지 않으므로 네트워크 없이 열고 인쇄할 수 있다.

본문 글꼴은 `--font`로 woff2 파일을 명시한 경우에만 HTML에 내장된다. 글꼴을 지정하지
않아도 빌드는 완료되지만 경고를 출력하고 시스템 글꼴을 사용한다. 이 경우 기기별 조판 차이가
발생할 수 있다.

PDF는 HTML 정본을 자동화 브라우저로 인쇄한 파생 산출물이다. 스크린샷은 화면·인쇄 배치를
검토하기 위한 QA 증거이며 정본을 대체하지 않는다.

## 설치 및 기본 사용

| 환경 | 권장 배포 채널 | 설치 식별자 |
|---|---|---|
| Claude Code | GitHub `marketplace` 플러그인 | `korean-report@korean-report-skills` |
| Codex | GitHub `marketplace` 플러그인 | `korean-report@korean-report-skills` |
| OpenCode | npm 플러그인 | `korean-report-skills` |
| Cursor | npm 파일 복사 설치 | `korean-report-skills` |

### Claude Code

```text
/plugin marketplace add JangHyun-bin/korean-report-skills
/plugin install korean-report@korean-report-skills
```

### Codex

```bash
codex plugin marketplace add JangHyun-bin/korean-report-skills
codex plugin add korean-report@korean-report-skills
```

### OpenCode

OpenCode는 npm 패키지를 플러그인으로 로드한다. `opencode.json`의 `plugin` 배열에 패키지 이름을
등록하면 `config` hook이 두 스킬의 경로를 추가한다.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["korean-report-skills"]
}
```

별도의 `npm i -g` 또는 `npx` 복사는 필요하지 않다. 설정을 반영하려면 OpenCode를 다시 시작한다.

### npm 파일 복사 설치

`npx` 명령은 Claude Code, Codex, Cursor의 스킬 디렉터리에 두 스킬을 복사한다. OpenCode의
npm 플러그인 등록과는 다른 설치 방식이다.

```bash
npx korean-report-skills                 # Claude Code · Codex · Cursor
npx korean-report-skills cursor          # Cursor만 선택
npx korean-report-skills --project       # 현재 프로젝트에 설치
npx korean-report-skills --remove        # 복사한 스킬 제거
```

설치 후 세션을 새로 시작하고 스킬 목록에서 `korean-report-doc`과 `korean-report-style`을 확인한다.
설치 위치, 갱신, 제거, claude.ai 업로드 절차는 [INSTALL.md](INSTALL.md)에 명시하였다.

### 자연어 사용

```text
지난주 벤치 결과로 기술보고서를 작성해 줘.
이 문단을 외부 협력사에 전달할 보고 문체로 수정해 줘.
이 진행현황에서 미측정 수치와 근거가 없는 주장을 표시해 줘.
```

Codex에서는 `$korean-report-doc`, Claude Code에서는 `/korean-report-doc`처럼 스킬을 명시할 수도 있다.

### 실행 의존성

`korean-report-style`은 추가 런타임 의존성이 없다. `korean-report-doc`의 HTML 빌드에는 Node 20
이상과 KaTeX가 필요하다. 렌더 QA, 스크린샷, PDF 출력에는 Python 3.11 이상, Playwright,
Chromium이 필요하다. 환경별 설치와 확인 명령은 [INSTALL.md](INSTALL.md)에 명시하였다.

## 품질 검사

### 편집 검사

`korean-report-style`의 lint는 Markdown과 HTML의 가시 텍스트를 검사한다. 현재 치환 목록 118건과
제목, 문맥 의존 표현, 어미 규칙을 다음 네 갈래로 보고한다.

| 갈래 | 의미 |
|---|---|
| 고침 | 검증된 어미 활용형. `--fix` 적용 가능 |
| 검토 | 문맥에 따라 선택해야 하는 표현 |
| 제목 | 명사구가 아닌 제목 |
| 의심 | `--heuristic`에서만 활성화되는 문맥 의존 표현 |

JSON, GitHub annotation, SARIF 출력을 지원한다. 모호한 용어 선택과 문맥 의존 표현은 자동으로
교정하지 않는다.

### 렌더 검사

브라우저 렌더 후 다음 항목을 검사한다.

- 수식 marker와 template token 잔존
- 문서와 표의 가로 넘침
- CSS token과 본문 글꼴 stack 적용
- SVG viewBox clipping과 캡션 누락
- `deck` section의 인쇄 페이지 초과

페이지 분할, 과도한 빈 공간, 제목의 고립, 다크 타일의 인쇄 반전은 스크린샷과 PDF로 확인한다.

### 저장소 회귀 검사

저장소의 Node·Python 검사는 builder, lint, template, CSS, 도해, 설치 manifest, 예시 산출물의
회귀를 검사한다. CI는 Ubuntu와 Windows에서 검사를 실행하고 README 이미지를 예시 문서에서 다시
생성하여 커밋된 이미지와 대조한다. 상단 검사 badge는 저장소에서 수집되는 검사 수와 연동한다.

## 적용 예시

아래 이미지는 같은 가상 원고를 기본 Markdown과 `paper` 모드로 각각 조판한 결과다.

<table>
<tr>
<th width="50%">기본 Markdown</th>
<th width="50%">paper 모드 적용</th>
</tr>
<tr>
<td><img src="docs/assets/ba_before.png" alt="스킬을 적용하지 않은 가상 문서"></td>
<td><img src="docs/assets/ba_after.png" alt="paper 모드를 적용한 가상 문서"></td>
</tr>
</table>

문체 규약은 표현 교정뿐 아니라 수치의 상태, 주장과 한계, 의사결정 요청의 근거를 함께 표시한다.

<img src="docs/assets/ba_after_body.png" alt="도해와 상태 배지가 조판된 가상 문서 본문" width="100%">

전후 원고와 규칙별 근거는 [examples/before_after.md](examples/before_after.md)에 있다. 예시의 기업,
공정, 인물, 수치는 모두 가상이다.

## 소스 저장소에서 직접 실행

이 절은 플러그인 사용법이 아니라 소스 저장소에서 생성기와 빌드 도구를 직접 실행하는
개발자 경로다.

```bash
npm install
python3 -m pip install playwright
python3 -m playwright install chromium

python3 scripts/new-document.py --title "문서 제목" --mode paper
python3 문서_제목.py
```

생성된 Python 파일의 `# 여기부터 고쳐 쓴다` 구간에서 본문, 표, 도해를 수정한다. 본문 글꼴을
HTML에 내장하려면 실행 시 woff2 경로를 지정한다.

```bash
python3 문서_제목.py --font Pretendard-Regular.woff2 --font Pretendard-SemiBold.woff2
python3 scripts/qa.py 문서_제목.html --pdf --shot shots/
```

문체 검사와 저장소 회귀 검사는 다음과 같이 실행한다.

```bash
python3 plugins/korean-report/skills/korean-report-style/assets/lint.py 초안.md
python3 plugins/korean-report/skills/korean-report-style/assets/lint.py 초안.md --fix
npm test
```

## 저장소 구조

```text
plugins/korean-report/
  skills/
    korean-report-doc/
      assets/                 template, CSS, figures.py, mathbuild.js, qa.py
      references/             design·figure 규약
    korean-report-style/
      assets/lint.py          문체 검사기
      references/             치환 규칙·software handoff heuristic
.claude-plugin/               Claude Code·Codex marketplace 선언
.opencode/                    OpenCode npm plugin adapter
bin/install.js                Claude Code·Codex·Cursor file-copy 설치기
scripts/                      생성기, QA, 패키징, 이미지 생성
tests/                        정합성·회귀·end-to-end 검사
```

문체 규칙은 Markdown 표를 검사의 단일 원천으로 사용한다. `base.css`에는 공통 디자인 token,
`paper.css`와 `deck.css`에는 모드별 규칙이 있다. 도해는 SVG class를 공통 token에 연결한다.

새 문체 규칙과 문맥 heuristic은 현재 구조 안에서 추가할 수 있다. 새 출력 모드, 글꼴 정책,
언어 지원은 template, builder, QA, 회귀 검사를 함께 변경해야 한다. 현재 버전은 한국어 규약만 제공한다.

## 기여와 보안

기여 절차와 회귀 검사 기준은 [CONTRIBUTING.md](CONTRIBUTING.md)에 있다. 보안 취약점은 공개 issue가
아니라 [Security Advisory](../../security/advisories/new)로 신고한다. 세부 정책은
[SECURITY.md](SECURITY.md)에 명시하였다.

## 라이선스

[Apache-2.0](LICENSE)

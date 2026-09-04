# 설치

`korean-report` 플러그인에는 `korean-report-doc`과 `korean-report-style` 두 스킬이
포함되어 있습니다. 실행 환경에 맞는 설치 경로 하나를 선택합니다.

| 실행 환경 | 권장 배포 경로 | 갱신 방법 |
|---|---|---|
| Claude Code | 플러그인 `marketplace` | `marketplace` 갱신 |
| Codex | 플러그인 `marketplace` | `codex plugin marketplace upgrade` |
| Cursor | npm 설치기로 파일 복사 | 설치기 재실행 |
| OpenCode | npm 플러그인 | 패키지 버전 갱신 |

파일 복사 방식은 Claude Code와 Codex에서도 사용할 수 있습니다. 복사본은 `marketplace`와
연결되지 않으므로 설치기를 다시 실행해야 갱신됩니다.

## Claude Code

```text
/plugin marketplace add JangHyun-bin/korean-report-skills
/plugin install korean-report@korean-report-skills
```

설치 후 플러그인 재로드를 요청받으면 `/reload-plugins`를 실행합니다. 등록된 `marketplace`를
새로 조회할 때는 다음 명령을 사용합니다.

```text
/plugin marketplace update korean-report-skills
```

프로젝트 구성원에게 설치를 안내하려면 `.claude/settings.json`에 `marketplace`를 등록합니다.

```json
{
  "extraKnownMarketplaces": {
    "korean-report-skills": {
      "source": {
        "source": "github",
        "repo": "JangHyun-bin/korean-report-skills"
      }
    }
  }
}
```

## Codex

```bash
codex plugin marketplace add JangHyun-bin/korean-report-skills
codex plugin add korean-report@korean-report-skills
codex plugin list
```

Git `marketplace`의 snapshot을 갱신한 뒤 설치 버전을 다시 확인합니다.

```bash
codex plugin marketplace upgrade korean-report-skills
codex plugin list
```

제거 명령은 다음과 같습니다.

```bash
codex plugin remove korean-report@korean-report-skills
```

## Cursor와 파일 복사 설치

게시된 npm 패키지는 Claude Code, Codex, Cursor의 스킬 경로에 두 폴더를 복사합니다.
인자를 생략하면 세 환경에 모두 설치합니다.

```bash
npx korean-report-skills
npx korean-report-skills cursor
npx korean-report-skills --project
npx korean-report-skills --remove
```

특정 GitHub revision을 직접 설치해야 할 때만 GitHub spec을 사용합니다.

```bash
npx github:JangHyun-bin/korean-report-skills cursor
```

`--project`는 현재 저장소의 `.claude/skills`, `.codex/skills`, `.cursor/skills`에
복사합니다. 개인 설치 경로에 적용하려면 이 옵션을 생략합니다.

Node 없이 파일만 복사하려면 저장소를 복제한 뒤 셸 설치기를 실행합니다.

```bash
bash scripts/install.sh
bash scripts/install.sh codex cursor
bash scripts/install.sh --project
```

셸 설치기에는 Node가 필요하지 않습니다. `korean-report-doc`으로 문서를 빌드할 때는
Node 20 이상이 별도로 필요합니다.

## OpenCode

프로젝트 또는 전역 `opencode.json`의 `plugin` 배열에 npm 패키지를 등록합니다.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["korean-report-skills"]
}
```

OpenCode를 다시 시작하면 플러그인의 `config` hook이 패키지에 포함된 두 스킬 경로를
`skills.paths`에 추가합니다. 버전을 고정해야 하면 npm spec을 명시합니다.

```json
{
  "plugin": ["korean-report-skills@1.18.0"]
}
```

제거할 때는 `plugin` 배열에서 항목을 삭제하고 OpenCode를 다시 시작합니다.

## 설치 확인

새 세션에서 스킬 목록을 엽니다. `korean-report-doc`과 `korean-report-style`이 모두
표시되어야 합니다.

```text
/skills
```

파일 복사 설치의 기본 경로는 다음과 같습니다.

| 실행 환경 | 개인 경로 | 프로젝트 경로 |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `./.claude/skills/` |
| Codex | `~/.codex/skills/` | `./.codex/skills/` |
| Cursor | `~/.cursor/skills/` | `./.cursor/skills/` |
| OpenCode 수동 설치 | `~/.config/opencode/skills/` | `./.opencode/skills/` |

각 스킬 폴더의 바로 아래에 `SKILL.md`가 있어야 합니다. 예를 들어
`korean-report-doc/SKILL.md`는 인식되지만 폴더가 한 번 더 중첩된 경로는 인식되지 않습니다.

## 기본 사용

설치 후 에이전트에 작업을 요청합니다. 저장소 복제나 로컬 스크립트 실행은 필요하지 않습니다.

```text
지난주 벤치 결과로 기술보고서를 작성해 줘.
이 문단의 문체와 상태 표현을 검토해 줘.
```

Codex에서는 스킬을 명시적으로 지정할 수도 있습니다.

```text
$korean-report-doc 이 데이터로 진행현황 문서를 작성해 줘.
```

문체·프레이밍·정확성 검토에는 `korean-report-style`만 적용됩니다. HTML이나 PDF 산출물 제작에는
`korean-report-doc`과 `korean-report-style`이 함께 적용됩니다.

## 문서 빌드 의존성

`korean-report-style`은 추가 런타임 의존성이 없습니다. `korean-report-doc`의 HTML
빌드에는 Node 20 이상과 KaTeX가 필요합니다.

```bash
npm install katex
```

렌더 QA, 스크린샷 및 PDF 출력에는 Python 3.11 이상, Playwright와 Chromium이 필요합니다.

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

기준 HTML에는 CSS와 KaTeX 수식 글꼴이 내장됩니다. 본문 글꼴까지 내장하려면 사용 권한이
있는 WOFF2 파일을 `mathbuild.js`의 `--font` 인자로 지정합니다. 본문 글꼴을 지정하지 않으면
빌드는 완료되지만 시스템 폰트에 따라 `typesetting` 결과가 달라질 수 있습니다.

```bash
DOC_SKILL=/absolute/path/to/korean-report-doc

node "$DOC_SKILL/assets/mathbuild.js" raw.html report.html \
  --assets "$DOC_SKILL/assets" \
  --font Pretendard-Regular.woff2 \
  --font Pretendard-SemiBold.woff2

python3 "$DOC_SKILL/assets/qa.py" report.html --pdf --shot shots
```

## 소스 체크아웃

저장소의 scaffold와 예제는 개발 및 규칙 확장용입니다. 플러그인 설치만 한 사용자에게는
루트 `scripts/` 경로가 제공되지 않습니다.

```bash
git clone https://github.com/JangHyun-bin/korean-report-skills.git
cd korean-report-skills
npm install
python3 -m pip install playwright pytest
python3 -m playwright install chromium
python3 scripts/new-document.py --title "분기 기술보고" --mode paper
```

claude.ai 웹에 업로드할 `.skill` 압축 파일도 소스 저장소에서 생성합니다. Bash, `zip`,
`unzip`이 필요합니다.

```bash
npm run pack
```

`dist/korean-report-doc.skill`과 `dist/korean-report-style.skill`을 Claude의
Settings → Capabilities에서 각각 업로드합니다.

## 실행 코드와 권한

Claude Code, Codex, Cursor의 파일 복사 설치에는 install hook이 없습니다. 복사된 스킬에는
지시문, 참조 문서, HTML·CSS 자산, Python·Node 스크립트가 포함됩니다. 문서 빌드나 검사를
요청하면 에이전트가 해당 스크립트를 실행할 수 있습니다.

OpenCode는 패키지를 읽을 때 JavaScript `config` hook을 실행합니다. 이 hook은 패키지 안의
스킬 디렉터리를 `skills.paths`에 추가합니다. 저장소와 배포 내용을 확인한 뒤 설치합니다.

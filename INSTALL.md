# 설치

두 스킬 모두 **Agent Skills 표준(SKILL.md)** 을 따르므로
Claude Code · Codex · Cursor 에 **파일 수정 없이** 그대로 들어간다.

경로는 셋이며 아래 순서로 권한다.

| | 대상 | 갱신 |
|---|---|---|
| 플러그인 | Claude Code · Codex | 자동 |
| npx | Cursor · 위 둘 | 다시 실행 |
| 셸 스크립트 | 위와 같음 (node 없는 환경) | 다시 실행 |

## 플러그인 — Claude Code · Codex

이 저장소가 곧 마켓플레이스다. 두 도구가 같은 선언 파일을 읽으므로
저장소 주소 하나로 양쪽 다 설치된다.

Claude Code:

```
/plugin marketplace add JangHyun-bin/korean-report-skills
/plugin install korean-report@korean-report-skills
```

Codex:

```bash
codex plugin marketplace add JangHyun-bin/korean-report-skills
codex plugin add korean-report@korean-report-skills
```

`codex plugin list` 로 확인하고 `codex plugin remove korean-report@korean-report-skills` 로
지운다. 대화 중에는 `/plugins` 로 연다.

설치 요약이 `Run /reload-plugins to activate.` 라고 하면 그 명령을 실행한다.
`/plugin` 을 열면 **Installed** 탭에서 켜고 끄거나 지울 수 있다.

셸에서 바로 설치하려면:

```bash
claude plugin install korean-report@korean-report-skills --scope user
```

**갱신** — 마켓플레이스를 등록해 두면 새 버전이 자동으로 따라온다.
직접 당기려면 `/plugin marketplace update korean-report-skills`.

**팀 전체에 적용** — 프로젝트의 `.claude/settings.json` 에 아래를 넣으면
팀원이 저장소를 신뢰할 때 설치를 안내받는다.

```json
{
  "extraKnownMarketplaces": {
    "korean-report-skills": {
      "source": { "source": "github", "repo": "JangHyun-bin/korean-report-skills" }
    }
  }
}
```

## npx — Cursor, 그리고 플러그인을 쓰지 않을 때

파일로 직접 복사한다. 게시 없이 GitHub 에서 바로 실행된다.

```bash
npx github:JangHyun-bin/korean-report-skills            # claude · codex · cursor 전부
npx github:JangHyun-bin/korean-report-skills cursor     # 골라서
npx github:JangHyun-bin/korean-report-skills --project  # 이 저장소에만
npx github:JangHyun-bin/korean-report-skills --remove   # 되돌리기
```

`--project` 로 넣고 커밋하면 팀원이 클론만 해도 같은 스킬을 쓴다.

## 셸 스크립트 — node 가 없을 때

```bash
bash scripts/install.sh                 # 전부
bash scripts/install.sh codex cursor    # 골라서
bash scripts/install.sh --project       # 이 저장소에만
```

## 수동

```bash
mkdir -p ~/.claude/skills
cp -R plugins/korean-report/skills/korean-report-doc plugins/korean-report/skills/korean-report-style ~/.claude/skills/
```

| 도구 | 개인 | 프로젝트 |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `./.claude/skills/` |
| Codex | `~/.codex/skills/` | `./.codex/skills/` |
| Cursor | `~/.cursor/skills/` | `./.cursor/skills/` |

Claude Desktop 은 Claude Code 와 같은 `~/.claude/skills/` 를 읽는다. 한 번 넣으면 둘 다 쓴다.

> `~/.agents/skills/` 를 공용 경로로 쓰는 도구도 있으나(OpenCode 등)
> **Claude Code 와 Codex 는 각자의 경로만 읽는다.** 위 표대로 넣는다.

## claude.ai 웹

```bash
npm run pack        # dist/korean-report-doc.skill · dist/korean-report-style.skill
```

만들어진 `.skill` 파일을 **Settings → Capabilities** 에서 업로드한다.
Pro · Max · Team · Enterprise 에서 코드 실행이 켜져 있어야 한다.

---

## 확인

**세션을 새로 시작한 뒤**:

```
/skills
```

목록에 `korean-report-doc` 과 `korean-report-style` 이 보이면 된다.
보이지 않으면 경로를 확인한다.

```bash
ls ~/.claude/skills/    # Claude Code
ls ~/.codex/skills/     # Codex
ls ~/.cursor/skills/    # Cursor
```

각 폴더 안에 `SKILL.md` 가 바로 있어야 한다.
한 겹 더 들어가 있으면(`korean-report-doc/korean-report-doc/SKILL.md`) 인식되지 않는다.

## 쓰는 법

**자동** — 요청이 설명과 맞으면 알아서 걸린다.

```
지난주 벤치 결과로 기술보고서 만들어줘
이 문단 말투 좀 다듬어줘
```

**명시적** — Codex 는 `$` 접두어를 쓴다.

```
$korean-report-doc  이 데이터로 진행현황 문서 만들어줘
```

Claude Code 는 `/korean-report-doc` 으로 부른다.

## 끄기 · 지우기

```bash
mv ~/.claude/plugins/korean-report/skills/korean-report-doc ~/.claude/skills/_korean-report-doc   # 임시로 끄기
rm -rf ~/.claude/plugins/korean-report/skills/korean-report-doc                                    # 삭제
```

---

## 실행에 필요한 것

`korean-report-doc` 이 실제로 문서를 빌드하려면:

```bash
npm  install katex
pip  install playwright && playwright install chromium
```

### 본문 폰트

문서는 **네트워크 없이 열려야 한다**(design.md §0.2). 그래서 Pretendard 를
CDN 에서 부르지 않고 빌드 시점에 내장한다. woff2 를 받아 `--font` 로 지정한다.

```bash
curl -L -o Pretendard-Regular.woff2 \
  https://github.com/orioncactus/pretendard/raw/main/packages/pretendard/dist/web/static/woff2/Pretendard-Regular.woff2
curl -L -o Pretendard-SemiBold.woff2 \
  https://github.com/orioncactus/pretendard/raw/main/packages/pretendard/dist/web/static/woff2/Pretendard-SemiBold.woff2

node plugins/korean-report/skills/korean-report-doc/assets/mathbuild.js raw.html out.html \
     --assets plugins/korean-report/skills/korean-report-doc/assets \
     --font Pretendard-Regular.woff2 --font Pretendard-SemiBold.woff2
```

한글 전체 자족을 담은 woff2 는 굵기당 1 MB 안팎이다. 문서가 커지는 것이 부담이면
`pyftsubset` 으로 실제 쓰인 글자만 남긴 서브셋을 만들어 지정한다.

`--font` 를 주지 않으면 빌드는 통과하되 경고가 뜨고, 읽는 사람의 시스템 폰트로
폴백된다. 조판이 기기마다 달라지므로 배포본에는 반드시 내장한다.

`korean-report-style` 은 문장 규약이라 의존성이 없다.

## 주의

스킬은 에이전트가 읽는 지시문이다. 출처를 모르는 스킬은 설치하지 않는다.
이 둘은 `SKILL.md` 와 참조 문서, 템플릿, 파이썬·노드 스크립트로만 이루어져 있고
설치 시 자동 실행되는 코드는 없다.

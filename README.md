# 한국어 문서 스킬셋

한국어 기술 문서를 **자립형 HTML 한 파일**로 만드는 제작 스킬과, 그 문서의
**문장 규약**을 담당하는 문체 스킬. Agent Skills 표준(`SKILL.md`)을 따르므로
Claude Code · Codex · Cursor 에 파일 수정 없이 들어간다.

설치는 [INSTALL.md](INSTALL.md) 참조. 요약하면 `bash scripts/install.sh` 한 줄.

---

## 무엇이 달라지나

같은 내용을 두 번 썼다. 사실은 하나도 바꾸지 않았다 — 수치도, 원인도, 요청도 같다.

<table>
<tr>
<th width="50%">전 — 평소 쓰는 방식</th>
<th width="50%">후 — 두 스킬 적용</th>
</tr>
<tr>
<td><img src="docs/assets/ba_before.png" alt="스킬 없이 작성한 문서"></td>
<td><img src="docs/assets/ba_after.png" alt="스킬을 적용한 문서"></td>
</tr>
</table>

| 전 | 후 |
|---|---|
| 문의 대응이 왜 느려졌나 | 문의 대응 지연의 구조와 개선 방향 |
| 반토막 넘게 늘었습니다 | 4.2시간에서 9.1시간으로 증가하였다 |
| 템플릿이 죽어 있어서 | 템플릿이 비활성 상태였으므로 |
| 엉뚱한 팀으로 넘어가고 | 담당 팀이 아닌 곳으로 이관되고 |
| 원인 분석에서 드러난 결함 세 가지 | 구조적 개선 — 분류 체계 정비와 자동응답 복구 |
| 야간 인력을 얼마나 늘릴지 정해 주십시오 | 3명 증원을 산정하였다. 근거는 부록 A. 조정 요청 |

본문은 도해·상태 배지·캡션이 함께 조판된다.

<img src="docs/assets/ba_after_body.png" alt="도해와 상태 배지가 조판된 본문" width="100%">

전체 대조와 규칙별 근거는 [examples/before_after.md](examples/before_after.md) 참조.
이 예시의 주제(고객 문의 대응)가 저장소의 다른 예시(반도체 계측)와 다른 것은 의도한 것이다 —
**규칙이 분야에 묶이지 않는다는 것을 보이기 위해서다.**

---

## korean-report-doc — 문서 제작

- `SKILL.md` — 모드 선택(paper/deck), 빌드 파이프라인, QA 절차, 편집 요청 처리
- `references/design.md` — 색 · 타이포 · 컴포넌트 · 인쇄 규약
- `references/figures.md` — 도해 7종 사용법
- `assets/paper_template.html` · `deck_template.html` — 치환 토큰만 담은 얇은 껍데기
- `assets/css/{base,paper,deck}.css` — 공통 레이어 + 모드 레이어
- `assets/figures.py` — 도해 · 표 생성 헬퍼
- `assets/mathbuild.js` — CSS · 폰트 · KaTeX 를 빌드 시점에 내장

## korean-report-style — 문장 규약

- `SKILL.md` — 문체 · 프레이밍 · 정확성 · 편집 후 정합성
- `references/substitutions.md` — 치환 목록 115건

예시는 모두 가상 사례 「A사 — 인라인 계측 체계 확립과 수율 개선」에서 가져왔다.
실재하는 기업·공정·수치가 아니며, 도메인은 예시일 뿐이고 규칙 자체는 분야를 가리지 않는다.
왜 이 도메인인지는 [결정 기록](docs/decisions/2026-08-10-example-domain-swap.md) 참조.

## 관계

doc 이 절차를 잡고 style 이 문장을 다듬는다.
doc 의 `SKILL.md` 가 style 을 참조하므로 둘이 함께 걸린다.
짧은 글을 다듬을 때는 style 만 걸린다.

## 저장소 구조

```
skills/          두 스킬. 이 폴더가 그대로 ~/.claude/skills/ 로 복사된다
scripts/         install.sh · qa.py · pack-skills.sh
examples/        build_example.py — SKILL.md §2 파이프라인의 참조 구현
tests/           문서와 자산이 어긋나면 실패하는 검사
dist/            빌드 산출물 (git 추적 안 함)
```

## 개발

```bash
npm install                                   # katex
pip install playwright pytest && playwright install chromium

npm test                                      # node + python 검사
python examples/build_example.py              # dist/example_*_raw.html
node skills/korean-report-doc/assets/mathbuild.js \
     dist/example_paper_raw.html dist/example_paper.html \
     --assets skills/korean-report-doc/assets
python scripts/qa.py dist/example_paper.html --pdf --shot dist/shots
```

`tests/` 는 이 저장소에서 실제로 났던 사고의 회귀를 막는다 — 중복된 CSS 블록,
문서만 존재하고 구현되지 않은 클래스, 좌표계 역전, 음수 폭, 구버전 수식 마커,
없는 파일을 가리키는 문서. 자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md) 참조.

## 라이선스

[Apache-2.0](LICENSE)

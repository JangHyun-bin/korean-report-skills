# 보안

## 이 저장소가 가진 특수한 위험

여기 담긴 것은 라이브러리가 아니라 **에이전트가 읽고 그대로 따르는 지시문**이다.
`SKILL.md` 한 줄을 바꾸면 그 스킬을 설치한 모든 사람의 에이전트 행동이 바뀐다.
일반적인 코드 취약점보다 이쪽 경로가 더 중요하다.

특히 다음을 취약점으로 취급한다.

- **지시문 주입** — `SKILL.md`·참조 문서에 삽입된, 문서 작성과 무관한 지시
  (예: 파일 유출, 임의 명령 실행, 다른 스킬 무력화)
- **빌드 스크립트의 임의 실행** — `figures.py`·`mathbuild.js`·`scripts/*`가
  입력 데이터로 임의 코드를 실행하게 되는 경로
- **산출물 오염** — 생성된 HTML에 의도하지 않은 스크립트·외부 요청이 들어가는 경우.
  이 저장소는 **런타임 네트워크 의존 0**을 원칙으로 하며, 검사가 이를 강제한다
- **공급망** — `.skill` 아카이브가 `skills/` 폴더와 다른 내용을 담는 경우.
  `bash scripts/pack-skills.sh --verify` 가 대조한다

## 신고

취약점은 **공개 이슈로 올리지 않는다.**
GitHub의 [Security Advisory](https://github.com/JangHyun-bin/korean-report-skills/security/advisories/new)
로 비공개 신고한다.

포함해 주면 좋은 것 — 영향받는 파일, 재현 절차, 예상되는 피해 범위.

첫 응답까지 영업일 기준 5일을 목표로 한다.

## 설치자가 확인할 것

스킬은 출처를 모르면 설치하지 않는다. 이 저장소는 다음을 지킨다.

- **설치 시 자동 실행되는 코드가 없다.** `scripts/install.sh` 는 파일 복사만 한다
- 실행 자산은 `figures.py`(문자열 생성) · `mathbuild.js`(빌드) 뿐이며,
  둘 다 네트워크에 접근하지 않는다
- 생성 문서는 자립형이다 — 외부 자원을 런타임에 부르지 않는다

설치 전 직접 확인하려면:

```bash
grep -rn "http" plugins/korean-report/skills/            # 외부 참조 여부
grep -rn "exec\|eval\|subprocess" plugins/korean-report/skills/   # 실행 경로 여부
```

## 지원 범위

최신 릴리스만 지원한다. 이전 버전에는 수정을 소급하지 않는다.

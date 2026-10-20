# 외래어 영문 표기

`.krstyle.toml` 의 `[lint]` 에 `loanwords = "english"` 를 지정하거나 `lint.py --loanwords english`
로 실행할 때만 적용하는 표다. 기본 정책(`keep`)은 `substitutions.md` §7.2 를 따른다 —
규격 · API 에 등장하는 말은 영문, 분야에 정착한 개념어는 한글 음차를 유지한다.

조직에 따라 영어에서 온 낱말을 전부 영문으로 표기하는 정책을 쓴다. 이 경우 한글 음차는
원어와 1:1 로 대조되지 않아 검색 · 대조 비용이 증가한다. 아래 표는 기술 문서에서 자주 등장하는
음차의 예시이며 목록이 아니다.

## 1. 음차 → 영문

| 쓰지 않는다 | 쓴다 |
|---|---|
| 카메라 | camera |
| 서버 | server |
| 데이터 | data |
| 시스템 | system |
| 모델 | model |
| 센서 | sensor |
| 모드 | mode |
| 파일 | file |
| 폴더 | folder |
| 디렉터리 | directory |
| 링크 | link |
| 페이지 | page |
| 키워드 | keyword |
| 로그 | log |
| 테스트 | test |
| 코드 | code |
| 프로그램 | program |
| 스크립트 | script |
| 메모리 | memory |
| 프로세서 | processor |
| 스마트폰 | smartphone |
| 컴퓨터 | computer |
| 네트워크 | network |
| 디바이스 | device |
| 클라이언트 | client |
| 인터페이스 | interface |
| 파이프라인 | pipeline |
| 템플릿 | template |
| 이미지 | image |
| 픽셀 | pixel |
| 프레임 | frame |
| 버전 | version |
| 빌드 | build |
| 패키지 | package |
| 라이브러리 | library |
| 플러그인 | plugin |
| 토큰 | token |
| 세션 | session |
| 게이트 | gate |
| 가드 | guard |

인용 · inline code · 「」 안은 검사하지 않는다. 고유명사 안의 음차(제품명 · 문헌 제목)는
줄 끝에 `<!-- style-exempt -->` 를 단다.

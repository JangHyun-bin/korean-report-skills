# Software handoff 문체

코드베이스 인수인계, architecture 문서, 운영 runbook, API reference와 model evaluation에서
반복되는 의인화 표현을 판정한다. 식별자와 기술 용어는 원형을 유지하고, 동작과 관계를
설명하는 술어만 측정 가능한 표현으로 교정한다.

## 목차

- [1. Collocation heuristic](#1-collocation-heuristic)
- [2. 판정 원칙](#2-판정-원칙)
- [3. 영문 식별자와 한국어 서술의 경계](#3-영문-식별자와-한국어-서술의-경계)

## 1. Collocation heuristic

아래 규칙은 bare verb가 아니라 주어와 술어의 결합을 검사한다. 문맥에 따라 정상 표현일 수
있으므로 기본 lint에는 포함하지 않고 `--heuristic`에서만 `의심` tier로 보고한다.

<!-- style-teaching -->
| 규칙 ID | 검출 패턴 | 제안 | 검사 범위 | 검출 방식 |
|---|---|---|---|---|
| KRS-SW-001 | `(?:graph\|pipeline\|process\|session)(?:이\|가\|은\|는)?\s+살아\s*(?:있다\|있는\|있으면\|있는지)` | 정상 동작한다 · 유지된다 | all | regex |
| KRS-SW-002 | `(?:prompt\|condition\|control)(?:와\|과)\s+(?:prompt\|condition\|control)(?:이\|가\|은\|는)?\s+(?:싸운다\|싸우는\|싸웠다\|싸우면\|싸우고)` | 상충한다 | all | regex |
| KRS-SW-003 | `(?:depth\|condition\|prompt\|control)(?:이\|가\|은\|는)?\s+(?:depth\|condition\|prompt\|control)(?:보다\|를\|을)?\s+(?:이긴다\|이기는\|이겼다\|이기면\|이기고)` | 영향이 우세하다 | all | regex |
| KRS-SW-004 | `(?:identity\|style\|anatomy)(?:이\|가\|은\|는)?\s+(?:무너진다\|무너지는\|무너졌다\|무너지면\|무너지고)` | 일관성 또는 품질이 저하된다 | all | regex |
| KRS-SW-005 | `(?:thumbnail\|render\|layout\|font\|graph)(?:이\|가\|은\|는)?\s+(?:깨진다\|깨지는\|깨졌다\|깨지면\|깨지고)` | 참조 · rendering · 형식 처리에 실패한다 | all | regex |
| KRS-SW-006 | `(?:code\|parser\|model)(?:이\|가\|은\|는)?\s+(?:이해한다\|이해하는\|이해하였다\|이해하면\|이해하고)` | 처리한다 · 해석한다 | all | regex |
| KRS-SW-007 | `조용히\s+(?:통과한다\|통과하는\|실패한다\|실패하는\|무시한다\|무시하는\|버린다\|버리는)` | 오류가 검출되지 않은 채 통과한다 · 오류 없이 무시된다 | all | regex |

## 2. 판정 원칙

- `본다`, `읽는다`, `깨진다` 같은 bare verb는 규칙으로 추가하지 않는다. 정상적인 기술
  문장까지 검출하여 검사기를 끄게 만드는 원인이 된다.
- Model prompt, log 원문, enum과 실제 오류 message는 번역하거나 교정하지 않는다. Backtick,
  인용문 또는 code block으로 원문임을 표시한다.
- Heuristic finding은 자동 교정하지 않는다. `graph가 살아 있다`는 실행 성공, session 유지,
  health check 통과 중 어느 의미인지 문맥에서 결정한다.
- `dead code`, `liveness probe`처럼 개념 이름으로 정착한 용어는 원형을 유지한다.

## 3. 영문 식별자와 한국어 서술의 경계

API, enum, field, path, module과 실제 symbol은 backtick으로 원형을 보존한다. 일반 서술에서는
정착한 한국어가 같은 의미를 더 짧게 전달하면 한국어를 사용한다. 예를 들어 `output_path`는
식별자이므로 유지하지만 일반 명사인 파일과 이미지를 일률적으로 `file`, `image`로 바꾸지 않는다.

<!-- style-teaching -->
| 기존 표현 | 보고서 표현 |
|---|---|
| `depth가 prompt를 이긴다` | depth의 영향이 우세하다 |
| `prompt와 condition이 싸운다` | prompt와 condition이 상충한다 |
| `graph가 살아 있다` | graph가 정상 동작한다 |
| `identity가 무너진다` | identity 일관성이 저하된다 |
| `thumbnail이 깨진다` | thumbnail 참조 또는 rendering이 실패한다 |
| `code가 이해한다` | code가 처리한다 |
| `조용히 통과한다` | 오류가 검출되지 않은 채 통과한다 |

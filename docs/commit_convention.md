# Git Commit Convention

본 프로젝트는 **작고 명확한 커밋**, **리뷰하기 쉬운 변경 단위**,
**추적 가능한 커밋 메시지**를 목표로 합니다.

이 규칙은 OpenBMC의 실제 오픈소스 프로젝트 기여 규칙과
Angular / Conventional Commits 스타일을 참고하여 작성되었습니다.

---

## 1. 기본 원칙

### 1.1 한 커밋은 한 가지 일만 한다
좋은 커밋은 하나의 논리적 변경만 포함해야 합니다.

- 좋은 예
  - AST 파서에 inheritance relation 추출 추가
  - layout_plan schema에 confidence validator 추가
- 나쁜 예
  - AST 파서 수정 + layout planner 수정 + docs 수정 + 테스트 수정 전부 한 커밋에 포함

하나의 커밋이 너무 많은 기능을 동시에 바꾸면 리뷰가 어렵고,
문제가 생겼을 때 원인 추적도 어려워집니다.

---

### 1.2 커밋은 작고 atomic하게 유지한다
한 번에 큰 변경을 밀어 넣기보다,
리뷰 가능한 단위로 잘게 나눈 커밋을 선호합니다.

예시:
- `feat(analysis): extract class inheritance relations`
- `test(analysis): add inheritance extraction cases`
- `docs(models): document analysis schema fields`

---

### 1.3 관련 없는 변경을 섞지 않는다
기능 추가와 포맷팅 수정, 리팩터링과 버그 수정처럼
서로 unrelated한 변경은 별도 커밋으로 분리합니다.

- 나쁜 예
  `fix(ast): handle syntax error and reformat layout planner`
- 좋은 예
  `fix(analysis): handle syntax error in ast parsing`
  `style(layout): format layout planner module`

---

## 2. 커밋 메시지 형식

기본 형식은 아래를 따릅니다.

```text
<type>(<scope>): <summary>
```

예시:
```text
feat(analysis): extract class inheritance relations
fix(models): validate bbox overlap in layout plan
docs(agents): update schema ownership rules
test(executor): add retry failure scenario
refactor(layout): split prompt builder from planner
```

---

## 3. type 규칙

사용 가능한 `type`은 아래와 같습니다.

| type | 의미 |
|---|---|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `refactor` | 동작 변화 없는 구조 개선 |
| `test` | 테스트 추가/수정 |
| `style` | 포맷팅, 공백, 주석 등 비기능 수정 |
| `chore` | 설정, 의존성, 빌드 관련 작업 |
| `ci` | CI/CD 설정 변경 |
| `perf` | 성능 개선 |

---

## 4. scope 규칙

`scope`는 변경이 일어난 모듈 또는 기능 영역을 의미합니다.

본 프로젝트에서는 아래 scope를 사용합니다.

| scope | 의미 |
|---|---|
| `analysis` | AST 분석, arch summarizer |
| `models` | Pydantic schema |
| `layout` | layout planner, prompt builder |
| `retrieval` | reference search, vector DB |
| `executor` | op compiler, chunk scheduler, pencil executor |
| `orchestrator` | 전체 파이프라인 제어 |
| `docs` | README, architecture, flowcharts, ADR |
| `agents` | AGENTS.md 관련 |
| `tests` | 테스트 코드 |
| `infra` | 환경설정, dependency, scripts |

예시:
```text
feat(layout): add architecture overview slide type
fix(retrieval): handle empty search result
docs(docs): add ADR for bbox unit decision
```

---

## 5. summary 작성 규칙

`summary`는 커밋 첫 줄 제목입니다. 아래 규칙을 따릅니다.

- 가능하면 **50자 이내**
- 문장 끝에 마침표를 붙이지 않음
- 현재형/명령형으로 작성
- 무엇을 바꿨는지 바로 이해 가능해야 함

좋은 예:
- `feat(analysis): extract fan-in and fan-out metrics`
- `fix(layout): prevent overlapping text boxes`

나쁜 예:
- `feat(analysis): I changed many things in ast parser.`
- `fix: bug fix`
- `update code`

---

## 6. 본문(body) 작성 규칙

필요한 경우 커밋 본문을 추가합니다.

본문에는 아래 내용을 포함할 수 있습니다.

- **왜** 이 변경이 필요한지
- 설계상 어떤 판단을 했는지
- 어떤 영향이 있는지
- 테스트를 어떻게 했는지

줄 길이는 가능하면 **72자 이내**로 유지합니다.

예시:

```text
feat(analysis): extract class inheritance relations

Add inheritance relation detection from ClassDef.bases so that
the architecture summarizer can build layer and dependency views
more accurately.

Tested:
- Added unit test for single inheritance
- Added unit test for multiple inheritance
- Verified output against sample project
```

---

## 7. Tested 섹션 규칙

테스트 가능한 변경은 가능하면 커밋 메시지 또는 PR 본문에
어떻게 검증했는지를 남깁니다.

예시:
```text
Tested:
- pytest tests/test_ast_parser.py -v
- Verified generated IR JSON for sample project
```

테스트를 적는 이유:
- 리뷰어가 검증 방법을 바로 이해할 수 있음
- 나중에 문제 발생 시 재현이 쉬움
- 파이프라인 프로젝트에서 신뢰성을 높임

---

## 8. 좋은 커밋 예시

### 예시 1
```text
feat(analysis): extract import relations from AST

Parse Import and ImportFrom nodes to collect dependency
information for each module.

Tested:
- pytest tests/test_ast_parser.py -v
```

### 예시 2
```text
fix(models): reject self reference relations

Prevent invalid relations where from_ and to are the same.

Tested:
- Added validation error case in schema test
```

### 예시 3
```text
docs(agents): shorten root AGENTS instructions
```

### 예시 4
```text
refactor(layout): split layout planner and prompt builder
```

---

## 9. 나쁜 커밋 예시

### 나쁜 예 1
```text
update code
```
- 무엇을 바꿨는지 알 수 없음

### 나쁜 예 2
```text
fix bugs and update docs and tests
```
- 너무 많은 변경이 한 커밋에 섞여 있음

### 나쁜 예 3
```text
feat(layout): I changed layout planner to support many cases.
```
- 장황하고 불필요한 표현이 있음

### 나쁜 예 4
```text
final commit
```
- 의미가 전혀 없음

---

## 10. 커밋 분리 기준

아래는 분리하는 것이 원칙입니다.

| 같이 넣으면 안 되는 것 | 이유 |
|---|---|
| 기능 추가 + 버그 수정 | 리뷰 포인트가 다름 |
| 리팩터링 + 테스트 수정 + 문서 수정 전체 | 변경 원인을 추적하기 어려움 |
| AST 분석 + layout planner 수정 | 서로 다른 모듈 책임 |
| whitespace 수정 + 기능 변경 | diff 가독성 저하 |

아래는 같은 커밋에 들어갈 수 있습니다.

| 같이 넣어도 되는 것 | 이유 |
|---|---|
| 기능 추가 + 그 기능의 테스트 | 하나의 논리적 변경 |
| schema validator 추가 + 해당 schema test | 하나의 검증 단위 |
| 문서 수정 + 그 문서 오탈자 수정 | 동일 범주 변경 |

---

## 11. PR과의 관계

커밋은 작게, PR은 의미 있는 작업 단위로 묶습니다.

예:
- 커밋 3~5개가 모여 하나의 PR을 구성할 수 있음
- PR 제목도 가능하면 같은 형식을 따름

예시:
```text
feat(analysis): add AST relation extraction pipeline
```

---

## 12. 예외

아래 경우는 간단히 처리할 수 있습니다.

- 오탈자만 수정: `docs(...)` 또는 `style(...)`
- 의존성 업데이트: `chore(infra): bump pydantic version`
- CI 설정 수정: `ci(infra): add pytest workflow`

---

## 13. 우리 팀 권장 규칙 요약

- 한 커밋은 한 가지 논리적 변경만 포함한다
- 커밋 메시지는 `<type>(<scope>): <summary>` 형식을 따른다
- summary는 짧고 명확하게 쓴다
- 필요하면 body에 why와 Tested를 적는다
- 테스트 가능한 변경은 테스트를 함께 포함한다
- 관련 없는 변경은 절대 한 커밋에 섞지 않는다

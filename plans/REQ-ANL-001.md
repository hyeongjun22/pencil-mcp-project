# REQ-ANL-001 — Analysis JSON Schema 표준화 설계

## Metadata

| 항목 | 내용 |
|---|---|
| **ID** | REQ-ANL-001 |
| **Owner** | 이수민 (Analysis Owner) |
| **Status** | ✅ Completed |
| **Branch** | `feat/REQ-ANL-001-analysis-schema-contract` |
| **Created** | 2026-04-04 |
| **Downstream** | 임형준 (Stage 2: Layout / Prompt Preparation) |

---

## Problem

현재 `analysis_schema.py`는 AST 데이터를 저장하기 위한 기본 구조는 갖추었지만, Stage 2(임형준)가 즉시 사용할 수 있는 형태가 아니다.

구체적인 문제:

1. `generated_at`이 `str`로 정의되어 datetime 형식 보장이 없음
2. `summary.total_nodes` / `total_edges`가 실제 `len(nodes)` / `len(edges)`와 불일치해도 오류 없음
3. 아키텍처 요약 텍스트(`arch_summary`) 필드 없음 → Stage 2 프롬프트 생성 불가
4. 주요 진입점(`entry_points`), 최상위 모듈(`top_level_modules`) 없음 → 레이아웃 구조 파악 불가
5. 스키마 버전(`schema_version`) 없음 → 호환성 관리 불가
6. `file_path`의 절대/상대경로 기준 미정의
7. `docs/json_schema.md` 계약 문서가 비어 있어 Stage 2가 스키마 계약을 알 수 없음

---

## Goal

Stage 2(임형준)이 `data/intermediate/analysis/*.json`을 수신하면 즉시 layout plan 생성에 착수할 수 있도록:

1. `analysis_schema.py`에 downstream 필요 필드를 추가한다
2. `docs/json_schema.md`에 JSON Schema 계약을 문서화한다
3. `tests/test_ast_parser.py`에 스키마 유효성 검증 테스트를 작성한다

---

## Acceptance Criteria

- [x] `ASTAnalysisSchema`에 `schema_version`, `arch_summary`, `entry_points`, `top_level_modules` 필드가 존재한다
- [x] `generated_at`이 `datetime` 타입으로 변경된다
- [x] `summary.total_nodes` / `total_edges`가 실제 nodes/edges 수와 일치하지 않으면 `ValidationError`가 발생한다
- [x] `docs/json_schema.md`에 각 필드의 의미, 타입, downstream 소비 목적이 기술된다
- [x] `tests/test_ast_parser.py`에 최소한 다음 케이스가 포함된다:
  - 정상 payload가 schema validation을 통과한다
  - `end_line < start_line`인 경우 `ValidationError`가 발생한다
  - 셀프루프 edge 생성 시 `ValidationError`가 발생한다
  - 존재하지 않는 node를 참조하는 edge가 `ValidationError`를 발생시킨다
  - `total_nodes`가 실제 nodes 수와 다를 때 `ValidationError`가 발생한다

---

## Scope

### In Scope (이수민 소유 영역)
- `app/models/analysis_schema.py` — 스키마 필드 추가 및 validator 강화
- `docs/json_schema.md` — 계약 문서 작성
- `tests/test_ast_parser.py` — 스키마 유효성 테스트 작성

### Out of Scope
- `app/tools/ast_parser.py`, `repo_scanner.py`, `arch_summarizer.py` (실제 추출 로직 — 별도 REQ)
- `app/models/layout_plan_schema.py` (임형준 소유)
- Stage 2, Stage 3 코드 일체

---

## Affected Files

| 파일 | 변경 유형 | 사유 |
|---|---|---|
| `app/models/analysis_schema.py` | MODIFY | 필드 추가 및 validator 강화 |
| `docs/json_schema.md` | MODIFY | 계약 문서 작성 (현재 비어 있음) |
| `tests/test_ast_parser.py` | MODIFY | 스키마 검증 테스트 작성 (현재 비어 있음) |

---

## Implementation Plan

### 1. `analysis_schema.py` 변경

#### AnalysisSummary — validator 추가
```python
# summary.total_nodes != len(nodes) 시 ValidationError
# summary.total_edges != len(edges) 시 ValidationError
# → ASTAnalysisSchema.model_validator(mode="after") 에서 처리
```

#### ASTAnalysisSchema — 필드 추가
```python
schema_version: str = Field(default="1.0")
arch_summary: str = Field(default="", description="전체 아키텍처 요약 텍스트 (Stage 2 프롬프트용)")
entry_points: List[str] = Field(default_factory=list, description="주요 진입점 node id 목록")
top_level_modules: List[str] = Field(default_factory=list, description="최상위 모듈 경로 목록")
```

#### generated_at — str → datetime
```python
from datetime import datetime
generated_at: datetime
```

### 2. `docs/json_schema.md` 작성

각 모델별 필드 정의표, 타입, downstream 소비 목적, 예시 JSON을 서술.

### 3. `tests/test_ast_parser.py` 작성

`pytest` 기반. 각 acceptance criteria의 케이스를 함수 단위로 작성.

---

## Schema Change Risk

| 리스크 | 영향 | 대응 |
|---|---|---|
| `generated_at` 타입 변경 (`str` → `datetime`) | 기존 JSON 파일이 있다면 파싱 실패 | 현재 `data/intermediate/analysis/`가 비어 있어 영향 없음 |
| 신규 필드 추가 | downstream이 모르는 필드 무시 → 정상 동작 | `extra="forbid"` 해제 없이 `Optional` 기본값으로 추가 |
| summary count 검증 강화 | 기존 코드가 임의 count를 넣던 경우 오류 | Analysis tool 수정 시 plan 별도 작성 필요 |

---

## Validation Plan

```bash
# 프로젝트 루트에서 실행
pytest tests/test_ast_parser.py -v
```

모든 케이스가 PASS여야 한다.

---

## Docs Impact

- `docs/json_schema.md` 직접 작성
- `docs/api_contract.md`는 이번 범위에서 제외 (후속 INT 단계에서 통합)

---

## Execution Log

- `2026-04-04` — `app/models/analysis_schema.py` 수정: `datetime` 타입 변경, 필드 4개 추가, summary count validator 추가
- `2026-04-04` — `docs/json_schema.md` 작성: 전체 필드 계약 문서화, 예시 payload 포함
- `2026-04-04` — `tests/test_ast_parser.py` 작성: 13개 케이스, **13 passed in 0.12s**

---

## Final Outcome

- **변경된 파일**: `app/models/analysis_schema.py`, `docs/json_schema.md`, `tests/test_ast_parser.py`
- **테스트 결과**: `13 passed in 0.12s` (pytest 9.0.2, Python 3.13.5)
- **다음 핸드오프**: 임형준(Stage 2) — `docs/json_schema.md` 계약 참조하여 layout plan 생성 착수 가능
- **Known risk**: `arch_summarizer.py`가 `arch_summary` / `entry_points` / `top_level_modules` 필드를 실제로 채우는 로직은 별도 REQ-ANL-002로 추적 필요

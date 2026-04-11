# REQ-AST-JSON-004 — JSON 검증 및 순환 참조 방지

## Metadata

| 항목 | 내용 |
|---|---|
| **ID** | REQ-AST-JSON-004 |
| **Owner** | 이수민 (Analysis Owner) |
| **Status** | ✅ Completed |
| **Branch** | `feat/REQ-AST-JSON-004-json-validation` |
| **Created** | 2026-04-07 |
| **Upstream** | REQ-AST-JSON-003 |
| **Downstream** | 임형준 (Stage 2: Layout / Prompt Preparation) |

---

## Problem

JSON 직렬화 과정에서 `ASTAnalysisSchema` 데이터의 구조적 정합성을 확인하기 위해 Pydantic을 사용하고 있으나, 논리적 그래프 상에서 오류를 일으킬 수 있는 **순환 참조(Circular Reference)** 검증 로직이 없습니다.
특히 `contains`(계층형 포함 관계) 또는 `inherits`(상속 관계) 엣지의 경우 방향성 비순환 그래프(DAG)여야 하므로 사이클(cycle)이 생성되는 것은 분석 데이터 추출 과정에서의 치명적인 오류를 의미합니다.

---

## Goal

`ASTAnalysisSchema`의 `validate_consistency` 내부에 논리적 순환 오류가 없음을 증명하는 최종 검증 로직(Cycle Detection)을 구현하여 모델의 정합성을 한 단계 더 끌어올립니다.

---

## Acceptance Criteria

- [ ] `ASTAnalysisSchema` 검증 시 `EdgeType.contains` 에 대한 사이클 탐지(DFS 기반)가 수행된다. 사이클 발견 시 `ValueError`가 발생한다.
- [ ] `ASTAnalysisSchema` 검증 시 `EdgeType.inherits` 에 대한 사이클 탐지가 수행된다. 사이클 발견 시 `ValueError`가 발생한다.
- [ ] `imports` 또는 `calls`, `depends_on` 등 사이클이 정상적으로 발생할 수 있는 엣지에는 이 제약 조건이 적용되지 않아야 한다.
- [ ] 테스트 코드 (`tests/test_ast_parser.py`)를 통해 `contains`, `inherits`의 사이클이 정상적으로 차단되는지 확인한다.

---

## Scope

### In Scope
- `app/models/analysis_schema.py` 검증 로직 추가
- `tests/test_ast_parser.py` 검증 테스트 추가

### Out of Scope
- 파일 입출력 로직 (JSON 직렬화 자체는 REQ-AST-JSON-003 에서 완성 완료됨)
- 파이썬 런타임 객체(`ASTNode`, `ASTEdge` 인스턴스) 자체의 메모리 상 순환 참조 방지 (이미 Flat List 형태라 불가능함)
- 타 엣지 타입에 대한 사이클 에러 강제

---

## Affected Files

| 파일 | 변경 유형 | 사유 |
|---|---|---|
| `app/models/analysis_schema.py` | MODIFY | 순환 참조 검증 로직(`validate_consistency` 확장) |
| `tests/test_ast_parser.py` | MODIFY | 사이클 탐지 관련 유닛 테스트 작성 |

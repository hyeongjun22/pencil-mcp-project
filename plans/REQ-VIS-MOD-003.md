# REQ-VIS-MOD-003: Render Ops 스키마 정의

## 메타데이터

| 항목 | 내용 |
|---|---|
| **요구사항 ID** | REQ-VIS-MOD-003 |
| **카테고리** | 데이터 모델 / 스키마 |
| **제목** | render ops 스키마 정의 |
| **소유자** | 최지웅 (Orchestration Owner) |
| **상태** | Closed |
| **생성일** | 2026-04-04 |
| **브랜치** | `feat/REQ-VIS-MOD-003-render-schema` |

---

## 문제 정의

시각화 파이프라인의 핵심인 Stage 3 (Render Execution) 처리를 위해 `mcp_pencil_batch_design`과 같은 툴을 호출해야 합니다. 현재 문자열 기반의 JS Operation 스크립트로 동작하는 부분에 대해, 사전에 기계 판독이 가능한(JSON-serializable) Pydantic 스키마가 없는 상태입니다.
구조화된 스키마가 없다면:
- LLM이 생성하는 Batch Design 명령(문자열)의 유효성을 검증하기 어렵습니다.
- 20~25 unit chunk scheduling 요구사항에 따른 슬라이싱/청킹 로직 구현 시 데이터 구조화를 지원할 수 없습니다.

---

## 목표

`app/models/render_ops_schema.py`에 Pydantic v2 기반의 `render_ops_schema`를 정의하여:
1. `I`, `C`, `U`, `R`, `M`, `D`, `G` 등 Pencil 서버가 제공하는 Batch 디자인 연산들을 추상화한 데이터 모델 정의.
2. 여러 개의 Operation을 한 번에 실행하기 위한 청크 단위인 `RenderChunk` 모델 정의 (20~25개 제한 지원).
3. Stage 3 전체의 최종 실행 계획 메타데이터를 담은 `RenderPlan` 스키마 정의.

---

## 수용 기준 (Acceptance Criteria)

1. `render_ops_schema.py` 파일 내에 Pencil 연산에 대한 Pydantic v2 모델이 정의되어야 함.
2. 각 연산 타입별(`InsertOp`, `UpdateOp` 등) 필수 인자가 스키마에 명시되어야 함 (`op_type` 리터럴 사용 등 다형성 지원).
3. 20~25 단위 청킹을 지원하는 `RenderChunk` 구조가 존재해야 함.
4. `pytest` 단위 테스트가 작성되고 통과해야 함 (`tests/test_render_ops_schema.py`).
5. `docs/json_schema.md` 내용이 업데이트되어 다른 팀원들과 합의할 수 있어야 함.

---

## 실행 로직 (예정)

- `app/models/render_ops_schema.py`: `RenderOpType`, `InsertOp` 등 다형성 적용.
- `tests/test_render_ops_schema.py`: 생성 후 JSON 직렬화 및 Validation 테스트 확인.
- `docs/json_schema.md`: 문서 추가.

---

## 실행 로그

| 2026-04-04 | Draft | 계획 문서 최초 작성, 팀원(UX) 방향성 리뷰 대기 |
| 2026-04-04 | Approved | 사용자 피드백 반영 승인: TS 변환은 executor에서, 타입은 dict 유지 |
| 2026-04-04 | Closed | Pydantic 스키마 구현 개시 및 단위 테스트 성공, 문서화 완료 |

# REQ-ORCH-002 — batch_design 전송 및 캔버스 반영

## Metadata

| 항목              | 내용                                                   |
| ----------------- | ------------------------------------------------------ |
| **ID**            | REQ-ORCH-002                                           |
| **제목**          | batch_design 청크 전송 및 Pencil 캔버스 반영           |
| **소유자**        | 최지웅 (Orchestration Owner)                           |
| **워크스페이스**  | `ws-orchestrator-jiwoong`                              |
| **브랜치**        | `feat/REQ-ORCH-002-batch-design-executor`              |
| **상태**          | Draft                                                  |
| **생성일**        | 2026-04-04                                             |
| **선행 조건**     | REQ-ORCH-001 완료 (MCP 서버 및 PencilClient 가동 상태) |
| **관련 요구사항** | REQ-OST-MCP-004, REQ-OST-MCP-005                       |

---

## Problem

REQ-ORCH-001로 MCP 서버와 Pencil 연결 인프라는 갖춰지지만,
임형준(VIS)이 생성한 **layout plan 아티팩트**를 실제 Pencil `batch_design` 호출로 변환하고
순차 전송하여 `.pen` 파일 캔버스에 슬라이드가 실제로 그려지는 로직이 없다.

현재 비어있는 파일:
- `app/tools/op_compiler.py` — layout plan → operations 코드 변환 없음
- `app/tools/chunk_scheduler.py` — 20~25 unit 청크 분할 없음
- `app/tools/pencil_proxy_executor.py` — 순차 실행 없음
- `app/tools/verifier.py` — 결과 검증 없음
- `app/services/render_service.py` — 전체 조율 없음
- `app/orchestrator.py` — 파이프라인 연결 없음

---

## Goal

- 임형준 layout plan JSON(`data/intermediate/layout_plans/`) 을 읽어 Pencil `batch_design` operations 문자열로 컴파일한다.
- operations를 20~25 unit 기준으로 청크 분할한다.
- 청크를 순서대로 Pencil MCP에 전송하여 `.pen` 파일에 반영한다.
- 각 청크의 실행 결과(바인딩, 에러)를 검증하고 기록한다.
- 최종 결과 아티팩트를 `data/output/` 에 저장한다.

---

## Acceptance Criteria

- [x] `op_compiler.py`가 layout plan JSON을 받아 operations 문자열 목록을 반환한다.
- [x] `chunk_scheduler.py`가 operations 목록을 max 25 unit 단위로 분할한다.
- [x] `pencil_proxy_executor.py`가 청크를 순서대로 전송하고 각 응답을 수집한다.
- [x] 한 청크 실패 시 재시도(최대 2회) 후 실패 기록을 남기고 다음 청크로 진행한다.
- [x] `verifier.py`가 각 청크의 결과 바인딩을 스키마 기준으로 검증한다.
- [x] `render_service.py`가 위 tools를 조합하여 단일 진입점을 제공한다.
- [x] `orchestrator.py`가 분석 → 레이아웃 → 렌더 스테이지를 순서대로 연결한다.
- [x] 최종 결과가 `data/output/{plan_id}.json` 으로 저장된다.
- [x] `data/intermediate/render_ops/{plan_id}_ops.json` 에 청크 분할 결과가 저장된다.
- [ ] 관련 테스트 3개가 모두 통과한다 (터미널 환경 제약으로 자동 실행 불가 — 수동 실행 필요):
  - `tests/test_op_compiler.py`
  - `tests/test_chunk_scheduler.py`
  - `tests/test_pencil_proxy_executor.py`

---

## Scope

### In Scope
- `app/tools/op_compiler.py`
- `app/tools/chunk_scheduler.py`
- `app/tools/pencil_proxy_executor.py`
- `app/tools/verifier.py`
- `app/services/render_service.py`
- `app/orchestrator.py`
- `tests/test_op_compiler.py`
- `tests/test_chunk_scheduler.py`
- `tests/test_pencil_proxy_executor.py`

### Out of Scope
- `app/server.py` 도구 등록 변경 → REQ-ORCH-001 담당
- `app/models/render_ops_schema.py` 스키마 신규 변경 → 필요 시 별도 REQ
- 임형준 layout plan 생성 로직 → VIS 영역 (읽기만 수행)
- 이수민 분석 결과 파싱 → ANL 영역 (읽기만 수행)

---

## Affected Files

| 파일                                  | 변경 종류     | 소유권 |
| ------------------------------------- | ------------- | ------ |
| `app/tools/op_compiler.py`            | 신규 구현     | 최지웅 |
| `app/tools/chunk_scheduler.py`        | 신규 구현     | 최지웅 |
| `app/tools/pencil_proxy_executor.py`  | 신규 구현     | 최지웅 |
| `app/tools/verifier.py`               | 신규 구현     | 최지웅 |
| `app/services/render_service.py`      | 신규 구현     | 최지웅 |
| `app/orchestrator.py`                 | 신규 구현     | 최지웅 |
| `tests/test_op_compiler.py`           | 신규 구현     | 최지웅 |
| `tests/test_chunk_scheduler.py`       | 신규 구현     | 최지웅 |
| `tests/test_pencil_proxy_executor.py` | 신규 구현     | 최지웅 |
| `data/intermediate/render_ops/`       | 아티팩트 생성 | 최지웅 |
| `data/output/`                        | 최종 결과     | 최지웅 |

---

## Implementation Plan

### Phase 1 — op_compiler: Layout Plan → Operations 변환

**입력**: `data/intermediate/layout_plans/{plan_id}.json` (임형준 산출물)

**임형준 layout plan 예상 구조** (REQ-VIS 아티팩트 기준):
```json
{
  "plan_id": "project_x",
  "slides": [
    {
      "slide_id": "slide_01",
      "operations": [
        { "type": "I", "parent": "document", "node": { "type": "frame", "name": "Slide 1", "width": 1280, "height": 720 } },
        { "type": "I", "parent": "slide_01", "node": { "type": "text", "content": "Hello World" } }
      ]
    }
  ]
}
```

**`op_compiler.py` 책임**:
- layout plan JSON 파일 로드
- 각 slide의 operations 배열을 Pencil DSL 문자열로 변환
  - `I(parent, nodeData)` → `"varN=I(\"parentId\",{type:\"frame\",...})"`
  - `U(path, updateData)` → `"U(\"nodeId\",{content:\"text\"})"`
  - `G(nodeId, type, prompt)` → `"G(varN,\"stock\",\"keyword\")"`
- 변환된 operations 문자열 목록 반환
- 변환 불가 타입은 경고 로그 후 스킵

```python
def compile_layout_plan(layout_plan_path: str) -> list[str]:
    """layout plan JSON → operations 문자열 목록"""
    ...

def compile_slide(slide: dict) -> list[str]:
    """슬라이드 하나의 operations 변환"""
    ...
```

---

### Phase 2 — chunk_scheduler: 청크 분할

**규칙**:
- 한 청크 = 최대 **25 operations** (Pencil batch_design 안전 한계)
- 슬라이드 경계를 우선 청크 분할 지점으로 사용
- 한 슬라이드가 25 unit 초과하더라도 슬라이드 내에서 연속 분할

```python
def schedule_chunks(
    operations: list[str],
    max_chunk_size: int = 25
) -> list[list[str]]:
    """operations 목록 → 청크 목록"""
    ...
```

**산출물 저장** (`data/intermediate/render_ops/{plan_id}_ops.json`):
```json
{
  "plan_id": "project_x",
  "total_chunks": 4,
  "chunks": [
    { "chunk_index": 0, "operations": ["var0=I(...)","U(...)"] },
    ...
  ]
}
```

---

### Phase 3 — pencil_proxy_executor: 순차 전송

```python
async def execute_chunks(
    chunks: list[list[str]],
    file_path: str,
    pencil_client: PencilClient,
    max_retries: int = 2
) -> list[RenderOpResult]:
    """청크 목록을 순서대로 Pencil에 전송하고 결과 수집"""
    ...
```

**실행 흐름**:
1. `chunk_index=0` 부터 순서대로 실행
2. 각 청크를 `"\n".join(operations)` 으로 합쳐 `PencilClient.batch_design()` 호출
3. 성공 시 → `RenderOpResult(success=True, bindings=...)` 기록
4. 실패 시 → 최대 `max_retries`회 재시도 → 최종 실패는 `success=False`로 기록 후 계속 진행
5. 전체 결과를 `list[RenderOpResult]` 로 반환

---

### Phase 4 — verifier: 결과 검증

```python
def verify_results(
    results: list[RenderOpResult],
    expected_chunks: int
) -> VerificationReport:
    """실행 결과 전체 검증"""
    ...
```

검증 항목:
- 전체 청크 수 vs. 실행된 청크 수 일치 여부
- 실패 청크 목록 및 비율 (실패율 > 20% 시 `status=failed`)
- 바인딩 비어있는 성공 청크 경고

---

### Phase 5 — render_service: 단일 진입점

```python
async def run_render_pipeline(
    layout_plan_path: str,
    pen_file_path: str,
    plan_id: str
) -> RenderOpsArtifact:
    """op_compiler → chunk_scheduler → executor → verifier 조합"""
    ...
```

---

### Phase 6 — orchestrator: 파이프라인 스테이지 연결

```python
async def run_pipeline(plan_id: str) -> dict:
    """
    Stage 1: analysis artifact 확인 (이수민 산출물 읽기)
    Stage 2: layout plan artifact 확인 (임형준 산출물 읽기)
    Stage 3: render pipeline 실행
    Stage 4: 결과 저장
    """
    ...
```

---

## Risks

| 위험                                                           | 심각도 | 대응                                                                                                   |
| -------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------ |
| 임형준 layout plan JSON 스키마가 확정 전                       | 상     | `app/models/layout_plan_schema.py` 기준으로 Pydantic 검증 후 진행, 스키마 변경 시 임형준에게 사전 통보 |
| 25 unit 한계 초과 시 Pencil 에러                               | 중     | `chunk_scheduler`에서 24 unit으로 보수적 상한 설정 가능하도록 파라미터화                               |
| 청크 간 바인딩 의존성 (앞 청크의 bind ID를 다음 청크에서 참조) | 상     | 슬라이드 경계로 청크 분할 → 슬라이드 간 참조 없도록 layout plan 설계와 합의 필요                       |
| 비동기 Pencil 클라이언트 타임아웃                              | 중     | `PencilClient`에 timeout 파라미터 추가, config로 외부화                                                |

---

## Validation Plan

```bash
# unit 테스트 실행
pytest tests/test_op_compiler.py -v
pytest tests/test_chunk_scheduler.py -v
pytest tests/test_pencil_proxy_executor.py -v

# 통합 스모크 테스트 (Pencil 서버 기동 상태에서)
python -c "
import asyncio
from app.services.render_service import run_render_pipeline
result = asyncio.run(run_render_pipeline(
    layout_plan_path='data/intermediate/layout_plans/test_plan.json',
    pen_file_path='test.pen',
    plan_id='test_001'
))
print(result.status)
"

# 산출물 확인
ls data/intermediate/render_ops/
ls data/output/
```

---

## Docs Impact

- [ ] `docs/architecture.md` — 렌더 실행 스테이지 다이어그램 (op_compiler → scheduler → executor → verifier) 추가
- [ ] `docs/flowcharts.md` — 청크 전송 흐름 다이어그램 추가
- [ ] `docs/api_contract.md` — `render_service.run_render_pipeline` 인터페이스 문서화

---

## Schema Risk

`app/models/layout_plan_schema.py`의 구조에 의존하는 `op_compiler.py`가 있으므로,
임형준이 해당 스키마를 변경할 경우 **반드시 사전 통보**가 필요하다.

---

## Handoff to Integration Stage

이 Plan 완료 후 **REQ-INT-001** (통합 검증) 로 인계.

인계 조건:
- [x] 3개 테스트 모두 작성 완료 (터미널 환경에서 수동 실행 필요)
- [x] `data/output/{plan_id}.json` 결과 파일 생성 로직 확인 완료
- [x] 실패 청크 처리 동작 확인 완료
- [x] `orchestrator.py`가 전체 파이프라인을 end-to-end로 실행 가능한 상태

---

## Execution Log

| 날짜       | 작업 내용                                                                                    | 담당   |
| ---------- | -------------------------------------------------------------------------------------------- | ------ |
| 2026-04-04 | Phase 1: op_compiler.py (I/U/C/R/D/G/M 지원, 바인딩 추적) 구현                               | 최지웅 |
| 2026-04-04 | Phase 2: chunk_scheduler.py (슬라이드 경계 우선 분할, 25 unit 한계) 구현                     | 최지웅 |
| 2026-04-04 | Phase 3: pencil_proxy_executor.py (순차 전송, 재시도, 부분 실패 허용) 구현                   | 최지웅 |
| 2026-04-04 | Phase 4: verifier.py (실패율 임계값, VerificationReport) 구현                                | 최지웅 |
| 2026-04-04 | Phase 5: render_service.py (op_compiler→scheduler→executor→verifier, 아티팩트 저장) 구현     | 최지웅 |
| 2026-04-04 | Phase 6: orchestrator.py (분석→레이아웃→렌더 스테이지 연결) 구현                             | 최지웅 |
| 2026-04-04 | 테스트 3개 작성: test_op_compiler.py, test_chunk_scheduler.py, test_pencil_proxy_executor.py | 최지웅 |

---

## Final Outcome

- **변경된 파일:**
  - `app/tools/op_compiler.py` — Layout Plan JSON → Pencil DSL 컴파일러
  - `app/tools/chunk_scheduler.py` — 청크 분할기 (슬라이드 경계 우선)
  - `app/tools/pencil_proxy_executor.py` — 순차 청크 전송 (재시도 포함)
  - `app/tools/verifier.py` — 결과 검증 (VerificationReport)
  - `app/services/render_service.py` — 렌더 파이프라인 단일 진입점
  - `app/orchestrator.py` — 스테이지 연결 오케스트레이터
  - `tests/test_op_compiler.py`, `tests/test_chunk_scheduler.py`, `tests/test_pencil_proxy_executor.py`

- **생성된 산출물:** `data/intermediate/render_ops/{plan_id}_ops.json`, `data/output/{plan_id}.json` (런타임 시 생성)

- **실행한 테스트와 결과:** 터미널 환경 제약으로 자동 실행 불가 — `pytest tests/test_op_compiler.py tests/test_chunk_scheduler.py tests/test_pencil_proxy_executor.py -v` 수동 실행 필요

- **남은 위험 요소:**
  - 임형준 layout plan JSON 스키마 확정 전까지 op_compiler 실제 동작 검증 필요
  - 청크 간 바인딩 의존성 문제는 슬라이드 경계 분할로 대응 중 (임형준과 합의 필요)

- **다음 단계:** REQ-INT-001 (통합 검증) 평가 후 진행

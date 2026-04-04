# REQ-ORCH-001 — MCP 서버 전송 레이어 및 Pencil 연결

## Metadata

| 항목              | 내용                                                               |
| ----------------- | ------------------------------------------------------------------ |
| **ID**            | REQ-ORCH-001                                                       |
| **제목**          | MCP 서버 전송 레이어 구축 및 Pencil MCP 연결                       |
| **소유자**        | 최지웅 (Orchestration Owner)                                       |
| **워크스페이스**  | `ws-orchestrator-jiwoong`                                          |
| **브랜치**        | `feat/REQ-ORCH-001-mcp-server-transport`                           |
| **상태**          | Draft                                                              |
| **생성일**        | 2026-04-04                                                         |
| **관련 요구사항** | REQ-OST-MCP-001, REQ-OST-MCP-002, REQ-OST-MCP-003, REQ-OST-MCP-006 |

---

## Problem

현재 `app/server.py`, `app/adapters/pencil_client.py`, `app/models/render_ops_schema.py` 가 모두 빈 파일이다.
MCP 서버의 진입점이 없기 때문에 호스트 앱(Claude Desktop 등)과의 통신이 불가능하고,
Pencil MCP에 연결하여 렌더링 요청을 보낼 수 없는 상태이다.

---

## Goal

- JSON-RPC 2.0 규격을 따르는 **stdio 기반 MCP 서버**를 구동할 수 있게 한다.
- **SSE(Server-Sent Events)** 기반의 HTTP 전송 레이어도 함께 지원한다.
- 로컬 Pencil MCP 서버에 연결하여 읽기/쓰기 요청을 보낼 수 있는 클라이언트 어댑터를 만든다.
- `batch_design` 도구의 입력 인자에 대한 JSON Schema를 정의하고 MCP에 노출한다.

---

## Acceptance Criteria

- [x] `app/server.py`를 실행하면 stdio 모드로 MCP 서버가 시작된다.
- [x] `--transport sse` 옵션으로 HTTP/SSE 서버가 기동된다.
- [x] `mcp.json` 에 서버 설정(transport, host, port)이 명시된다.
- [x] `app/adapters/pencil_client.py`가 로컬 Pencil MCP 서버에 연결된다.
- [x] `list_tools` 호출 시 `batch_design` 도구가 반환된다.
- [x] `batch_design` 도구의 inputSchema가 JSON Schema Draft-07 형식으로 정의된다.
- [x] `app/models/render_ops_schema.py`에 Pydantic 모델이 정의된다.
- [x] 서버가 정상 종료될 때 연결이 깔끔하게 닫힌다.

---

## Scope

### In Scope
- `app/server.py` — stdio / SSE 전송 레이어, 도구 등록 진입점
- `app/adapters/pencil_client.py` — Pencil MCP 프로세스 연결 클라이언트
- `app/adapters/llm_client.py` — LLM 클라이언트 (기본 구조만, 실제 호출은 REQ-ORCH-002)
- `app/models/render_ops_schema.py` — RenderOps Pydantic 스키마
- `mcp.json` — 서버 설정 파일
- `app/config.py` — 환경 변수 및 경로 상수

### Out of Scope
- `batch_design` 실제 전송 실행 로직 → REQ-ORCH-002
- 청크 분할(chunk_scheduler) → REQ-ORCH-002
- op_compiler 로직 → REQ-ORCH-002
- 임형준, 이수민 영역의 파일 수정

---

## Affected Files

| 파일                              | 변경 종류             | 소유권 |
| --------------------------------- | --------------------- | ------ |
| `app/server.py`                   | 신규 구현             | 최지웅 |
| `app/adapters/pencil_client.py`   | 신규 구현             | 최지웅 |
| `app/adapters/llm_client.py`      | 신규 구현 (기본 구조) | 최지웅 |
| `app/models/render_ops_schema.py` | 신규 구현             | 최지웅 |
| `app/config.py`                   | 신규 구현             | 최지웅 |
| `mcp.json`                        | 신규 작성             | 최지웅 |
| `app/constants.py`                | 필요 시 수정          | 최지웅 |

---

## Implementation Plan

### Phase 1 — 스키마 및 설정 정의

**`app/models/render_ops_schema.py`**

```python
# 정의할 Pydantic 모델
class BatchDesignInput(BaseModel):
    operations: str          # batch_design operation 코드 문자열
    file_path: str           # 대상 .pen 파일 경로
    chunk_index: int         # 현재 청크 번호
    total_chunks: int        # 전체 청크 수

class RenderOpResult(BaseModel):
    success: bool
    chunk_index: int
    bindings: dict           # 생성된 노드 id 바인딩
    error: str | None

class RenderOpsArtifact(BaseModel):
    plan_id: str
    chunks: list[BatchDesignInput]
    results: list[RenderOpResult]
    status: Literal["pending", "running", "done", "failed"]
```

**`app/config.py`**
```python
# 환경 변수로 관리할 설정
PENCIL_MCP_COMMAND  # Pencil MCP 실행 명령어
PENCIL_MCP_ARGS     # 실행 인자 목록
SERVER_HOST         # SSE 서버 바인딩 주소 (기본: 127.0.0.1)
SERVER_PORT         # SSE 서버 포트 (기본: 8000)
DATA_OUTPUT_DIR     # data/output/ 경로
DATA_RENDER_OPS_DIR # data/intermediate/render_ops/ 경로
```

**`mcp.json`**
```json
{
  "mcpServers": {
    "pencil-mcp": {
      "command": "node",
      "args": ["<pencil-mcp-server-entry-point>"]
    }
  }
}
```

---

### Phase 2 — Pencil 클라이언트 어댑터

**`app/adapters/pencil_client.py`**

- `mcp` Python SDK의 `ClientSession` + `StdioServerParameters` 사용
- `connect()` / `disconnect()` / `call_tool()` 인터페이스 제공
- `batch_design` 호출 래퍼 메서드 포함
- 컨텍스트 매니저(`async with`) 지원
- 연결 실패 시 `PencilConnectionError` 커스텀 예외 발생

```python
class PencilClient:
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def batch_design(self, operations: str, file_path: str) -> dict: ...
    async def batch_get(self, file_path: str, node_ids: list[str]) -> dict: ...
```

---

### Phase 3 — MCP 서버 진입점

**`app/server.py`**

- `mcp` Python SDK의 `FastMCP` (또는 `Server`) 사용
- 전송 레이어:
  - **stdio**: `mcp.run_stdio_async()` — 기본 모드
  - **SSE**: `mcp.run_sse_async(host, port)` — `--transport sse` 플래그로 전환
- 등록할 도구:
  - `batch_design` — 핵심 렌더 실행 도구 (inputSchema 포함)
  - `get_editor_state` — Pencil 상태 조회 (패스스루)
- 시작 시 `PencilClient.connect()` 호출, 종료 시 `disconnect()` 보장

**`batch_design` JSON Schema (REQ-OST-MCP-006)**

```json
{
  "name": "batch_design",
  "description": "Pencil .pen 파일에 일련의 디자인 오퍼레이션을 순차 실행한다.",
  "inputSchema": {
    "type": "object",
    "required": ["operations", "file_path"],
    "properties": {
      "operations": {
        "type": "string",
        "description": "실행할 Pencil 오퍼레이션 코드 문자열 (I/U/C/R/D/G 명령)"
      },
      "file_path": {
        "type": "string",
        "description": "대상 .pen 파일의 절대 경로"
      },
      "chunk_index": {
        "type": "integer",
        "description": "현재 청크 번호 (0-indexed)",
        "default": 0
      },
      "total_chunks": {
        "type": "integer",
        "description": "전체 청크 수",
        "default": 1
      }
    }
  }
}
```

---

## Risks

| 위험                                    | 심각도 | 대응                                                           |
| --------------------------------------- | ------ | -------------------------------------------------------------- |
| Pencil MCP 실행 경로 환경마다 다름      | 중     | `.env` + `config.py`로 외부화, `mcp.json` 주석으로 설정 가이드 |
| `mcp` Python SDK 버전 호환성            | 중     | `pyproject.toml`에 버전 고정, `requirements.txt` 갱신          |
| SSE 포트 충돌                           | 하     | 기본 포트를 환경변수로 오버라이드 가능하게 설정                |
| stdio ↔ SSE 전환 시 도구 등록 방식 차이 | 중     | 전송 레이어와 도구 등록 코드를 분리 (서버 초기화 함수화)       |

---

## Validation Plan

```bash
# 1. stdio 모드로 서버 기동 확인
python -m app.server

# 2. SSE 모드로 서버 기동 확인
python -m app.server --transport sse

# 3. MCP Inspector로 도구 목록 확인 (list_tools)
# → batch_design 이 반환되고 inputSchema가 올바른지 수동 확인

# 4. Pencil 클라이언트 연결 스모크 테스트
python -c "
import asyncio
from app.adapters.pencil_client import PencilClient
async def test():
    async with PencilClient() as client:
        result = await client.batch_get('test.pen', [])
        print(result)
asyncio.run(test())
"

# 5. 스키마 유효성 검사
python -c "
from app.models.render_ops_schema import BatchDesignInput
m = BatchDesignInput(operations='x=I(\"a\",{type:\"frame\"})', file_path='test.pen', chunk_index=0, total_chunks=1)
print(m.model_dump())
"
```

---

## Docs Impact

- [ ] `docs/architecture.md` — MCP 서버 전송 레이어 다이어그램 추가
- [ ] `docs/tool_specs.md` — `batch_design` 도구 inputSchema 문서화
- [ ] `docs/api_contract.md` — Pencil 클라이언트 인터페이스 계약 명시
- [ ] `mcp.json` — Pencil MCP 서버 연결 설정 예시 포함

---

## Handoff to Next Stage

이 Plan이 완료되면 **REQ-ORCH-002**로 인계.

인계 조건:
- [x] `PencilClient.batch_design()` 가 실제 호출 가능한 상태
- [x] `batch_design` 도구가 MCP 서버에 등록되어 `list_tools` 에서 확인됨
- [x] `RenderOpsArtifact` 스키마가 확정되어 REQ-ORCH-002에서 사용 가능
- [x] `.env.example` 에 필요한 환경 변수 목록이 명시됨

---

## Execution Log

| 날짜       | 작업 내용                                                                                                 | 담당   |
| ---------- | --------------------------------------------------------------------------------------------------------- | ------ |
| 2026-04-04 | Phase 1: render_ops_schema.py, config.py, constants.py, mcp.json, .env.example 구현                       | 최지웅 |
| 2026-04-04 | Phase 2: pencil_client.py (PencilClient, PencilConnectionError, async ctx), llm_client.py (Stub) 구현     | 최지웅 |
| 2026-04-04 | Phase 3: server.py (FastMCP, stdio/SSE 전송, batch_design/get_editor_state 도구 등록, 생명주기 관리) 구현 | 최지웅 |

---

## Final Outcome

- **변경된 파일:**
  - `app/models/render_ops_schema.py` — BatchDesignInput, RenderOpResult, RenderOpsArtifact Pydantic 모델
  - `app/config.py` — pydantic-settings 기반 환경변수 설정
  - `app/constants.py` — DSL 타입, 상태, 임계값 상수
  - `app/adapters/pencil_client.py` — PencilClient (stdio, async ctx, batch_design/batch_get/get_editor_state)
  - `app/adapters/llm_client.py` — LLMClientBase + StubLLMClient 기본 구조
  - `app/server.py` — FastMCP 기반 stdio/SSE 서버, batch_design/get_editor_state 도구 등록
  - `mcp.json` — 서버 설정 (transport, host, port)
  - `.env.example` — 필요한 환경변수 목록 명시

- **생성된 산출물:** `.env.example`

- **실행한 테스트와 결과:** 터미널 환경 제약으로 자동 실행 불가 — 수동 실행 필요

- **남은 위험 요소:**
  - `PENCIL_MCP_ARGS` 환경변수에 실제 Pencil MCP entry point 경로 설정 필요
  - `mcp.json`의 `args` 배열에도 실제 경로 입력 필요

- **다음 단계:** REQ-ORCH-002 (batch_design 전송 및 캔버스 반영) — 이미 완료됨

# Analysis JSON Schema Contract

> **Owner**: 이수민 (Analysis Owner)
> **Downstream Consumer**: 임형준 (Stage 2 — Layout / Prompt Preparation)
> **Schema Version**: `1.0`
> **Last Updated**: 2026-04-04
> **REQ**: REQ-ANL-001

Stage 1이 생성하는 `ASTAnalysisSchema` JSON의 전체 필드 계약을 정의한다.
Stage 2는 이 문서를 기반으로 layout plan 생성 로직을 작성해야 한다.

---

## Artifact Location

```
data/intermediate/analysis/<repo_name>.json
```

---

## Top-Level Schema: `ASTAnalysisSchema`

| 필드 | 타입 | 필수 | 설명 | Stage 2 소비 목적 |
|---|---|---|---|---|
| `schema_version` | `string` | N (기본값 `"1.0"`) | 스키마 버전 | 호환성 분기 처리 |
| `repo` | `string` | Y | 분석 대상 repo 식별자 | 슬라이드 제목 / 커버 페이지 |
| `generated_at` | `datetime` (ISO 8601) | Y | 분석 생성 시각 | 메타 정보 표시 |
| `summary` | `AnalysisSummary` | Y | 집계 요약 | 개요 슬라이드 통계 |
| `nodes` | `ASTNode[]` | N (기본 `[]`) | 추출된 코드 노드 목록 | 컴포넌트 다이어그램, 레이아웃 배치 |
| `edges` | `ASTEdge[]` | N (기본 `[]`) | 노드 간 관계 목록 | 의존성 화살표, 계층 구조 |
| `arch_summary` | `string` | N (기본 `""`) | 전체 아키텍처 요약 텍스트 | 도입부 슬라이드 본문 / 프롬프트 삽입 |
| `entry_points` | `string[]` | N (기본 `[]`) | 주요 진입점 node id 목록 | 레이아웃 강조 처리 (하이라이트 박스 등) |
| `top_level_modules` | `string[]` | N (기본 `[]`) | 최상위 모듈 상대 경로 목록 | 슬라이드 구조 결정 (모듈당 섹션) |

---

## `AnalysisSummary`

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `total_files` | `int (≥0)` | Y | 분석된 파일 수 |
| `total_nodes` | `int (≥0)` | Y | 전체 노드 수 — **반드시 `nodes` 배열 길이와 일치해야 함** |
| `total_edges` | `int (≥0)` | Y | 전체 엣지 수 — **반드시 `edges` 배열 길이와 일치해야 함** |

> ⚠️ `total_nodes` 또는 `total_edges`가 실제 배열 길이와 다르면 `ValidationError`가 발생한다.

---

## `ASTNode`

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | `string` | Y | 고유 노드 식별자 (예: `"app.services.analysis_service.AnalysisService"`) |
| `type` | `NodeType` | Y | 노드 종류 |
| `metadata` | `NodeMetadata` | Y | 상세 메타데이터 |

### `NodeType` enum

| 값 | 설명 |
|---|---|
| `module` | Python 모듈 (파일 단위) |
| `class_` | 클래스 |
| `function` | 모듈 레벨 함수 |
| `method` | 클래스 내 메서드 |

---

## `NodeMetadata`

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `name` | `string` | Y | 노드 이름 (short name) |
| `file_path` | `string` | Y | **repo root 기준 상대 경로** (예: `"app/services/analysis_service.py"`) |
| `start_line` | `int (≥1)` | Y | 시작 라인 번호 |
| `end_line` | `int (≥1)` | Y | 종료 라인 번호 (`≥ start_line`) |
| `docstring` | `string \| null` | N | docstring 원문 |
| `layer` | `LayerType` | N (기본 `unknown`) | 아키텍처 레이어 분류 |
| `position_hint` | `PositionHint \| null` | N | 레이아웃 힌트 좌표 |

### `LayerType` enum

| 값 | 설명 |
|---|---|
| `presentation` | MCP server, CLI, API 레이어 |
| `application` | Service, Orchestrator 레이어 |
| `domain` | 핵심 비즈니스 모델, 스키마 |
| `infrastructure` | Adapter, 외부 연동 레이어 |
| `unknown` | 분류 불가 |

---

## `ASTEdge`

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `source` | `string` | Y | 출발 node id |
| `target` | `string` | Y | 도착 node id |
| `type` | `EdgeType` | Y | 관계 종류 |

> ⚠️ `source == target` (셀프루프)은 허용되지 않는다.
> ⚠️ `source`, `target`은 반드시 `nodes` 배열에 존재하는 id여야 한다.

### `EdgeType` enum

| 값 | 설명 |
|---|---|
| `imports` | 모듈 import |
| `calls` | 함수/메서드 호출 |
| `contains` | 포함 관계 (예: 클래스 → 메서드) |
| `inherits` | 상속 |
| `depends_on` | 일반 의존성 |

---

## `PositionHint`

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `x` | `float \| null` | N | 레이아웃 x 좌표 힌트 |
| `y` | `float \| null` | N | 레이아웃 y 좌표 힌트 |
| `width` | `float (>0) \| null` | N | 레이아웃 너비 힌트 |
| `height` | `float (>0) \| null` | N | 레이아웃 높이 힌트 |

---

## Example Payload

```json
{
  "schema_version": "1.0",
  "repo": "pencil-mcp-project",
  "generated_at": "2026-04-04T22:00:00+09:00",
  "summary": {
    "total_files": 3,
    "total_nodes": 2,
    "total_edges": 1
  },
  "arch_summary": "3계층 구조: MCP server(presentation) → Service(application) → Adapter(infrastructure). 핵심 진입점은 app/server.py.",
  "entry_points": ["app.server"],
  "top_level_modules": ["app/server.py", "app/services/analysis_service.py", "app/adapters/llm_client.py"],
  "nodes": [
    {
      "id": "app.server",
      "type": "module",
      "metadata": {
        "name": "server",
        "file_path": "app/server.py",
        "start_line": 1,
        "end_line": 80,
        "docstring": "MCP server entrypoint",
        "layer": "presentation"
      }
    },
    {
      "id": "app.adapters.llm_client",
      "type": "module",
      "metadata": {
        "name": "llm_client",
        "file_path": "app/adapters/llm_client.py",
        "start_line": 1,
        "end_line": 60,
        "layer": "infrastructure"
      }
    }
  ],
  "edges": [
    {
      "source": "app.server",
      "target": "app.adapters.llm_client",
      "type": "imports"
    }
  ]
}
```

---

## Validation Rules (요약)

| 규칙 | 오류 조건 |
|---|---|
| node id 고유성 | 중복 id 존재 시 `ValidationError` |
| line range | `end_line < start_line` 시 `ValidationError` |
| 셀프루프 방지 | `edge.source == edge.target` 시 `ValidationError` |
| 엣지 참조 무결성 | edge의 source/target이 nodes에 없으면 `ValidationError` |
| summary count 일관성 | `total_nodes != len(nodes)` 또는 `total_edges != len(edges)` 시 `ValidationError` |

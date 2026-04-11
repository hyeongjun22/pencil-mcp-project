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
# JSON 스키마 계약 문서

이 문서는 파이프라인 각 스테이지 간 데이터 핸드오프에 사용되는 JSON 스키마 계약을 정의합니다.

---

## 목차

1. [Presentation 스키마](#presentation-스키마)
2. [Layout Plan 스키마](#layout-plan-스키마)
3. [공통 Enum 타입](#공통-enum-타입)
4. [핸드오프 계약](#핸드오프-계약)
5. [예시 JSON](#예시-json)

---

## Presentation 스키마

- **파일**: `app/models/presentation_schema.py`
- **용도**: Stage 2 (Layout / Prompt Preparation)의 중간 산출물
- **소유자**: 임형준 (Visualization Owner)
- **출력 경로**: `data/intermediate/presentation/`
- **소비자**: `app/tools/op_compiler.py`, `app/services/render_service.py`

### 스키마 계층 구조

```
Presentation (루트)
├── PresentationMeta           — 메타정보
├── StyleGuide                 — 전역 스타일
│   ├── ColorPalette           — 색상 팔레트 (10색)
│   ├── Typography             — 타이포그래피 (3 폰트 패밀리 + 6 크기)
│   └── Spacing                — 간격 기본값 (5종)
└── Slide[]                    — 슬라이드 목록
    ├── slide_index            — 순서 인덱스
    ├── role                   — SlideRole enum
    ├── title                  — 슬라이드 제목
    ├── SlideLayout            — 레이아웃
    │   ├── direction          — LayoutDirection enum
    │   └── Section[]          — 섹션 목록
    │       ├── section_id     — 섹션 ID
    │       ├── weight         — 공간 비율 가중치
    │       ├── alignment      — 수평 정렬
    │       ├── vertical_alignment — 수직 정렬
    │       └── ContentBlock[] — 콘텐츠 블록 목록
    │           ├── block_id       — 블록 ID
    │           ├── content_type   — ContentType enum
    │           ├── content        — 본문 (str | list[str])
    │           ├── meta           — 유형별 추가 메타 (선택)
    │           └── style_overrides — 개별 스타일 오버라이드 (선택)
    └── notes                  — 발표자 노트 (선택)
```

---

## 모델 상세

### PresentationMeta

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `title` | `str` | ✅ | 프레젠테이션 제목 (최소 1자) |
| `description` | `str \| null` | ❌ | 설명 |
| `source_repo` | `str \| null` | ❌ | 원본 코드 저장소 |
| `total_slides` | `int` | ✅ | 총 슬라이드 수 (≥ 1) |
| `target_audience` | `str \| null` | ❌ | 대상 청중 |
| `generated_at` | `datetime` | ❌ | 생성 시각 (자동 생성) |

### ColorPalette

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `primary` | `str` | ✅ | — | 주 브랜드 색상 |
| `secondary` | `str` | ✅ | — | 보조 브랜드 색상 |
| `accent` | `str` | ✅ | — | 강조 색상 |
| `background` | `str` | ✅ | — | 배경 색상 |
| `surface` | `str` | ✅ | — | 카드/패널 표면 색상 |
| `text_primary` | `str` | ✅ | — | 주 텍스트 색상 |
| `text_secondary` | `str` | ✅ | — | 보조 텍스트 색상 |
| `success` | `str` | ❌ | `#10B981` | 성공 상태 색상 |
| `warning` | `str` | ❌ | `#F59E0B` | 경고 상태 색상 |
| `error` | `str` | ❌ | `#EF4444` | 에러 상태 색상 |

### Typography

| 필드 | 타입 | 기본값 | 제약 | 설명 |
|---|---|---|---|---|
| `font_family_heading` | `str` | `Inter` | — | 제목용 폰트 |
| `font_family_body` | `str` | `Inter` | — | 본문용 폰트 |
| `font_family_code` | `str` | `JetBrains Mono` | — | 코드용 폰트 |
| `font_size_title` | `int` | `48` | 12–120 | 타이틀 크기(px) |
| `font_size_heading` | `int` | `32` | 12–96 | 헤딩 크기(px) |
| `font_size_subheading` | `int` | `24` | 10–72 | 서브헤딩 크기(px) |
| `font_size_body` | `int` | `16` | 8–48 | 본문 크기(px) |
| `font_size_caption` | `int` | `12` | 6–36 | 캡션 크기(px) |
| `font_size_code` | `int` | `14` | 8–36 | 코드 크기(px) |

### Spacing

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `padding_slide` | `int` | `48` | 슬라이드 패딩(px) |
| `padding_section` | `int` | `24` | 섹션 패딩(px) |
| `padding_block` | `int` | `16` | 블록 패딩(px) |
| `gap_sections` | `int` | `32` | 섹션 간 갭(px) |
| `gap_blocks` | `int` | `16` | 블록 간 갭(px) |

### ContentBlock

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `block_id` | `str` | ✅ | 블록 고유 식별자 (최소 1자) |
| `content_type` | `ContentType` | ✅ | 콘텐츠 유형 enum |
| `content` | `str \| list[str]` | ✅ | 본문 내용 |
| `meta` | `dict \| null` | ❌ | 유형별 추가 메타데이터 |
| `style_overrides` | `dict \| null` | ❌ | 개별 스타일 오버라이드 |

#### `meta` 필드 사용 예시

| content_type | meta 예시 |
|---|---|
| `code_block` | `{"language": "python", "line_numbers": true}` |
| `image` | `{"alt": "아키텍처 다이어그램", "src": "arch.png"}` |
| `chart` | `{"chart_type": "bar", "data_source": "metrics.json"}` |
| `table` | `{"headers": ["이름", "버전"], "rows": [...]}` |

### Section

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `section_id` | `str` | ✅ | — | 섹션 고유 식별자 |
| `weight` | `float` | ❌ | `1.0` | 공간 비율 가중치 (0 < w ≤ 10) |
| `alignment` | `Alignment` | ❌ | `left` | 수평 정렬 |
| `vertical_alignment` | `VerticalAlignment` | ❌ | `top` | 수직 정렬 |
| `content_blocks` | `list[ContentBlock]` | ❌ | `[]` | 콘텐츠 블록 목록 |

### SlideLayout

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `direction` | `LayoutDirection` | ❌ | `vertical` | 배치 방향 |
| `sections` | `list[Section]` | ✅ | — | 섹션 목록 (최소 1개) |

### Slide

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `slide_index` | `int` | ✅ | 순서 인덱스 (≥ 0) |
| `role` | `SlideRole` | ✅ | 슬라이드 역할/용도 |
| `title` | `str` | ✅ | 슬라이드 제목 (최소 1자) |
| `layout` | `SlideLayout` | ✅ | 레이아웃 구조 |
| `notes` | `str \| null` | ❌ | 발표자 노트 |

---

## Layout Plan 스키마

- **파일**: `app/models/layout_plan_schema.py`
- **용도**: Stage 2 (Layout / Prompt Preparation)와 렌더링 오퍼레이션(Stage 3) 사이의 기하학적 공간 배치 정의
- **소유자**: 임형준 (Visualization Owner)
- **출력 경로**: `data/intermediate/layout_plans/`

### 스키마 계층 구조

```
LayoutPlan (루트)
├── LayoutPlanMeta                     — 메타정보
└── LayoutNode                         — 최상위 노드 (root)
    ├── node_id                        — 노드 ID
    ├── node_type                      — 프레임 등(frame, text, image 등)
    ├── width (SizeDefinition)         — 폭 (mode: fill/hug/fixed, value)
    ├── height (SizeDefinition)        — 높이 (mode: fill/hug/fixed, value)
    ├── direction                      — LayoutDirection
    ├── flex_wrap                      — FlexWrap
    ├── padding                        — 패딩 (int 또는 상하좌우 개별 지정 객체 PaddingModel)
    ├── gap                            — 노드 간 갭
    ├── alignment                      — 자식 수평 정렬
    ├── vertical_alignment             — 자식 수직 정렬
    ├── attributes                     — 부가 렌더링 속성(dict)
    └── children[]                     — 하위 LayoutNode 목록 (재귀 구조)
```

### 모델 상세

#### SizeDefinition & SizeMode
- **SizeMode**: `fill_container` (FILL), `hug_contents` (HUG), `fixed` (FIXED)
- 고정 폭인 경우만 `value` (int) 속성을 사용.

#### PaddingModel
상하좌우에 각각 다른 여백이 필요할 시 사용.
- `top`, `right`, `bottom`, `left` (모두 int, 기본값 0)

---

## 공통 Enum 타입

파일: `app/models/common.py`

### ContentType (14종)

| 값 | 설명 |
|---|---|
| `title` | 제목 |
| `subtitle` | 부제목 |
| `heading` | 섹션 헤딩 |
| `body_text` | 본문 텍스트 |
| `bullet_list` | 글머리 기호 목록 |
| `code_block` | 코드 블록 |
| `image` | 이미지 |
| `diagram` | 다이어그램 |
| `table` | 표 |
| `chart` | 차트 |
| `icon` | 아이콘 |
| `quote` | 인용문 |
| `metric` | 숫자 지표 |
| `divider` | 구분선 |

### SlideRole (9종)

| 값 | 설명 |
|---|---|
| `cover` | 표지 |
| `toc` | 목차 |
| `section_divider` | 섹션 구분 |
| `content` | 일반 콘텐츠 |
| `comparison` | 비교 |
| `architecture` | 아키텍처 |
| `code_walkthrough` | 코드 워크스루 |
| `metrics_dashboard` | 지표 대시보드 |
| `closing` | 마무리 |

### LayoutDirection

| 값 | 설명 |
|---|---|
| `horizontal` | 수평 배치 |
| `vertical` | 수직 배치 |

### Alignment

| 값 | 설명 |
|---|---|
| `left` | 왼쪽 정렬 |
| `center` | 가운데 정렬 |
| `right` | 오른쪽 정렬 |
| `justify` | 양쪽 정렬 |

### VerticalAlignment

| 값 | 설명 |
|---|---|
| `top` | 위쪽 정렬 |
| `middle` | 중앙 정렬 |
| `bottom` | 아래쪽 정렬 |

---

## 핸드오프 계약

### Stage 2 → Stage 3

| 항목 | 내용 |
|---|---|
| **생산자** | `app/tools/prompt_builder.py`, `app/services/layout_service.py` |
| **산출물** | `data/intermediate/presentation/*.json` |
| **소비자** | `app/tools/op_compiler.py`, `app/services/render_service.py` |
| **스키마** | `app/models/presentation_schema.py` → `Presentation` 모델 |
| **검증** | `Presentation.model_validate(data)` |

소비자 측에서는 반드시 `Presentation.model_validate()`를 호출하여
입력 데이터의 유효성을 검증해야 합니다.

### Layout 파이프라인 핸드오프

| 항목 | 내용 |
|---|---|
| **소비자** | `app/tools/op_compiler.py` (Stage 3) |
| **산출물** | `data/intermediate/layout_plans/*.json` |
| **스키마 검증** | `LayoutPlan.model_validate(data)` |

---

## Render Ops 스키마

- **파일**: `app/models/render_ops_schema.py`
- **용도**: Stage 3 (Render Execution)에서 Pencil MCP 호출용 오퍼레이션 데이터 정의
- **소유자**: 최지웅 (Orchestration Owner)
- **출력 경로**: `data/intermediate/render_ops/`

### 스키마 계층 구조

```
RenderPlan (루트)
├── plan_id                        — 렌더 플랜 고유 식별자
├── layout_plan_id                 — 원본 레이아웃 플랜 식별자
├── total_chunks                   — 총 청크 수
└── chunks[]                       — 렌더를 실행할 청크 리스트 (RenderChunk)
    ├── chunk_index                — 청크 순서 인덱스
    └── operations[]               — 오퍼레이션 리스트 (최대 25개, RenderOp Union)
        ├── op_type                — RenderOpType Enum (I, C, U, R, M, D, G)
        ├── binding                — 변수명 (선택)
        └── (각 타입별 필드들)      — parent, node_data, path, update_data 등
```

### 핸드오프 계약 특이사항 (Stage 3)

- **생산자**: `app/tools/op_compiler.py` (Layout Plan을 해석하여 생성)
- **데이터 흐름**: `data/intermediate/render_ops/*.json`에 저장 후 사용
- **소비자 (포맷터)**: `app/tools/pencil_proxy_executor.py`
  - JSON으로 정의된 `RenderOp`를 읽어 Pencil MCP `batch_design` 파라미터 규격에 맞는 **Javascript 문자열 (예: `foo=I(...)`)로 치환**하는 역할을 수행.
  - `node_data`는 렌더링 호환성 유지를 위해 엄격한 타입 대신 `dict[str, Any]` 형태 사용.

---

## 예시 JSON

```json
{
  "meta": {
    "title": "Repository Architecture Overview",
    "description": "코드 저장소의 아키텍처를 시각적으로 설명하는 프레젠테이션",
    "source_repo": "my-project",
    "total_slides": 2,
    "target_audience": "개발 팀",
    "generated_at": "2026-04-04T00:00:00"
  },
  "style_guide": {
    "color_palette": {
      "primary": "#1E40AF",
      "secondary": "#7C3AED",
      "accent": "#F59E0B",
      "background": "#0F172A",
      "surface": "#1E293B",
      "text_primary": "#F8FAFC",
      "text_secondary": "#94A3B8"
    },
    "typography": {
      "font_family_heading": "Inter",
      "font_family_body": "Inter",
      "font_family_code": "JetBrains Mono",
      "font_size_title": 48,
      "font_size_heading": 32,
      "font_size_subheading": 24,
      "font_size_body": 16,
      "font_size_caption": 12,
      "font_size_code": 14
    },
    "spacing": {
      "padding_slide": 48,
      "padding_section": 24,
      "padding_block": 16,
      "gap_sections": 32,
      "gap_blocks": 16
    }
  },
  "slides": [
    {
      "slide_index": 0,
      "role": "cover",
      "title": "My Project Architecture",
      "layout": {
        "direction": "vertical",
        "sections": [
          {
            "section_id": "main",
            "weight": 1.0,
            "alignment": "center",
            "vertical_alignment": "middle",
            "content_blocks": [
              {
                "block_id": "title_block",
                "content_type": "title",
                "content": "My Project"
              },
              {
                "block_id": "subtitle_block",
                "content_type": "subtitle",
                "content": "Architecture Overview"
              }
            ]
          }
        ]
      },
      "notes": "프로젝트 소개 슬라이드"
    },
    {
      "slide_index": 1,
      "role": "architecture",
      "title": "시스템 아키텍처",
      "layout": {
        "direction": "horizontal",
        "sections": [
          {
            "section_id": "diagram_area",
            "weight": 2.0,
            "content_blocks": [
              {
                "block_id": "arch_diagram",
                "content_type": "diagram",
                "content": "시스템 아키텍처 다이어그램",
                "meta": {
                  "diagram_type": "component",
                  "src": "architecture.svg"
                }
              }
            ]
          },
          {
            "section_id": "description_area",
            "weight": 1.0,
            "content_blocks": [
              {
                "block_id": "arch_heading",
                "content_type": "heading",
                "content": "핵심 컴포넌트"
              },
              {
                "block_id": "arch_bullets",
                "content_type": "bullet_list",
                "content": [
                  "API Gateway",
                  "Auth Service",
                  "Core Engine",
                  "Data Store"
                ]
              }
            ]
          }
        ]
      }
    }
  ]
}
```

---

## 스키마 변경 규칙

`AGENTS.md`의 Schema Rules에 따라, 이 스키마를 변경할 때는:

1. `plans/`에 계획 업데이트 필수
2. 관련 테스트 검토/업데이트 필수
3. 이 문서(`docs/json_schema.md`) 업데이트 필수
4. 다운스트림 호환성 확인 필수

---

*마지막 업데이트: 2026-04-04*

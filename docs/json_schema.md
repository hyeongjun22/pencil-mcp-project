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

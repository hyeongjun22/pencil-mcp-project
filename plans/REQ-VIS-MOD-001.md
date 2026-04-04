# REQ-VIS-MOD-001: Presentation 스키마 정의

## 메타데이터

| 항목 | 내용 |
|---|---|
| **요구사항 ID** | REQ-VIS-MOD-001 |
| **카테고리** | 데이터 모델 / 스키마 |
| **제목** | presentation 스키마 정의 |
| **소유자** | 임형준 (Visualization Owner) |
| **상태** | Completed |
| **생성일** | 2026-04-04 |
| **브랜치** | `feat/REQ-VIS-MOD-001-presentation-schema` |

---

## 문제 정의

시각화 파이프라인의 Stage 2 (Layout / Prompt Preparation)에서 생성하는 중간 산출물(presentation)에 대한 정형화된 스키마가 없음. 이 산출물은 Stage 1(Analysis)의 분석 결과를 기반으로 시각화에 적합한 형태로 변환한 데이터이며, Stage 3(Render Execution)의 `render_ops_schema`로 넘겨지는 핵심 인터페이스.

스키마가 없으면:
- 스테이지 간 데이터 계약(contract)이 불명확해짐
- 하류(downstream) 소비자(op_compiler, render_service)가 입력 유효성을 검증할 수 없음
- 중간 산출물의 구조가 문서화되지 않아 협업에 지장

---

## 목표

`app/models/presentation_schema.py`에 Pydantic v2 기반의 presentation 스키마를 정의하여:
1. 시각화 중간 산출물의 구조를 명확히 정형화
2. 런타임 유효성 검증(validation) 지원
3. JSON 직렬화/역직렬화 지원
4. Stage 2 → Stage 3 핸드오프 계약 확립

---

## 수용 기준 (Acceptance Criteria)

1. `presentation_schema.py`에 Pydantic v2 모델이 정의되어 있어야 함
2. 프레젠테이션의 핵심 구성 요소(슬라이드, 섹션, 콘텐츠 블록, 스타일 정보)를 표현 가능해야 함
3. `model_validate()`로 유효한 JSON을 검증할 수 있어야 함
4. `model_json_schema()`로 JSON Schema를 export할 수 있어야 함
5. 예제 JSON 산출물이 `data/intermediate/presentation/`에 생성 가능해야 함
6. 단위 테스트가 통과해야 함
7. `docs/json_schema.md`에 스키마 계약이 문서화되어야 함

---

## 범위

### 포함 (In Scope)
- `app/models/presentation_schema.py` — 스키마 정의
- `app/models/common.py` — 공통 타입 (필요 시)
- `tests/test_presentation_schema.py` — 단위 테스트 (신규)
- `docs/json_schema.md` — 스키마 계약 문서화

### 제외 (Out of Scope)
- `layout_plan_schema.py` (별도 REQ)
- `analysis_schema.py` (이수민 소유)
- `render_ops_schema.py` (최지웅 소유)
- 서비스/도구 구현 (별도 REQ)

---

## 영향받는 파일

| 파일 | 변경 유형 | 설명 |
|---|---|---|
| `app/models/presentation_schema.py` | **신규 작성** | 메인 스키마 정의 |
| `app/models/common.py` | **신규 작성** | 공통 enum, 기본 타입 |
| `tests/test_presentation_schema.py` | **신규 작성** | 스키마 유효성 검사 테스트 |
| `docs/json_schema.md` | **업데이트** | 스키마 계약 문서 |
| `requirements.txt` | **업데이트** | pydantic 의존성 추가 |
| `pyproject.toml` | **업데이트** | 프로젝트 설정 |

---

## 구현 계획

### 1단계: 공통 타입 정의 (`app/models/common.py`)

스테이지 전체에서 공유할 기본 열거형(Enum)과 타입 정의:

```python
# 콘텐츠 유형
class ContentType(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    HEADING = "heading"
    BODY_TEXT = "body_text"
    BULLET_LIST = "bullet_list"
    CODE_BLOCK = "code_block"
    IMAGE = "image"
    DIAGRAM = "diagram"
    TABLE = "table"
    CHART = "chart"
    ICON = "icon"
    QUOTE = "quote"
    METRIC = "metric"
    DIVIDER = "divider"

# 레이아웃 방향
class LayoutDirection(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

# 정렬
class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"

class VerticalAlignment(str, Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"

# 슬라이드 용도
class SlideRole(str, Enum):
    COVER = "cover"
    TOC = "toc"
    SECTION_DIVIDER = "section_divider"
    CONTENT = "content"
    COMPARISON = "comparison"
    ARCHITECTURE = "architecture"
    CODE_WALKTHROUGH = "code_walkthrough"
    METRICS_DASHBOARD = "metrics_dashboard"
    CLOSING = "closing"
```

### 2단계: Presentation 스키마 정의 (`app/models/presentation_schema.py`)

계층 구조:
```
Presentation
├── PresentationMeta (메타정보)
├── StyleGuide (전역 스타일)
│   ├── ColorPalette
│   ├── Typography
│   └── Spacing
└── Slide[] (슬라이드 목록)
    ├── SlideLayout (레이아웃)
    │   └── Section[] (섹션)
    │       └── ContentBlock[] (콘텐츠 블록)
    └── SlideNotes (발표자 노트)
```

핵심 모델:
- **`ColorPalette`**: 프레젠테이션 전역 색상 팔레트 (primary, secondary, accent, background, text 등)
- **`Typography`**: 폰트 패밀리, 크기 프리셋, 굵기 등
- **`Spacing`**: 패딩, 갭, 마진의 기본값
- **`StyleGuide`**: 위 세 가지를 묶는 전역 스타일 가이드
- **`ContentBlock`**: 개별 콘텐츠 요소 (텍스트, 코드, 이미지, 차트 등)
- **`Section`**: 콘텐츠 블록의 논리적 그룹 (예: 좌측 패널, 우측 패널)
- **`SlideLayout`**: 섹션 배치 방식
- **`Slide`**: 단일 슬라이드 (역할, 레이아웃, 콘텐츠, 노트)
- **`PresentationMeta`**: 프레젠테이션 메타정보 (제목, 주제, 대상 청중 등)
- **`Presentation`**: 최상위 루트 모델

### 3단계: 테스트 작성 (`tests/test_presentation_schema.py`)

- 유효한 presentation JSON으로 모델 생성 테스트
- 필수 필드 누락 시 ValidationError 테스트
- 잘못된 enum 값에 대한 검증 테스트
- JSON 직렬화 → 역직렬화 라운드트립 테스트
- `model_json_schema()` export 테스트
- 중첩 구조(Slide → Section → ContentBlock) 테스트

### 4단계: 문서 업데이트 (`docs/json_schema.md`)

- Presentation 스키마 JSON Schema 정의 기술
- 주요 타입 설명 및 사용 예시
- Stage 2 → Stage 3 핸드오프 계약 명시

### 5단계: 프로젝트 설정 업데이트

- `requirements.txt`에 `pydantic>=2.0` 추가
- `pyproject.toml`에 프로젝트 메타데이터 기입

---

## 스키마 설계 상세

### 예시 JSON 산출물 구조

```json
{
  "meta": {
    "title": "Repository Architecture Overview",
    "description": "코드 저장소의 아키텍처를 시각적으로 설명하는 프레젠테이션",
    "source_repo": "my-project",
    "total_slides": 5,
    "target_audience": "개발 팀",
    "generated_at": "2026-04-04T00:00:00Z"
  },
  "style_guide": {
    "color_palette": {
      "primary": "#1E40AF",
      "secondary": "#7C3AED",
      "accent": "#F59E0B",
      "background": "#0F172A",
      "surface": "#1E293B",
      "text_primary": "#F8FAFC",
      "text_secondary": "#94A3B8",
      "success": "#10B981",
      "warning": "#F59E0B",
      "error": "#EF4444"
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
                "content": "My Project",
                "style_overrides": {}
              },
              {
                "block_id": "subtitle_block",
                "content_type": "subtitle",
                "content": "Architecture Overview",
                "style_overrides": {}
              }
            ]
          }
        ]
      },
      "notes": "프로젝트 소개 슬라이드",
      "transition": "fade"
    }
  ]
}
```

---

## 다운스트림 영향 분석

| 소비자 | 영향 | 비고 |
|---|---|---|
| `app/tools/op_compiler.py` | 입력 계약 확립 | Presentation → RenderOps 변환 시 활용 |
| `app/services/render_service.py` | 입력 계약 확립 | 렌더링 서비스 입력으로 활용 |
| `layout_plan_schema.py` | 선행 계약 참조 | Layout → Presentation 변환 관계 |
| `app/tools/prompt_builder.py` | 출력 계약 확립 | 프롬프트로 Presentation 생성 시 목표 스키마 |

---

## 리스크

| 리스크 | 영향 | 완화 방안 |
|---|---|---|
| 스키마 설계가 실제 렌더링 요구와 맞지 않을 수 있음 | 중간 | 다운스트림(render_ops)과 역호환 가능하도록 optional 필드 활용 |
| 다른 스키마가 아직 미정의 상태 | 낮음 | 독립적으로 검증 가능한 구조로 설계 |
| Pydantic v2 문법 차이 | 낮음 | v2 문법(model_validate, model_json_schema) 기준으로 작성 |

---

## 검증 계획

### 자동화 테스트
```bash
python -m pytest tests/test_presentation_schema.py -v
```

### 수동 검증
- 예제 JSON 파일로 스키마 검증
- `model_json_schema()` export 결과 확인
- `docs/json_schema.md` 문서 리뷰

---

## 문서 영향

- `docs/json_schema.md` — Presentation 스키마 계약 추가
- `plans/REQ-VIS-MOD-001.md` — 본 계획 파일 생성

---

## 실행 로그

| 일시 | 상태 | 내용 |
|---|---|---|
| 2026-04-04 | Draft | 계획 작성 완료, 리뷰 요청 |
| 2026-04-04 | Approved | 사용자 피드백: SlideRole/ContentType 충분, 색상 팔레트 충분, transition 필드 제거 |
| 2026-04-04 | In Progress | 구현 시작 |
| 2026-04-04 | Completed | 구현 완료, 39개 테스트 모두 통과 |

---

## 최종 결과

### 변경된 파일

| 파일 | 변경 유형 |
|---|---|
| `app/__init__.py` | 신규 생성 (패키지 초기화) |
| `app/models/__init__.py` | 신규 생성 (패키지 초기화) |
| `app/models/common.py` | 신규 작성 (5개 Enum 타입) |
| `app/models/presentation_schema.py` | 신규 작성 (10개 Pydantic 모델) |
| `tests/test_presentation_schema.py` | 신규 작성 (7개 테스트 클래스, 39개 테스트) |
| `docs/json_schema.md` | 신규 작성 (스키마 계약 문서) |
| `requirements.txt` | 업데이트 (pydantic 의존성) |
| `pyproject.toml` | 업데이트 (프로젝트 메타데이터) |

### 테스트 결과
- `python -m pytest tests/test_presentation_schema.py -v` → **39 passed**

### 산출물
- 스키마: `app/models/presentation_schema.py`
- 문서: `docs/json_schema.md`

### 알려진 리스크
- 다운스트림 스키마(`render_ops_schema.py`)가 미정의 상태이므로, 통합 시 조정 필요

### 다음 핸드오프
- `layout_plan_schema.py` 정의 (REQ-VIS 후속)
- `render_ops_schema.py`와의 계약 정합성 확인 (최지웅)


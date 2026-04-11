# REQ-VIS-MOD-002: Layout Plan 스키마 정의

## 메타데이터

| 항목 | 내용 |
|---|---|
| **요구사항 ID** | REQ-VIS-MOD-002 |
| **카테고리** | 데이터 모델 / 스키마 |
| **제목** | layout plan 스키마 정의 |
| **소유자** | 임형준 (Visualization Owner) |
| **상태** | Approved |
| **생성일** | 2026-04-04 |
| **브랜치** | `feat/REQ-VIS-MOD-002-layout-schema` |

---

## 문제 정의

시각화 파이프라인의 Stage 2 (Layout / Prompt Preparation)에서 생성되는 또 다른 핵심 산출물인 `layout plan`에 대한 정형화된 스키마가 부족함. 
Presentation 스키마가 발표 내용의 논리적 구조(Slide, Section, ContentBlock)를 담는다면, Layout Plan 스키마는 각 Section이나 Block이 화면상에 어떻게 배치될지 구체적인 플렉스박스(Flexbox) 규칙과 기하학적 형태(폭, 높이, 패딩, 정렬 등)를 구조적으로 표현해야 함.

스키마가 명확하지 않으면:
- 랜더링 실행 단계(Stage 3)에서 어떤 형태로 UI를 구성해야 할지 모호해짐.
- 분석 단계(Stage 1)나 프롬프트 생성 시 레이아웃 구조를 검증할 수 없음.
- 컴포넌트 간 공간 배치가 일관성 없이 구성될 수 있음.

---

## 목표

`app/models/layout_plan_schema.py`에 Pydantic v2 기반의 layout_plan 스키마를 정의하여:
1. UI 컴포넌트의 계층적 공간 배치 방식을 정의하는 노드 구조(`LayoutNode`) 확립.
2. Flexbox 기반의 레이아웃 규칙(방향, 갭, 패딩, 정렬, 래핑 등) 속성 정형화.
3. 폭(Width), 높이(Height)에 대한 반응형 동작(fill_container, hug_contents, fixed) 처리 지원.
4. JSON 직렬화/역직렬화 및 유효성 검증 제공.

---

## 수용 기준 (Acceptance Criteria)

1. `layout_plan_schema.py`에 Pydantic v2 모델이 정의되어 있어야 함.
2. Flexbox/레이아웃에 필요한 구조적 특성(크기, 여백, 정렬 등)이 스키마로 표현 가능해야 함.
3. `model_validate()`로 구조적 유효성을 판단할 수 있어야 함.
4. `model_json_schema()`로 JSON Schema를 추출 가능해야 함.
5. 단위 테스트가 작성되고 통과해야 함 (`tests/test_layout_plan_schema.py`).
6. `docs/json_schema.md`에 스키마 계약이 반영되어 문서화되어야 함.

---

## 스키마 설계 상세 (제안)

### 핵심 모델:

1. **`SizeMode` (Enum)**
   - `FILL`: 부모 컨테이너를 가득 채움 (`fill_container`)
   - `HUG`: 자식 콘텐츠 크기에 맞춤 (`hug_contents`)
   - `FIXED`: 고정 크기

2. **`SizeDefinition`**
   - 크기 정의: `mode` (SizeMode) 및 `value` (고정 픽셀일 경우, optional)

3. **`FlexWrap` (Enum)**
   - `NO_WRAP`, `WRAP`

4. **`LayoutNode` (Recursive BaseModel)**
   - `node_id`: 노드 고유 식별자
   - `node_type`: 노드 종류 (예: `frame`, `text`, `image`, `component` 등)
   - `width`: `SizeDefinition`
   - `height`: `SizeDefinition`
   - `direction`: `LayoutDirection` (기존 common Enum 재사용)
   - `flex_wrap`: `FlexWrap`
   - `padding`: 패딩 값 (단일 int 또는 top, right, bottom, left dict)
   - `gap`: 노드 간 간격 (int)
   - `alignment`: `Alignment` (기존 common Enum)
   - `vertical_alignment`: `VerticalAlignment` (기존 common Enum)
   - `attributes`: `dict` (텍스트 값, 렌더링될 실제 값과 같은 부가 속성)
   - `children`: `list[LayoutNode]` (재귀적 포함)

5. **`LayoutPlanMeta` & `LayoutPlan`**
   - 레퍼런스 이미지 ID, 대상 플랫폼 정보 등 메타데이터 포함.
   - 최상위 컨테이너 노드(`root`) 정보를 관리.

---

## 다운스트림 영향 분석

- `app/tools/op_compiler.py`: 전달받은 LayoutPlan을 해석하여 Pencil MCP 서버의 렌더링 오퍼레이션(`I`, `U` 등)으로 직접 치환됨. 따라서 호환성이 높아야 함.
- 기존 Presentation 생성 파이프라인: Presentation 내용과 Layout Plan의 매핑이 조화롭게 이뤄지도록 확장되어야 함.

---

## 검증 계획

### 자동화 테스트
```bash
python -m pytest tests/test_layout_plan_schema.py -v
```

---

## 실행 로그

| 일시 | 상태 | 내용 |
|---|---|---|
| 2026-04-04 | Draft | 계획 작성 완료, 리뷰 요청 |
| 2026-04-04 | Approved | 사용자 피드백: SizeMode(fill/hug/fixed) 충분. 패딩은 단일(int) 및 객체 다 지원 |

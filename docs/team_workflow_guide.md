# 팀원 작업 가이드

> 이 문서는 하네스 엔지니어링(Harness Engineering) 워크플로우에서 **팀원이 실제로 어떻게 작업해야 하는지** 단계별로 설명합니다.
> 세부 규칙은 `AGENTS.md`, `plans/README.md`를 참고하세요.

---

## 🧑‍🤝‍🧑 팀 구성과 담당 영역

| 이름 | 역할 | 담당 스테이지 | 워크스페이스 | 브랜치 접두사 |
|------|------|-------------|------------|-------------|
| 이수민 | Analysis Owner | 1단계 — 코드 분석 | `ws-analysis-sumin` | `feat/REQ-ANL-*` |
| 임형준 | Visualization Owner | 2단계 — 레이아웃/프롬프트 | `ws-visual-hyungjun` | `feat/REQ-VIS-*` |
| 최지웅 | Orchestration Owner | 3단계 — 렌더 실행/검증 | `ws-orchestrator-jiwoong` | `feat/REQ-ORCH-*` |

---

## 🔄 전체 파이프라인 흐름

```
이수민(분석)          임형준(시각화)         최지웅(실행)
    │                    │                    │
    ▼                    ▼                    ▼
 코드 스캔 ──►      레이아웃 설계 ──►     렌더 실행
 AST 파싱            디자인 토큰           청크 분할
 구조 요약            프롬프트 빌드          Pencil 호출
    │                    │                    │
    ▼                    ▼                    ▼
data/intermediate/   data/intermediate/   data/intermediate/
  analysis/            layout_plans/        render_ops/
                       presentation/      data/output/
```

**핵심 원칙:** 각 단계의 산출물은 **파일(Artifact)**로만 다음 사람에게 전달됩니다. 구두 전달이나 채팅으로만 넘기는 것은 금지입니다.

---

## 📋 작업 시작부터 완료까지 — 단계별 체크리스트

### Step 1. 플랜(Plan) 작성

코드를 한 줄이라도 쓰기 전에 `plans/` 폴더에 문서를 먼저 만듭니다.

```bash
# 예시: 이수민이 분석 파이프라인 작업을 시작할 때
plans/REQ-ANL-001.md
```

**플랜에 반드시 포함할 내용:**
- [ ] 요구사항 ID, 제목, 소유자
- [ ] 문제 정의 (Problem)
- [ ] 목표 (Goal)
- [ ] 완료 기준 (Acceptance Criteria) — 체크리스트 형태
- [ ] 범위 (In scope / Out of scope)
- [ ] 영향 받는 파일 목록
- [ ] 검증 방법 (테스트 명령어 포함)

### Step 2. 브랜치 생성

`main`에 직접 푸시하는 것은 **금지**입니다. 반드시 브랜치를 만드세요.

```bash
# 네이밍 규칙: <type>/REQ-{영역}-{번호}-{설명}
git checkout -b feat/REQ-ANL-001-ast-metadata-pipeline
```

**사용 가능한 브랜치 접두사:**

| prefix | 용도 | 예시 |
|---|---|---|
| `feat/` | 새로운 기능 추가 | `feat/REQ-ANL-001-ast-metadata-pipeline` |
| `fix/` | 버그 수정 | `fix/REQ-VIS-002-overlapping-textbox` |
| `refactor/` | 구조 개선 | `refactor/REQ-ORCH-003-split-compiler` |
| `docs/` | 문서만 수정 | `docs/REQ-DOC-001-update-architecture` |
| `chore/` | 설정/의존성/빌드 | `chore/REQ-OPS-001-bump-pydantic` |
| `test/` | 테스트만 추가/수정 | `test/REQ-ANL-002-add-parser-edge-cases` |

> 💡 접두사는 `docs/commit_convention.md`의 type 규칙과 동일하게 사용합니다.

### Step 3. 코드 작성

자신의 소유권 범위 내에서만 작업합니다.

| 담당자 | 수정 가능 영역 |
|--------|-------------|
| 이수민 | `app/tools/repo_scanner.py`, `ast_parser.py`, `arch_summarizer.py`, `app/services/analysis_service.py`, `app/models/analysis_schema.py` |
| 임형준 | `app/tools/layout_planner.py`, `prompt_builder.py`, `app/services/layout_service.py`, `prompt_service.py`, `app/prompts/`, `app/resources/`, `app/models/layout_plan_schema.py`, `presentation_schema.py` |
| 최지웅 | `app/server.py`, `app/orchestrator.py`, `app/tools/op_compiler.py`, `chunk_scheduler.py`, `pencil_proxy_executor.py`, `verifier.py`, `app/services/render_service.py`, `app/adapters/`, `app/models/render_ops_schema.py` |

> ⚠️ **다른 사람의 영역을 수정해야 할 때:** Plan 문서에 사유를 명시하고, 해당 소유자에게 리뷰를 요청합니다.

### Step 4. 산출물 저장

작업 결과물은 반드시 정해진 경로에 파일로 저장합니다.

```
data/
├── intermediate/
│   ├── analysis/          ← 이수민 산출물
│   ├── layout_plans/      ← 임형준 산출물
│   ├── presentation/      ← 임형준 산출물
│   └── render_ops/        ← 최지웅 산출물
└── output/                ← 최지웅 최종 결과물
```

### Step 5. 테스트 실행

자신의 담당 영역에 맞는 테스트를 돌립니다.

```bash
# 이수민
pytest tests/test_ast_parser.py

# 임형준
pytest tests/test_layout_planner.py

# 최지웅
pytest tests/test_op_compiler.py
pytest tests/test_chunk_scheduler.py
pytest tests/test_pencil_proxy_executor.py
```

### Step 6. 플랜 업데이트

코드를 다 작성했으면 Plan 문서의 **Execution Notes**와 **Final Outcome** 섹션을 업데이트합니다.

기록할 내용:
- 실제로 변경된 파일 목록
- 생성된 산출물 경로
- 실행한 테스트와 결과
- 남아있는 위험 요소
- 다음 담당자에게 넘길 내용

### Step 7. PR 생성 및 리뷰

PR을 열면 `.github/pull_request_template.md` 양식이 자동으로 뜹니다.  
**모든 체크리스트 항목을 빠짐없이 확인**한 후 리뷰를 요청합니다.

**리뷰 규칙:**
- 최소 **1명 이상**의 팀원 리뷰 필수
- 다른 사람의 영역을 건드린 경우 → **해당 소유자의 리뷰 필수**
- 통합(Integration) PR → **3명 전원 리뷰 권장**

---

## 🚫 절대 하면 안 되는 것 (Forbidden)

| 금지 사항 | 이유 |
|----------|------|
| `main`에 직접 push | 코드 충돌 및 추적 불가 |
| Plan 없이 코딩 시작 | 범위 관리 실패, 리뷰 불가 |
| 여러 목적을 한 PR에 섞기 | 리뷰 부담 증가, 롤백 어려움 |
| 스키마(`app/models/`) 몰래 변경 | 다음 파트 담당자 작업이 깨짐 |
| 산출물 없이 "다 했어요" 구두 전달 | 추적 불가, 핸드오프 실패 |
| 비밀키/시크릿 커밋 | 보안 사고 |

---

## 📦 핸드오프(인수인계) 체크리스트

다음 단계 담당자에게 넘길 때 아래를 모두 충족해야 합니다.

- [ ] Plan 문서의 Final Outcome 섹션이 채워져 있는가?
- [ ] 산출물이 `data/intermediate/` 올바른 경로에 저장되었는가?
- [ ] 스키마 검증을 통과했는가? (JSON이 `app/models/` 기준에 맞는가?)
- [ ] 변경된 파일 목록이 명시되어 있는가?
- [ ] 알려진 위험이나 제한 사항이 기록되어 있는가?

**좋은 핸드오프 예시:**
> ✅ Analysis JSON을 `data/intermediate/analysis/project_x.json`에 저장함.  
> `analysis_schema.py` 기준 검증 완료.  
> 다음 단계: 레이아웃 플래닝 (임형준).  
> 알려진 이슈: 중첩 클래스의 데코레이터 파싱 후속 처리 필요.

---

## 🗂️ 스키마 변경 시 특별 절차

`app/models/` 내의 파일을 수정해야 할 때는 **반드시** 아래를 따릅니다.

1. Plan 문서에 변경 사유와 영향 범위를 명시
2. 해당 스키마를 쓰는 **다음 파트 담당자에게 사전 고지**
3. 관련 테스트 업데이트
4. `docs/json_schema.md` 등 문서 반영
5. PR에서 Schema / Contract Impact 섹션 체크

---

## ❓ 자주 묻는 질문

**Q: 다른 사람의 코드를 참고만 하는 건 괜찮나요?**  
A: 네, 읽기(Read)는 자유입니다. 수정(Write)만 소유권 규칙을 따르면 됩니다.

**Q: 작업 범위가 커져서 Plan이 부족하면?**  
A: 새로운 REQ 파일을 분리해서 만드세요 (예: `REQ-ANL-002.md`).

**Q: 공유 영역(`AGENTS.md`, `plans/`, `docs/`)을 수정하고 싶으면?**  
A: `ws-control-shared` 워크스페이스에서 Plan을 먼저 작성하고 팀원과 합의 후 진행합니다.

**Q: AI 에이전트가 작업할 때도 같은 규칙인가요?**  
A: 네, `AGENTS.md` 하단의 "If You Are an Agent" 섹션에 동일한 순서가 정의되어 있습니다.

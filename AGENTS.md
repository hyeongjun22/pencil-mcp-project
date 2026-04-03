# AGENTS.md

## Purpose
This repository is operated with an Antigravity-style workflow.

All contributors and agents must follow this order:

1. Understand the task
2. Create or update a plan in `plans/`
3. Work inside the correct ownership scope
4. Produce intermediate artifacts when needed
5. Validate with tests/checks
6. Open a focused PR

Do not start implementation before creating or updating a plan file.

---

## Team Ownership

### 임형준 — Visualization Owner
Primary responsibilities:
- reference-image-based layout extraction
- Flexbox/layout structure design
- design token structure
- template-based prompt engine

Primary code ownership:
- `app/tools/layout_planner.py`
- `app/tools/prompt_builder.py`
- `app/services/layout_service.py`
- `app/services/prompt_service.py`
- `app/prompts/`
- `app/resources/templates/`
- `app/resources/design_tokens/`
- `app/models/layout_plan_schema.py`
- `app/models/presentation_schema.py`

Primary artifact ownership:
- `data/intermediate/layout_plans/`
- `data/intermediate/presentation/`

### 이수민 — Analysis Owner
Primary responsibilities:
- static repository/code analysis
- AST-based metadata extraction
- analysis JSON generation

Primary code ownership:
- `app/tools/repo_scanner.py`
- `app/tools/ast_parser.py`
- `app/tools/arch_summarizer.py`
- `app/services/analysis_service.py`
- `app/models/analysis_schema.py`

Primary artifact ownership:
- `data/intermediate/analysis/`

### 최지웅 — Orchestration Owner
Primary responsibilities:
- MCP server
- batch_design transformation
- 20~25 unit chunk scheduling
- Pencil execution proxy
- end-to-end execution verification

Primary code ownership:
- `app/server.py`
- `app/orchestrator.py`
- `app/tools/op_compiler.py`
- `app/tools/chunk_scheduler.py`
- `app/tools/pencil_proxy_executor.py`
- `app/tools/verifier.py`
- `app/services/render_service.py`
- `app/adapters/pencil_client.py`
- `app/adapters/llm_client.py`
- `app/models/render_ops_schema.py`

Primary artifact ownership:
- `data/intermediate/render_ops/`
- `data/output/`

---

## Shared Control Rule
The following are shared control areas:
- `AGENTS.md`
- `plans/`
- `docs/`
- `.github/pull_request_template.md`
- schema contracts that affect multiple stages

Shared control changes must be written in a plan first.

---

## Project Workflow

### Plan First
Before changing code, you must:
- identify the relevant requirement ID
- create or update a file in `plans/`
- define goal, scope, risks, and validation
- confirm the expected handoff artifact
- note acceptance criteria

No coding without a plan.

### One Logical Change
One PR must contain one logical change only.

Good:
- AST metadata extraction update only
- layout token mapping update only
- chunk retry logic update only

Bad:
- parser refactor + layout redesign + proxy execution update in one PR

### Ownership First
Work inside your owned stage by default.

You may read any file needed for context, but do not broadly modify another owner's area unless:
- the plan explicitly allows it
- the downstream or upstream owner is noted
- the change is documented in the plan

---

## Pipeline Handoff Rules

### Stage 1 — Analysis
Owner: 이수민

Output expectations:
- repository scan results
- AST-derived metadata
- architecture summary
- analysis JSON artifact

Write outputs to:
- `data/intermediate/analysis/`

### Stage 2 — Layout / Prompt Preparation
Owner: 임형준

Inputs:
- analysis artifacts from Stage 1
- reference image rules
- design token conventions
- layout schema expectations

Output expectations:
- layout plan artifact
- presentation-oriented structure
- prompt-ready template data

Write outputs to:
- `data/intermediate/layout_plans/`
- `data/intermediate/presentation/`

### Stage 3 — Render Execution
Owner: 최지웅

Inputs:
- layout plan artifacts
- prompt-ready structures
- render schema rules

Output expectations:
- render ops
- chunked execution units
- Pencil proxy execution results
- verification status
- screenshots / exports / logs

Write outputs to:
- `data/intermediate/render_ops/`
- `data/output/`

---

## Directory Rules

### `app/server.py`
- MCP server entrypoint only
- registration and startup wiring
- do not place business logic here

### `app/orchestrator.py`
- top-level flow coordination
- stage ordering and handoff
- no schema definitions here

### `app/tools/`
- single-purpose stage logic
- small, composable functions
- avoid hidden cross-stage coupling

### `app/services/`
- orchestration within a bounded domain
- combine tools
- do not become god-objects

### `app/models/`
- schema and contract definitions only
- no network calls
- no rendering logic
- no filesystem-heavy behavior

### `app/prompts/`
- prompt text/templates only
- no business logic

### `app/adapters/`
- external system boundaries only
- MCP, Pencil, LLM, file integrations

### `app/utils/`
- generic helpers only
- avoid domain-specific coupling

### `data/`
- `input/`: raw source inputs
- `intermediate/`: stage handoff artifacts
- `output/`: final execution results

### `tests/`
- should map to production responsibilities
- every important change should affect tests when relevant

### `docs/`
- architecture, flow, schema, and contracts
- chat decisions do not count until written here

---

## Schema Rules

Any change to:
- `app/models/analysis_schema.py`
- `app/models/layout_plan_schema.py`
- `app/models/presentation_schema.py`
- `app/models/render_ops_schema.py`

requires:
- a plan update
- related test review/update
- docs update or explicit PR explanation
- downstream compatibility check

No silent schema changes.

---

## Testing Rules

At minimum, update or run relevant tests for the changed stage.

### Analysis-related
- `tests/test_ast_parser.py`

### Layout-related
- `tests/test_layout_planner.py`

### Render compilation-related
- `tests/test_op_compiler.py`

### Chunking-related
- `tests/test_chunk_scheduler.py`

### Pencil proxy-related
- `tests/test_pencil_proxy_executor.py`

If a change crosses multiple stages, note the cross-stage risk in the plan.

---

## Branch Rules

Branch naming format:

`<type>/REQ-{AREA}-{NUMBER}-{description}`

### Branch prefix types

| prefix | 용도 |
|---|---|
| `feat/` | 새로운 기능 추가 |
| `fix/` | 버그 수정 |
| `refactor/` | 동작 변화 없는 구조 개선 |
| `docs/` | 문서만 수정 |
| `chore/` | 설정, 의존성, 빌드 관련 |
| `test/` | 테스트만 추가/수정 |

> prefix는 `docs/commit_convention.md`의 type 규칙과 동일하게 사용합니다.

Examples:
- `feat/REQ-ANL-001-ast-metadata-pipeline`
- `feat/REQ-VIS-001-layout-token-engine`
- `feat/REQ-ORCH-001-render-chunk-proxy`
- `feat/REQ-INT-001-e2e-integration`
- `fix/REQ-VIS-002-overlapping-textbox`
- `refactor/REQ-ORCH-003-split-compiler`
- `docs/REQ-DOC-001-update-architecture`
- `chore/REQ-OPS-001-bump-pydantic`

---

## Antigravity Workspace Rules

Recommended workspaces:
- `ws-analysis-sumin`
- `ws-visual-hyungjun`
- `ws-orchestrator-jiwoong`
- `ws-control-shared`

### Workspace rule
One workspace should have:
- one main objective
- one active plan
- one related branch
- one dominant owner

Do not stack unrelated work in the same workspace.

### Shared control workspace
Use `ws-control-shared` for:
- plan approval/update
- schema-impact review
- docs review
- PR scope review
- integration coordination

---

## Required Completion Report

When finishing a task, report:
- goal completed
- files changed
- artifacts produced
- tests run
- known risks
- next recommended handoff

---

## Documentation Rules

Update docs when changing:
- architecture flow
- schema shape
- API contract
- handoff artifact format
- orchestration order
- prompt contract expectations

If docs are not updated, explain why in the PR.

---

## Forbidden

- No direct push to `main`
- No implementation without a plan
- No large mixed-purpose PRs
- No silent schema changes
- No undocumented prompt contract changes
- No committing secrets
- No broad edits outside your ownership area without plan note
- No bypassing artifact handoff with ad-hoc undocumented objects

---

## Review Rules

- At least one teammate review before merge
- Cross-stage changes require review from the affected owner
- Integration PRs should be reviewed by all three owners when possible

---

## If You Are an Agent
Follow this exact order:

1. Read `AGENTS.md`
2. Read the relevant plan file in `plans/`
3. Inspect only the files needed for the task
4. Confirm the expected artifact and acceptance criteria
5. Make minimal scoped changes
6. Run relevant validation
7. Update the plan with outcome notes
8. Prepare a concise PR summary

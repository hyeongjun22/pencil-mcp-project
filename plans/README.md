# plans/README.md

## Purpose
The `plans/` directory is the implementation control layer of this repository.

Every meaningful task must begin with a plan.
A plan is required before coding.

This repository follows a stage-based pipeline:

1. analysis
2. layout / prompt preparation
3. render orchestration
4. integration

Plans make stage ownership, handoff artifacts, risks, and validation explicit.

---

## Plan Naming

Use requirement-style IDs.

Format:
`REQ-{AREA}-{NUMBER}.md`

Recommended areas:
- `ANL` — analysis
- `VIS` — visualization / layout / prompt
- `ORCH` — orchestration / execution
- `INT` — integration
- `DOC` — documentation
- `OPS` — operational improvements

Examples:
- `REQ-ANL-001.md`
- `REQ-VIS-001.md`
- `REQ-ORCH-001.md`
- `REQ-INT-001.md`

---

## Required Plan Fields

Every plan should include:

- metadata
- problem
- goal
- acceptance criteria
- scope
- affected files
- implementation plan
- risks
- validation plan
- docs impact
- execution log
- final outcome

---

## Ownership Mapping

### Analysis Plans
Owner: 이수민

Typical scope:
- repo scanning
- AST parsing
- architecture summarization
- analysis artifact generation

Main artifact:
- `data/intermediate/analysis/`

### Visualization Plans
Owner: 임형준

Typical scope:
- reference-based layout rules
- design token structure
- layout planning
- prompt template preparation

Main artifacts:
- `data/intermediate/layout_plans/`
- `data/intermediate/presentation/`

### Orchestration Plans
Owner: 최지웅

Typical scope:
- MCP server flow
- batch_design transform
- render ops generation
- chunking
- Pencil proxy execution
- verification

Main artifacts:
- `data/intermediate/render_ops/`
- `data/output/`

### Integration Plans
Owner: shared

Typical scope:
- end-to-end stage connection
- contract validation
- artifact compatibility
- final pipeline verification

---

## Plan Lifecycle

### 1. Draft
Create the plan before coding.

Must define:
- problem
- scope
- ownership
- expected artifact
- acceptance criteria

### 2. In Progress
Update when implementation starts.

Add:
- touched files
- deviations
- risks found
- blockers

### 3. Ready for Review
Update after validation.

Add:
- tests run
- output artifacts
- known limitations

### 4. Completed
Finalize after merge or handoff.

Add:
- actual changed files
- final result
- follow-up tasks

---

## Handoff Rule

Do not hand off work with only a chat summary.

A proper handoff includes:
- updated plan status
- artifact path
- changed files
- known risks
- next owner or next stage

Good handoff example:
- Analysis JSON written to `data/intermediate/analysis/project_x.json`
- Schema validated against `analysis_schema.py`
- Next stage: layout planning
- Known issue: decorators in nested classes need follow-up

---

## Scope Rule

One plan should represent one logical change.

Good:
- improve AST metadata extraction
- add layout token normalization
- add chunk size constraint logic

Bad:
- parser refactor + layout redesign + proxy retry changes in one plan

If scope grows too much, split into another REQ file.

---

## Schema Rule

If a plan changes any schema in `app/models/`, it must explicitly include:
- affected schema file
- downstream consumer
- compatibility risk
- required test updates
- docs impact

---

## Minimum Validation Rule

Every completed plan should record validation.

Examples:
- unit tests
- integration tests
- schema validation
- manual artifact inspection
- Pencil execution smoke test

---

## Current Core Plans

Recommended starting files:
- `REQ-ANL-001.md`
- `REQ-VIS-001.md`
- `REQ-ORCH-001.md`
- `REQ-INT-001.md`

---

## Final Rule
No code change is complete until:
- the plan is updated
- validation is recorded
- handoff is explicit
- the PR is scoped correctly

## Summary
Briefly describe this PR.

- Requirement ID:
- Plan file:
- Workspace:
- Branch:
- Owner:
- Related issue/thread:

## What Changed
- 
- 
- 

## Why
- 
- 

## Stage Ownership
Check the primary stage for this PR.

- [ ] Analysis
- [ ] Visualization / Layout / Prompt
- [ ] Orchestration / Execution
- [ ] Integration
- [ ] Docs only

## Scope Check
- [ ] This PR contains one logical change only
- [ ] No unrelated refactor is included
- [ ] No out-of-scope ownership changes are hidden in this PR

## Files Changed
- `app/...`
- `tests/...`
- `docs/...`
- `plans/...`

## Artifact / Handoff Impact
What artifact does this PR produce or change?

- [ ] `data/intermediate/analysis/`
- [ ] `data/intermediate/layout_plans/`
- [ ] `data/intermediate/presentation/`
- [ ] `data/intermediate/render_ops/`
- [ ] `data/output/`
- [ ] no artifact impact

Details:
- 

## Validation
### Checks run
- [ ] `pytest tests/test_ast_parser.py`
- [ ] `pytest tests/test_layout_planner.py`
- [ ] `pytest tests/test_op_compiler.py`
- [ ] `pytest tests/test_chunk_scheduler.py`
- [ ] `pytest tests/test_pencil_proxy_executor.py`
- [ ] manual validation
- [ ] not applicable

### Commands
```bash
# paste commands here
```

### Results
- 

## Schema / Contract Impact
- [ ] no schema change
- [ ] schema updated
- [ ] downstream compatibility checked
- [ ] docs updated accordingly

Details:
- 

## Plan Check
- [ ] I created or updated the relevant file in `plans/`
- [ ] I updated execution notes or final outcome
- [ ] Any deviation from the original plan is explained below

### Deviation from Plan
- None
- Or explain here:

## Docs Impact
- [ ] docs updated
- [ ] docs not needed

If not needed, explain:
- 

## Commit Convention Check
> 자세한 규칙은 [`docs/commit_convention.md`](../docs/commit_convention.md)를 참고하세요.

- [ ] 모든 커밋 메시지가 `<type>(<scope>): <summary>` 형식을 따르는가
- [ ] 각 커밋이 **한 가지 논리적 변경**만 포함하는가
- [ ] `summary`가 50자 이내이며, 현재형/명령형으로 작성되었는가
- [ ] 관련 없는 변경(포맷팅, 리팩터링 등)이 기능 커밋에 섞여 있지 않은가
- [ ] 테스트 가능한 변경에 `Tested:` 섹션이 포함되어 있는가

사용한 type/scope:
- 

## Risks / Review Focus
Please review especially for:
- 
- 

## Merge Checklist
- [ ] Ready for review
- [ ] No secret or local-only config committed
- [ ] Handoff is explicit
- [ ] Tests were updated where needed
- [ ] PR scope is still focused
- [ ] Commit convention is followed (`docs/commit_convention.md`)

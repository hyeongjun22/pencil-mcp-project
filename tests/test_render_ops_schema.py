import pytest
from pydantic import ValidationError
from app.models.render_ops_schema import (
    RenderOpType,
    InsertOp,
    CopyOp,
    UpdateOp,
    ReplaceOp,
    MoveOp,
    DeleteOp,
    GenerateImageOp,
    RenderChunk,
    RenderPlan,
    RenderOp
)

def test_insert_op_validation():
    op = InsertOp(
        op_type=RenderOpType.INSERT,
        binding="container",
        parent="root_id",
        node_data={"type": "frame", "width": 200}
    )
    assert op.binding == "container"
    assert op.parent == "root_id"
    assert op.node_data["type"] == "frame"

    # missing parent should fail
    with pytest.raises(ValidationError):
        InsertOp(op_type=RenderOpType.INSERT, node_data={})

def test_render_chunk_max_length():
    ops = [
        DeleteOp(op_type=RenderOpType.DELETE, node_id=f"node_{i}")
        for i in range(26)
    ]
    
    with pytest.raises(ValidationError) as exc_info:
        RenderChunk(chunk_index=0, operations=ops)
    
    assert "List should have at most 25 items" in str(exc_info.value) or "too_long" in str(exc_info.value)

def test_render_plan_serialization():
    op1 = InsertOp(
        op_type=RenderOpType.INSERT,
        parent="root",
        node_data={"type": "text", "content": "Hello"}
    )
    op2 = UpdateOp(
        op_type=RenderOpType.UPDATE,
        path="child_1",
        update_data={"content": "World"}
    )
    
    chunk = RenderChunk(chunk_index=0, operations=[op1, op2])
    plan = RenderPlan(
        plan_id="plan-123",
        layout_plan_id="layout-123",
        total_chunks=1,
        chunks=[chunk]
    )
    
    # Dump to json and reload
    plan_json = plan.model_dump_json()
    loaded_plan = RenderPlan.model_validate_json(plan_json)
    
    assert loaded_plan.plan_id == "plan-123"
    assert len(loaded_plan.chunks) == 1
    assert len(loaded_plan.chunks[0].operations) == 2
    assert isinstance(loaded_plan.chunks[0].operations[0], InsertOp)
    assert isinstance(loaded_plan.chunks[0].operations[1], UpdateOp)
    
    # check discriminated union works
    assert loaded_plan.chunks[0].operations[0].op_type == RenderOpType.INSERT
    assert loaded_plan.chunks[0].operations[1].op_type == RenderOpType.UPDATE

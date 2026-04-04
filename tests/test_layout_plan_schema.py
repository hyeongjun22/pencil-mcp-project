import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.common import Alignment, LayoutDirection, VerticalAlignment
from app.models.layout_plan_schema import (
    FlexWrap,
    LayoutNode,
    LayoutPlan,
    LayoutPlanMeta,
    PaddingModel,
    SizeDefinition,
    SizeMode,
)


def test_size_definition():
    """크기 정의 모델 테스트."""
    # 유효한 모드: FILL
    size_fill = SizeDefinition(mode=SizeMode.FILL)
    assert size_fill.mode == SizeMode.FILL
    assert size_fill.value is None

    # 유효한 모드: FIXED (값 지정)
    size_fixed = SizeDefinition(mode=SizeMode.FIXED, value=100)
    assert size_fixed.mode == SizeMode.FIXED
    assert size_fixed.value == 100

    # 유효하지 않은 모드 검증
    with pytest.raises(ValidationError):
        SizeDefinition(mode="invalid_mode")


def test_padding_variations():
    """패딩 값 variation (int vs dict) 검증."""
    # 1. 단일 int (default = 0)
    node1 = LayoutNode(
        node_id="n1",
        node_type="frame",
        width=SizeDefinition(mode=SizeMode.FILL),
        height=SizeDefinition(mode=SizeMode.FILL),
        padding=20,
    )
    assert node1.padding == 20

    # 2. Pydantic Model 주입
    node2 = LayoutNode(
        node_id="n2",
        node_type="frame",
        width=SizeDefinition(mode=SizeMode.FILL),
        height=SizeDefinition(mode=SizeMode.FILL),
        padding=PaddingModel(top=10, right=20, bottom=10, left=20),
    )
    assert isinstance(node2.padding, PaddingModel)
    assert node2.padding.top == 10
    assert node2.padding.right == 20

    # 3. Dict 주입 (자동 파싱되는지 검증)
    node3 = LayoutNode(
        node_id="n3",
        node_type="frame",
        width=SizeDefinition(mode=SizeMode.FILL),
        height=SizeDefinition(mode=SizeMode.FILL),
        padding={"top": 5, "right": 5, "bottom": 5, "left": 5},
    )
    assert isinstance(node3.padding, PaddingModel)
    assert node3.padding.top == 5


def test_layout_node_recursive():
    """재귀적 노드 구조 생성 테스트."""
    child_node = LayoutNode(
        node_id="child1",
        node_type="text",
        width=SizeDefinition(mode=SizeMode.HUG),
        height=SizeDefinition(mode=SizeMode.HUG),
        attributes={"text": "Hello World"}
    )
    
    parent_node = LayoutNode(
        node_id="parent1",
        node_type="frame",
        width=SizeDefinition(mode=SizeMode.FILL),
        height=SizeDefinition(mode=SizeMode.FIXED, value=200),
        direction=LayoutDirection.HORIZONTAL,
        gap=16,
        children=[child_node]
    )
    
    assert parent_node.node_id == "parent1"
    assert len(parent_node.children) == 1
    assert parent_node.children[0].node_id == "child1"
    assert parent_node.children[0].attributes["text"] == "Hello World"


def test_layout_plan_valid():
    """전체 Layout Plan 구조 유효성 테스트."""
    now = datetime.now()
    meta = LayoutPlanMeta(reference_id="ref123", target_platform="web", generated_at=now)
    
    root_node = LayoutNode(
        node_id="root",
        node_type="frame",
        width=SizeDefinition(mode=SizeMode.FILL),
        height=SizeDefinition(mode=SizeMode.FILL),
        direction=LayoutDirection.VERTICAL,
        padding=PaddingModel(top=24, right=24, bottom=24, left=24),
    )
    
    plan = LayoutPlan(meta=meta, root=root_node)
    
    assert plan.meta.reference_id == "ref123"
    assert plan.root.node_id == "root"
    assert plan.root.direction == LayoutDirection.VERTICAL

    # 직렬화 / 역직렬화 테스트
    json_data = plan.model_dump_json()
    parsed_plan = LayoutPlan.model_validate_json(json_data)
    assert parsed_plan.meta.reference_id == "ref123"
    assert parsed_plan.root.width.mode == SizeMode.FILL
    assert isinstance(parsed_plan.root.padding, PaddingModel)
    assert parsed_plan.root.padding.top == 24


def test_layout_plan_invalid():
    """오류 필드 주입 시 ValidationError 발생하는지 테스트."""
    with pytest.raises(ValidationError):
        LayoutNode(
            node_id="error_node",
            node_type="frame",
            # width 누락
            height=SizeDefinition(mode=SizeMode.FILL),
        )

    with pytest.raises(ValidationError):
        LayoutNode(
            node_id="error_node2",
            node_type="text",
            width=SizeDefinition(mode=SizeMode.FILL),
            height=SizeDefinition(mode=SizeMode.FILL),
            padding="string padding is invalid"  # 타입 오류
        )


def test_json_schema_export():
    """JSON 스키마 출력 테스트."""
    schema = LayoutPlan.model_json_schema()
    assert schema["type"] == "object"
    assert "LayoutNode" in schema["$defs"]
    assert "SizeDefinition" in schema["$defs"]
    assert "PaddingModel" in schema["$defs"]

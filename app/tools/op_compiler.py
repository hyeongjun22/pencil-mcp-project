"""
op_compiler.py — Layout Plan JSON → Pencil DSL operations 문자열 변환

소유자: 최지웅 (REQ-ORCH-002)

임형준(VIS)이 생성한 layout plan JSON을 읽어
Pencil batch_design에서 실행할 수 있는 DSL 코드 문자열 목록으로 변환한다.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.constants import (
    OP_COPY,
    OP_DELETE,
    OP_IMAGE,
    OP_INSERT,
    OP_MOVE,
    OP_REPLACE,
    OP_UPDATE,
)

logger = logging.getLogger(__name__)

# var 이름 생성용 카운터 (컴파일 세션마다 리셋)
_VAR_COUNTER: int = 0

# parent binding: parent key → var name
_PARENT_BINDINGS: dict[str, str] = {}


def _reset_state() -> None:
    global _VAR_COUNTER, _PARENT_BINDINGS
    _VAR_COUNTER = 0
    _PARENT_BINDINGS = {}


def _next_var() -> str:
    global _VAR_COUNTER
    name = f"var{_VAR_COUNTER}"
    _VAR_COUNTER += 1
    return name


def _format_value(v: Any) -> str:
    """Python 값을 Pencil DSL 인라인 리터럴로 변환한다."""
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dict):
        pairs = ", ".join(f'"{k}":{_format_value(val)}' for k, val in v.items())
        return "{" + pairs + "}"
    if isinstance(v, list):
        items = ", ".join(_format_value(i) for i in v)
        return "[" + items + "]"
    return f'"{v}"'


def _format_node_data(node: dict[str, Any]) -> str:
    """node dict를 Pencil DSL 오브젝트 리터럴로 변환한다."""
    pairs = ", ".join(f'{k}:{_format_value(v)}' for k, v in node.items())
    return "{" + pairs + "}"


def _resolve_parent(parent_key: str) -> str:
    """
    parent_key를 Pencil DSL parent 표현으로 변환한다.

    - "document" 는 예약어로 그대로 사용
    - 이전에 생성된 var 이름이 있으면 그것을 사용
    - 없으면 큰따옴표로 묶인 ID 문자열로 처리
    """
    if parent_key == "document":
        return "document"
    if parent_key in _PARENT_BINDINGS:
        return _PARENT_BINDINGS[parent_key]
    return f'"{parent_key}"'


def compile_op(op: dict[str, Any], slide_id: str) -> str | None:
    """
    단일 operation dict를 Pencil DSL 코드 한 줄로 변환한다.

    Args:
        op:        operation dict (type, parent, node, path, updateData 등)
        slide_id:  해당 op이 속한 슬라이드 ID (바인딩 추적에 사용)

    Returns:
        DSL 코드 문자열, 변환 불가 시 None
    """
    op_type = op.get("type", "").upper()

    # ── I (INSERT) ───────────────────────────────────────────────────────────
    if op_type == OP_INSERT:
        parent_key = op.get("parent", "document")
        parent_expr = _resolve_parent(parent_key)
        node = op.get("node", {})
        node_data = _format_node_data(node)
        var = _next_var()

        # 슬라이드 최상위 노드는 slide_id로 바인딩 등록
        node_name = node.get("name") or node.get("id") or ""
        if node_name:
            _PARENT_BINDINGS[node_name] = var
        # slide_id로도 등록 (첫 번째 insert가 slide 루트인 경우)
        if parent_key in ("document", "") and slide_id not in _PARENT_BINDINGS:
            _PARENT_BINDINGS[slide_id] = var

        return f"{var}=I({parent_expr},{node_data})"

    # ── U (UPDATE) ───────────────────────────────────────────────────────────
    if op_type == OP_UPDATE:
        path = op.get("path", "")
        path_expr = _resolve_parent(path) if path in _PARENT_BINDINGS else f'"{path}"'
        update_data = _format_node_data(op.get("updateData", {}))
        var = _next_var()
        return f'U({path_expr},{update_data})'

    # ── C (COPY) ─────────────────────────────────────────────────────────────
    if op_type == OP_COPY:
        source = op.get("source", "")
        parent_key = op.get("parent", "document")
        parent_expr = _resolve_parent(parent_key)
        copy_data = _format_node_data(op.get("copyData", {}))
        var = _next_var()
        return f'{var}=C("{source}",{parent_expr},{copy_data})'

    # ── R (REPLACE) ──────────────────────────────────────────────────────────
    if op_type == OP_REPLACE:
        path = op.get("path", "")
        path_expr = _resolve_parent(path) if path in _PARENT_BINDINGS else f'"{path}"'
        node_data = _format_node_data(op.get("node", {}))
        var = _next_var()
        return f'{var}=R({path_expr},{node_data})'

    # ── D (DELETE) ───────────────────────────────────────────────────────────
    if op_type == OP_DELETE:
        node_id = op.get("nodeId", "")
        id_expr = _resolve_parent(node_id) if node_id in _PARENT_BINDINGS else f'"{node_id}"'
        return f'D({id_expr})'

    # ── G (IMAGE) ────────────────────────────────────────────────────────────
    if op_type == OP_IMAGE:
        node_id = op.get("nodeId", "")
        id_expr = _resolve_parent(node_id) if node_id in _PARENT_BINDINGS else f'"{node_id}"'
        img_type = op.get("imageType", "stock")
        prompt = op.get("prompt", "")
        return f'G({id_expr},"{img_type}","{prompt}")'

    # ── M (MOVE) ─────────────────────────────────────────────────────────────
    if op_type == OP_MOVE:
        node_id = op.get("nodeId", "")
        id_expr = _resolve_parent(node_id) if node_id in _PARENT_BINDINGS else f'"{node_id}"'
        parent_key = op.get("parent")
        if parent_key:
            parent_expr = _resolve_parent(parent_key)
            index = op.get("index")
            if index is not None:
                return f'M({id_expr},{parent_expr},{index})'
            return f'M({id_expr},{parent_expr})'
        return f'M({id_expr},undefined)'

    logger.warning("알 수 없는 operation type: %s — 스킵", op_type)
    return None


def compile_slide(slide: dict[str, Any]) -> list[str]:
    """
    슬라이드 하나의 operations 배열을 DSL 문자열 목록으로 변환한다.

    Args:
        slide: layout plan의 슬라이드 dict

    Returns:
        DSL 코드 문자열 목록
    """
    slide_id = slide.get("slide_id", "slide_unknown")
    ops: list[str] = []
    for raw_op in slide.get("operations", []):
        compiled = compile_op(raw_op, slide_id)
        if compiled is not None:
            ops.append(compiled)
    return ops


def compile_layout_plan(layout_plan_path: str) -> list[str]:
    """
    layout plan JSON 파일을 로드하여 operations 문자열 목록으로 변환한다.

    Args:
        layout_plan_path: layout plan JSON 파일 경로

    Returns:
        모든 슬라이드의 DSL 코드 문자열 전체 목록
    """
    _reset_state()

    path = Path(layout_plan_path)
    if not path.exists():
        raise FileNotFoundError(f"Layout plan 파일이 없습니다: {layout_plan_path}")

    with path.open(encoding="utf-8") as f:
        plan: dict[str, Any] = json.load(f)

    all_ops: list[str] = []
    for slide in plan.get("slides", []):
        slide_ops = compile_slide(slide)
        all_ops.extend(slide_ops)

    logger.info(
        "compile_layout_plan 완료: plan_id=%s, 총 %d operations",
        plan.get("plan_id", "unknown"),
        len(all_ops),
    )
    return all_ops

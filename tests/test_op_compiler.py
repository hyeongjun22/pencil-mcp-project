"""
test_op_compiler.py — op_compiler 단위 테스트

소유자: 최지웅 (REQ-ORCH-002)
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.tools.op_compiler import (
    compile_layout_plan,
    compile_op,
    compile_slide,
    _reset_state,
)


@pytest.fixture(autouse=True)
def reset_state():
    """각 테스트 전 컴파일러 상태를 초기화한다."""
    _reset_state()
    yield
    _reset_state()


# ── compile_op 단위 테스트 ────────────────────────────────────────────────────

class TestCompileOp:
    def test_insert_basic(self):
        op = {
            "type": "I",
            "parent": "document",
            "node": {"type": "frame", "name": "Slide 1", "width": 1280, "height": 720},
        }
        result = compile_op(op, "slide_01")
        assert result is not None
        assert result.startswith("var0=I(document,")
        assert 'type:"frame"' in result
        assert 'name:"Slide 1"' in result

    def test_update_basic(self):
        op = {
            "type": "U",
            "path": "node_abc",
            "updateData": {"content": "Hello World"},
        }
        result = compile_op(op, "slide_01")
        assert result is not None
        assert 'U("node_abc",' in result
        assert 'content:"Hello World"' in result

    def test_delete_basic(self):
        op = {"type": "D", "nodeId": "some_node"}
        result = compile_op(op, "slide_01")
        assert result == 'D("some_node")'

    def test_image_op(self):
        op = {
            "type": "G",
            "nodeId": "img_frame",
            "imageType": "stock",
            "prompt": "modern office",
        }
        result = compile_op(op, "slide_01")
        assert result is not None
        assert 'G("img_frame","stock","modern office")' == result

    def test_unknown_type_returns_none(self):
        op = {"type": "Z", "data": "something"}
        result = compile_op(op, "slide_01")
        assert result is None

    def test_insert_registers_binding(self):
        """INSERT된 노드 name이 다음 op에서 parent로 사용될 수 있어야 한다."""
        _reset_state()
        op1 = {
            "type": "I",
            "parent": "document",
            "node": {"type": "frame", "name": "slide_01"},
        }
        op2 = {
            "type": "I",
            "parent": "slide_01",
            "node": {"type": "text", "content": "Hello"},
        }
        compile_op(op1, "slide_01")
        result2 = compile_op(op2, "slide_01")
        assert result2 is not None
        # parent가 var 이름으로 대체되어야 함
        assert "var0" in result2


# ── compile_slide 테스트 ──────────────────────────────────────────────────────

class TestCompileSlide:
    def test_empty_slide(self):
        slide = {"slide_id": "s1", "operations": []}
        result = compile_slide(slide)
        assert result == []

    def test_slide_with_ops(self):
        slide = {
            "slide_id": "s1",
            "operations": [
                {
                    "type": "I",
                    "parent": "document",
                    "node": {"type": "frame", "width": 100},
                },
                {
                    "type": "I",
                    "parent": "document",
                    "node": {"type": "text", "content": "Hi"},
                },
            ],
        }
        result = compile_slide(slide)
        assert len(result) == 2
        assert all(r is not None for r in result)


# ── compile_layout_plan 통합 테스트 ──────────────────────────────────────────

class TestCompileLayoutPlan:
    def _make_plan_file(self, plan: dict) -> str:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(plan, tmp)
        tmp.close()
        return tmp.name

    def test_basic_plan(self):
        plan = {
            "plan_id": "test_001",
            "slides": [
                {
                    "slide_id": "slide_01",
                    "operations": [
                        {
                            "type": "I",
                            "parent": "document",
                            "node": {"type": "frame", "name": "Slide 1", "width": 1280},
                        }
                    ],
                },
                {
                    "slide_id": "slide_02",
                    "operations": [
                        {
                            "type": "I",
                            "parent": "document",
                            "node": {"type": "frame", "name": "Slide 2", "width": 1280},
                        },
                        {
                            "type": "I",
                            "parent": "Slide 2",
                            "node": {"type": "text", "content": "Body"},
                        },
                    ],
                },
            ],
        }
        path = self._make_plan_file(plan)
        result = compile_layout_plan(path)
        assert len(result) == 3  # 슬라이드1:1 + 슬라이드2:2

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            compile_layout_plan("/nonexistent/path/plan.json")

    def test_empty_slides(self):
        plan = {"plan_id": "empty", "slides": []}
        path = self._make_plan_file(plan)
        result = compile_layout_plan(path)
        assert result == []

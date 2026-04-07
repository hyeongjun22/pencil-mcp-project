"""
test_chunk_scheduler.py — chunk_scheduler 단위 테스트

소유자: 최지웅 (REQ-ORCH-002)
"""
from __future__ import annotations

import pytest

from app.tools.chunk_scheduler import schedule_chunks, schedule_chunks_from_slides


class TestScheduleChunks:
    def test_empty_operations(self):
        result = schedule_chunks([], max_chunk_size=25)
        assert result == []

    def test_single_chunk(self):
        ops = [f"op{i}" for i in range(10)]
        result = schedule_chunks(ops, max_chunk_size=25)
        assert len(result) == 1
        assert result[0] == ops

    def test_exact_chunk_boundary(self):
        """딱 max_chunk_size개 — 청크 1개여야 한다."""
        ops = [f"op{i}" for i in range(25)]
        result = schedule_chunks(ops, max_chunk_size=25)
        assert len(result) == 1

    def test_overflow_creates_new_chunk(self):
        """26개 — 청크 2개(25+1)여야 한다."""
        ops = [f"op{i}" for i in range(26)]
        result = schedule_chunks(ops, max_chunk_size=25)
        assert len(result) == 2
        assert len(result[0]) == 25
        assert len(result[1]) == 1

    def test_multiple_chunks(self):
        ops = [f"op{i}" for i in range(70)]
        result = schedule_chunks(ops, max_chunk_size=25)
        assert len(result) == 3
        assert len(result[0]) == 25
        assert len(result[1]) == 25
        assert len(result[2]) == 20

    def test_total_ops_preserved(self):
        """모든 op이 청크에 보존되어야 한다."""
        ops = [f"op{i}" for i in range(100)]
        chunks = schedule_chunks(ops, max_chunk_size=25)
        flat = [op for chunk in chunks for op in chunk]
        assert flat == ops

    def test_slide_boundary_splits(self):
        """슬라이드 경계에서 청크가 분할되어야 한다."""
        # 10개 op → 경계 10 → 10개 op : 각각 하나의 청크
        ops = [f"op{i}" for i in range(20)]
        result = schedule_chunks(ops, max_chunk_size=25, slide_boundaries=[10])
        assert len(result) == 2
        assert len(result[0]) == 10
        assert len(result[1]) == 10

    def test_slide_boundary_at_zero_ignored(self):
        """경계가 0이면 이미 시작이므로 분할 없어야 한다."""
        ops = [f"op{i}" for i in range(5)]
        result = schedule_chunks(ops, max_chunk_size=25, slide_boundaries=[0])
        assert len(result) == 1

    def test_invalid_max_chunk_size(self):
        with pytest.raises(ValueError):
            schedule_chunks(["op"], max_chunk_size=0)

    def test_max_chunk_size_one(self):
        ops = ["a", "b", "c"]
        result = schedule_chunks(ops, max_chunk_size=1)
        assert len(result) == 3
        assert all(len(c) == 1 for c in result)


class TestScheduleChunksFromSlides:
    def test_two_slides(self):
        slide1_ops = [f"s1_op{i}" for i in range(5)]
        slide2_ops = [f"s2_op{i}" for i in range(5)]
        result = schedule_chunks_from_slides([slide1_ops, slide2_ops], max_chunk_size=25)
        # 슬라이드 경계에서 분할되므로 총 2개 청크여야 함
        assert len(result) == 2

    def test_slide_boundary_enforced(self):
        """두 슬라이드 각각 15개 op, max=25 → 경계(15)에서 분할 → 2 청크"""
        slide1_ops = [f"s1_op{i}" for i in range(15)]
        slide2_ops = [f"s2_op{i}" for i in range(15)]
        result = schedule_chunks_from_slides([slide1_ops, slide2_ops], max_chunk_size=25)
        assert len(result) == 2

    def test_empty_slides(self):
        result = schedule_chunks_from_slides([], max_chunk_size=25)
        assert result == []

    def test_single_slide(self):
        slide_ops = [f"op{i}" for i in range(30)]
        result = schedule_chunks_from_slides([slide_ops], max_chunk_size=25)
        assert len(result) == 2
        assert len(result[0]) == 25
        assert len(result[1]) == 5

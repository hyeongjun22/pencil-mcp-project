"""
test_pencil_proxy_executor.py — pencil_proxy_executor 단위 테스트

소유자: 최지웅 (REQ-ORCH-002)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.pencil_client import PencilConnectionError
from app.models.render_ops_schema import RenderOpResult
from app.tools.pencil_proxy_executor import execute_chunks, _execute_single_chunk


def _make_mock_client(responses: list) -> MagicMock:
    """batch_design 응답 시퀀스를 가진 mock PencilClient를 만든다."""
    client = MagicMock()
    client.batch_design = AsyncMock(side_effect=responses)
    return client


# ── execute_chunks 테스트 ─────────────────────────────────────────────────────

class TestExecuteChunks:
    @pytest.mark.asyncio
    async def test_all_success(self):
        chunks = [["op0", "op1"], ["op2", "op3"]]
        client = _make_mock_client([
            {"bindings": {"var0": "node-a"}},
            {"bindings": {"var1": "node-b"}},
        ])
        results = await execute_chunks(chunks, "test.pen", client, max_retries=0)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].bindings == {"var0": "node-a"}

    @pytest.mark.asyncio
    async def test_empty_chunks(self):
        client = _make_mock_client([])
        results = await execute_chunks([], "test.pen", client, max_retries=0)
        assert results == []

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        """청크 1 성공, 청크 2 실패 — 청크 3은 그래도 실행되어야 한다."""
        chunks = [["op0"], ["op1"], ["op2"]]
        client = _make_mock_client([
            {"bindings": {}},
            PencilConnectionError("Pencil 오류"),
            {"bindings": {}},
        ])
        results = await execute_chunks(chunks, "test.pen", client, max_retries=0)
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True

    @pytest.mark.asyncio
    async def test_chunk_index_assigned_correctly(self):
        chunks = [["a"], ["b"], ["c"]]
        client = _make_mock_client([{}, {}, {}])
        results = await execute_chunks(chunks, "test.pen", client, max_retries=0)
        for i, r in enumerate(results):
            assert r.chunk_index == i


# ── _execute_single_chunk 재시도 테스트 ──────────────────────────────────────

class TestExecuteSingleChunk:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        client = _make_mock_client([{"bindings": {"x": "1"}}])
        result = await _execute_single_chunk(
            chunk_index=0,
            operations="op0",
            file_path="test.pen",
            pencil_client=client,
            max_retries=2,
        )
        assert result.success is True
        assert result.chunk_index == 0

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """1회 실패 후 성공 — max_retries=2이므로 성공해야 한다."""
        client = _make_mock_client([
            PencilConnectionError("일시 오류"),
            {"bindings": {"y": "2"}},
        ])
        result = await _execute_single_chunk(
            chunk_index=1,
            operations="op1",
            file_path="test.pen",
            pencil_client=client,
            max_retries=2,
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_all_retries_fail(self):
        """max_retries=2 설정에서 3번 모두 실패 — success=False."""
        client = _make_mock_client([
            PencilConnectionError("err"),
            PencilConnectionError("err"),
            PencilConnectionError("err"),
        ])
        result = await _execute_single_chunk(
            chunk_index=2,
            operations="op2",
            file_path="test.pen",
            pencil_client=client,
            max_retries=2,
        )
        assert result.success is False
        assert result.error is not None
        assert result.chunk_index == 2

    @pytest.mark.asyncio
    async def test_no_retries(self):
        """max_retries=0 — 한 번만 시도."""
        client = _make_mock_client([PencilConnectionError("즉시 실패")])
        result = await _execute_single_chunk(
            chunk_index=0,
            operations="op",
            file_path="test.pen",
            pencil_client=client,
            max_retries=0,
        )
        assert result.success is False
        assert client.batch_design.call_count == 1

    @pytest.mark.asyncio
    async def test_empty_bindings_recorded(self):
        """성공이지만 bindings가 없는 경우 — 성공으로 기록."""
        client = _make_mock_client([{}])  # 빈 dict
        result = await _execute_single_chunk(
            chunk_index=0,
            operations="op",
            file_path="test.pen",
            pencil_client=client,
            max_retries=0,
        )
        assert result.success is True
        assert result.bindings == {}

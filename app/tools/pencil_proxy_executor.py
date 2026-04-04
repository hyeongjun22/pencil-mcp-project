"""
pencil_proxy_executor.py — 청크를 Pencil MCP에 순차 전송

소유자: 최지웅 (REQ-ORCH-002)

청크 목록을 순서대로 PencilClient.batch_design()으로 전송하고,
실패 시 최대 max_retries 회 재시도 후 결과를 수집한다.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Sequence

from app.adapters.pencil_client import PencilClient, PencilConnectionError
from app.config import settings
from app.models.render_ops_schema import RenderOpResult

logger = logging.getLogger(__name__)


async def execute_chunks(
    chunks: list[list[str]],
    file_path: str,
    pencil_client: PencilClient,
    max_retries: int | None = None,
) -> list[RenderOpResult]:
    """
    청크 목록을 순서대로 Pencil MCP에 전송하고 결과를 수집한다.

    실패한 청크는 최대 max_retries회 재시도한다.
    최종 실패한 청크도 success=False로 기록하고 다음 청크로 진행한다.

    Args:
        chunks:         청크 목록 (각 청크는 operations 문자열 목록)
        file_path:      대상 .pen 파일 절대 경로
        pencil_client:  연결된 PencilClient 인스턴스
        max_retries:    실패 시 최대 재시도 횟수 (기본: settings.max_retries)

    Returns:
        각 청크의 RenderOpResult 목록
    """
    _max_retries = max_retries if max_retries is not None else settings.max_retries
    results: list[RenderOpResult] = []

    for chunk_index, chunk_ops in enumerate(chunks):
        operations_str = "\n".join(chunk_ops)
        result = await _execute_single_chunk(
            chunk_index=chunk_index,
            operations=operations_str,
            file_path=file_path,
            pencil_client=pencil_client,
            max_retries=_max_retries,
        )
        results.append(result)

    success_count = sum(1 for r in results if r.success)
    logger.info(
        "execute_chunks 완료: %d/%d 청크 성공",
        success_count,
        len(results),
    )
    return results


async def _execute_single_chunk(
    chunk_index: int,
    operations: str,
    file_path: str,
    pencil_client: PencilClient,
    max_retries: int,
) -> RenderOpResult:
    """단일 청크를 실행하며 실패 시 재시도한다."""
    last_error: str | None = None

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info("청크 %d 재시도 (%d/%d)...", chunk_index, attempt, max_retries)
                await asyncio.sleep(0.5 * attempt)  # 지수 백오프(단순)

            raw = await pencil_client.batch_design(operations, file_path)

            # 응답에서 바인딩 추출
            bindings: dict = {}
            if isinstance(raw, dict):
                bindings = raw.get("bindings", raw)

            logger.info("청크 %d 성공 (attempt=%d)", chunk_index, attempt)
            return RenderOpResult(
                success=True,
                chunk_index=chunk_index,
                bindings=bindings,
                error=None,
            )

        except (PencilConnectionError, Exception) as exc:
            last_error = str(exc)
            logger.warning(
                "청크 %d 실패 (attempt=%d): %s",
                chunk_index,
                attempt,
                last_error,
            )

    # 최종 실패
    logger.error("청크 %d 최종 실패 (max_retries=%d): %s", chunk_index, max_retries, last_error)
    return RenderOpResult(
        success=False,
        chunk_index=chunk_index,
        bindings={},
        error=last_error,
    )

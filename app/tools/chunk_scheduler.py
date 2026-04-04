"""
chunk_scheduler.py — operations 목록을 청크 단위로 분할

소유자: 최지웅 (REQ-ORCH-002)

규칙:
- 한 청크 = 최대 max_chunk_size operations (기본 25)
- 슬라이드 경계를 우선 분할 지점으로 사용 (slide_boundaries 옵션)
- 한 슬라이드가 max_chunk_size 초과 시 슬라이드 내에서 연속 분할
"""
from __future__ import annotations

import logging
from typing import Sequence

from app.constants import DEFAULT_MAX_CHUNK_SIZE

logger = logging.getLogger(__name__)


def schedule_chunks(
    operations: list[str],
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    slide_boundaries: list[int] | None = None,
) -> list[list[str]]:
    """
    operations 목록을 max_chunk_size 단위로 분할한 청크 목록을 반환한다.

    Args:
        operations:       Pencil DSL 코드 문자열 목록
        max_chunk_size:   한 청크당 최대 operation 수 (기본 25)
        slide_boundaries: 슬라이드 경계 인덱스 목록 (해당 인덱스에서 우선 분할)
                          None이면 단순 max_chunk_size 기준 분할

    Returns:
        청크 목록 (각 청크는 operations 문자열 목록)
    """
    if not operations:
        return []

    if max_chunk_size < 1:
        raise ValueError(f"max_chunk_size는 1 이상이어야 합니다: {max_chunk_size}")

    boundary_set: set[int] = set(slide_boundaries or [])
    chunks: list[list[str]] = []
    current_chunk: list[str] = []

    for i, op in enumerate(operations):
        # 슬라이드 경계 AND 현재 청크가 차있으면 분할
        if i in boundary_set and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []

        current_chunk.append(op)

        # 최대 사이즈 초과 시 분할
        if len(current_chunk) >= max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = []

    # 남은 청크 저장
    if current_chunk:
        chunks.append(current_chunk)

    logger.info(
        "schedule_chunks 완료: %d operations → %d chunks (max_size=%d)",
        len(operations),
        len(chunks),
        max_chunk_size,
    )
    return chunks


def schedule_chunks_from_slides(
    slide_ops: list[list[str]],
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
) -> list[list[str]]:
    """
    슬라이드별 operations 목록을 받아 슬라이드 경계를 자동으로 설정하여 분할한다.

    Args:
        slide_ops:      슬라이드별 operations 목록 (list of list)
        max_chunk_size: 한 청크당 최대 operation 수

    Returns:
        청크 목록
    """
    # 슬라이드 경계 계산
    boundaries: list[int] = []
    cumulative = 0
    for ops in slide_ops[:-1]:  # 마지막 슬라이드 이후는 경계 불필요
        cumulative += len(ops)
        boundaries.append(cumulative)

    flat_ops = [op for ops in slide_ops for op in ops]
    return schedule_chunks(flat_ops, max_chunk_size=max_chunk_size, slide_boundaries=boundaries)

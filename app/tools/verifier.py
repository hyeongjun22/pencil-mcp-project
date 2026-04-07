"""
verifier.py — 렌더 실행 결과 검증

소유자: 최지웅 (REQ-ORCH-002)

검증 항목:
- 전체 청크 수 vs. 실행된 청크 수 일치 여부
- 실패 청크 목록 및 실패율 (>20% → status=failed)
- 바인딩 비어있는 성공 청크 경고
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from app.constants import FAILURE_RATE_THRESHOLD, STATUS_DONE, STATUS_FAILED
from app.models.render_ops_schema import RenderOpResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationReport:
    """렌더 실행 결과 검증 보고서."""

    total_chunks: int
    executed_chunks: int
    success_count: int
    failure_count: int
    failed_indices: list[int] = field(default_factory=list)
    empty_binding_warnings: list[int] = field(default_factory=list)
    failure_rate: float = 0.0
    status: Literal["done", "failed"] = STATUS_DONE
    summary: str = ""


def verify_results(
    results: list[RenderOpResult],
    expected_chunks: int,
) -> VerificationReport:
    """
    실행 결과 목록을 검증하고 VerificationReport를 반환한다.

    Args:
        results:         각 청크의 RenderOpResult 목록
        expected_chunks: 예상 총 청크 수

    Returns:
        검증 보고서
    """
    executed = len(results)
    success_count = sum(1 for r in results if r.success)
    failure_count = executed - success_count

    failed_indices = [r.chunk_index for r in results if not r.success]
    empty_binding_warnings = [
        r.chunk_index for r in results if r.success and not r.bindings
    ]

    failure_rate = failure_count / executed if executed > 0 else 0.0
    status: Literal["done", "failed"] = (
        STATUS_FAILED if failure_rate > FAILURE_RATE_THRESHOLD else STATUS_DONE
    )

    if executed != expected_chunks:
        logger.warning(
            "청크 수 불일치: 예상=%d, 실행=%d",
            expected_chunks,
            executed,
        )

    for idx in empty_binding_warnings:
        logger.warning("청크 %d: 성공했지만 바인딩이 비어있습니다", idx)

    summary_parts = [
        f"실행={executed}/{expected_chunks}",
        f"성공={success_count}",
        f"실패={failure_count}",
        f"실패율={failure_rate:.1%}",
        f"상태={status}",
    ]
    if failed_indices:
        summary_parts.append(f"실패청크={failed_indices}")

    summary = " | ".join(summary_parts)
    logger.info("verify_results: %s", summary)

    return VerificationReport(
        total_chunks=expected_chunks,
        executed_chunks=executed,
        success_count=success_count,
        failure_count=failure_count,
        failed_indices=failed_indices,
        empty_binding_warnings=empty_binding_warnings,
        failure_rate=failure_rate,
        status=status,
        summary=summary,
    )

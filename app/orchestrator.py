"""
orchestrator.py — 전체 파이프라인 스테이지 연결

소유자: 최지웅 (REQ-ORCH-002)

Stage 1: 이수민(ANL) 분석 아티팩트 확인
Stage 2: 임형준(VIS) layout plan 아티팩트 확인
Stage 3: render pipeline 실행
Stage 4: 결과 저장 및 보고
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import settings
from app.services.render_service import run_render_pipeline

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """파이프라인 실행 오류."""


async def run_pipeline(
    plan_id: str,
    pen_file_path: str | None = None,
) -> dict:
    """
    분석 → 레이아웃 → 렌더 파이프라인 전체를 순서대로 실행한다.

    Args:
        plan_id:       레이아웃 플랜 ID (파일명 기반)
        pen_file_path: 대상 .pen 파일 경로 (None이면 data/output/{plan_id}.pen 추정)

    Returns:
        실행 결과 요약 dict
    """
    logger.info("=== 파이프라인 시작: plan_id=%s ===", plan_id)

    # ── Stage 1: 분석 아티팩트 확인 (이수민 산출물 읽기) ─────────────────────
    analysis_path = settings.data_analysis_dir / f"{plan_id}.json"
    analysis_data = _load_artifact_if_exists(analysis_path, stage="Analysis")

    # ── Stage 2: layout plan 아티팩트 확인 (임형준 산출물 읽기) ──────────────
    layout_plan_path = settings.data_layout_plans_dir / f"{plan_id}.json"
    if not layout_plan_path.exists():
        raise PipelineError(
            f"Layout plan 아티팩트가 없습니다: {layout_plan_path}\n"
            "임형준(VIS)의 REQ-VIS 단계가 완료되었는지 확인하세요."
        )
    logger.info("Stage 2 — Layout plan 확인: %s", layout_plan_path)

    # ── Stage 3: render pipeline 실행 ────────────────────────────────────────
    _pen_file = pen_file_path or str(
        (settings.data_output_dir / f"{plan_id}.pen").resolve()
    )
    logger.info("Stage 3 — Render pipeline 실행 (pen_file=%s)", _pen_file)

    artifact = await run_render_pipeline(
        layout_plan_path=str(layout_plan_path),
        pen_file_path=_pen_file,
        plan_id=plan_id,
    )

    # ── Stage 4: 결과 보고 ───────────────────────────────────────────────────
    success_count = sum(1 for r in artifact.results if r.success)
    total_chunks = len(artifact.chunks)
    result_summary = {
        "plan_id": plan_id,
        "status": artifact.status,
        "total_chunks": total_chunks,
        "success_chunks": success_count,
        "failure_chunks": total_chunks - success_count,
        "output_file": str(settings.data_output_dir / f"{plan_id}.json"),
        "render_ops_file": str(settings.data_render_ops_dir / f"{plan_id}_ops.json"),
        "analysis_used": analysis_data is not None,
    }

    logger.info("=== 파이프라인 완료: %s ===", result_summary)
    return result_summary


def _load_artifact_if_exists(path: Path, stage: str) -> dict | None:
    """아티팩트 파일이 존재하면 로드하고 없으면 경고 후 None 반환."""
    if path.exists():
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Stage %s 아티팩트 로드: %s", stage, path)
            return data
        except Exception as exc:
            logger.warning("Stage %s 아티팩트 로드 실패: %s — %s", stage, path, exc)
    else:
        logger.warning(
            "Stage %s 아티팩트 없음: %s — 이전 스테이지가 완료되지 않았을 수 있습니다.",
            stage,
            path,
        )
    return None

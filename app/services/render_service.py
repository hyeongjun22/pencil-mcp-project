"""
render_service.py — 렌더 파이프라인 단일 진입점

소유자: 최지웅 (REQ-ORCH-002)

op_compiler → chunk_scheduler → pencil_proxy_executor → verifier 를
조합하여 단일 async 함수로 제공한다.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.adapters.pencil_client import PencilClient
from app.config import settings
from app.models.render_ops_schema import BatchDesignInput, RenderOpResult, RenderOpsArtifact
from app.tools.chunk_scheduler import schedule_chunks
from app.tools.op_compiler import compile_layout_plan
from app.tools.pencil_proxy_executor import execute_chunks
from app.tools.verifier import verify_results

logger = logging.getLogger(__name__)


async def run_render_pipeline(
    layout_plan_path: str,
    pen_file_path: str,
    plan_id: str,
    pencil_client: PencilClient | None = None,
    max_chunk_size: int | None = None,
) -> RenderOpsArtifact:
    """
    레이아웃 플랜 → Pencil 캔버스 렌더링 전체 파이프라인.

    1. layout plan JSON 로드 & DSL 변환 (op_compiler)
    2. operations 청크 분할 (chunk_scheduler)
    3. 청크 순차 전송 (pencil_proxy_executor)
    4. 결과 검증 (verifier)
    5. 아티팩트 저장 (data/intermediate/render_ops/, data/output/)

    Args:
        layout_plan_path: 임형준 산출물 layout plan JSON 경로
        pen_file_path:    대상 .pen 파일 절대 경로
        plan_id:          플랜 고유 ID (파일 저장에 사용)
        pencil_client:    사용할 PencilClient (None이면 새로 생성)
        max_chunk_size:   청크 크기 (None이면 settings.max_chunk_size)

    Returns:
        RenderOpsArtifact (status, chunks, results 포함)
    """
    _max_chunk_size = max_chunk_size or settings.max_chunk_size
    artifact = RenderOpsArtifact(plan_id=plan_id, status="running")

    try:
        # ── Step 1: op_compiler ──────────────────────────────────────────────
        logger.info("[%s] Step 1: layout plan 컴파일 중...", plan_id)
        all_ops = compile_layout_plan(layout_plan_path)
        logger.info("[%s] 총 %d operations 컴파일 완료", plan_id, len(all_ops))

        # ── Step 2: chunk_scheduler ──────────────────────────────────────────
        logger.info("[%s] Step 2: 청크 분할 중 (max_size=%d)...", plan_id, _max_chunk_size)
        chunks = schedule_chunks(all_ops, max_chunk_size=_max_chunk_size)
        logger.info("[%s] %d개 청크로 분할", plan_id, len(chunks))

        # BatchDesignInput 목록 구성
        batch_inputs = [
            BatchDesignInput(
                operations="\n".join(chunk),
                file_path=pen_file_path,
                chunk_index=i,
                total_chunks=len(chunks),
            )
            for i, chunk in enumerate(chunks)
        ]
        artifact.chunks = batch_inputs

        # 중간 아티팩트 저장
        await _save_render_ops(plan_id, chunks)

        # ── Step 3: pencil_proxy_executor ────────────────────────────────────
        logger.info("[%s] Step 3: Pencil 청크 전송 시작...", plan_id)

        own_client = False
        if pencil_client is None:
            pencil_client = PencilClient()
            await pencil_client.connect()
            own_client = True

        try:
            results: list[RenderOpResult] = await execute_chunks(
                chunks=chunks,
                file_path=pen_file_path,
                pencil_client=pencil_client,
            )
        finally:
            if own_client:
                await pencil_client.disconnect()

        artifact.results = results

        # ── Step 4: verifier ─────────────────────────────────────────────────
        logger.info("[%s] Step 4: 결과 검증 중...", plan_id)
        report = verify_results(results, expected_chunks=len(chunks))
        artifact.status = report.status  # type: ignore[assignment]
        logger.info("[%s] 검증 완료: %s", plan_id, report.summary)

    except Exception as exc:
        logger.exception("[%s] render pipeline 실패: %s", plan_id, exc)
        artifact.status = "failed"

    # ── Step 5: 최종 결과 저장 ───────────────────────────────────────────────
    await _save_output(plan_id, artifact)

    return artifact


# ── 파일 저장 헬퍼 ────────────────────────────────────────────────────────────

async def _save_render_ops(plan_id: str, chunks: list[list[str]]) -> None:
    """청크 분할 결과를 data/intermediate/render_ops/{plan_id}_ops.json에 저장한다."""
    import aiofiles

    out_dir = settings.data_render_ops_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{plan_id}_ops.json"

    payload = {
        "plan_id": plan_id,
        "total_chunks": len(chunks),
        "chunks": [
            {"chunk_index": i, "operations": ops}
            for i, ops in enumerate(chunks)
        ],
    }

    async with aiofiles.open(out_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(payload, ensure_ascii=False, indent=2))

    logger.info("render_ops 아티팩트 저장: %s", out_path)


async def _save_output(plan_id: str, artifact: RenderOpsArtifact) -> None:
    """최종 아티팩트를 data/output/{plan_id}.json에 저장한다."""
    import aiofiles

    out_dir = settings.data_output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{plan_id}.json"

    async with aiofiles.open(out_path, "w", encoding="utf-8") as f:
        await f.write(artifact.model_dump_json(indent=2, exclude_none=False))

    logger.info("output 아티팩트 저장: %s", out_path)

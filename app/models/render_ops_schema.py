"""
render_ops_schema.py — RenderOps Pydantic 스키마 정의

소유자: 최지웅 (REQ-ORCH-001)
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BatchDesignInput(BaseModel):
    """Pencil batch_design 단일 청크 입력."""

    operations: str = Field(
        ...,
        description="실행할 Pencil 오퍼레이션 코드 문자열 (I/U/C/R/D/G 명령)",
    )
    file_path: str = Field(
        ...,
        description="대상 .pen 파일의 절대 경로",
    )
    chunk_index: int = Field(
        default=0,
        description="현재 청크 번호 (0-indexed)",
    )
    total_chunks: int = Field(
        default=1,
        description="전체 청크 수",
    )


class RenderOpResult(BaseModel):
    """단일 청크 실행 결과."""

    success: bool = Field(..., description="청크 실행 성공 여부")
    chunk_index: int = Field(..., description="청크 번호")
    bindings: dict = Field(default_factory=dict, description="생성된 노드 id 바인딩")
    error: str | None = Field(default=None, description="에러 메시지 (실패 시)")


class RenderOpsArtifact(BaseModel):
    """전체 렌더 파이프라인 실행 아티팩트."""

    plan_id: str = Field(..., description="레이아웃 플랜 ID")
    chunks: list[BatchDesignInput] = Field(
        default_factory=list,
        description="분할된 청크 목록",
    )
    results: list[RenderOpResult] = Field(
        default_factory=list,
        description="각 청크 실행 결과",
    )
    status: Literal["pending", "running", "done", "failed"] = Field(
        default="pending",
        description="전체 실행 상태",
    )

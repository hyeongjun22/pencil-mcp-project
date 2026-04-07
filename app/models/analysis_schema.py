# models/analysis_schema.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_ABSOLUTE_PATH_RE = re.compile(r"^([/\\]|[A-Za-z]:)")


class NodeType(str, Enum):
    module = "module"
    class_ = "class"
    function = "function"
    method = "method"


class EdgeType(str, Enum):
    imports = "imports"
    calls = "calls"
    contains = "contains"
    inherits = "inherits"
    depends_on = "depends_on"


class LayerType(str, Enum):
    presentation = "presentation"
    application = "application"
    domain = "domain"
    infrastructure = "infrastructure"
    unknown = "unknown"


class PositionHint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: Optional[float] = Field(default=None, ge=0, description="레이아웃 x 좌표 힌트 (0 이상)")
    y: Optional[float] = Field(default=None, ge=0, description="레이아웃 y 좌표 힌트 (0 이상)")
    width: Optional[float] = Field(default=None, gt=0, description="레이아웃 너비 힌트 (양수)")
    height: Optional[float] = Field(default=None, gt=0, description="레이아웃 높이 힌트 (양수)")


class NodeMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    file_path: str = Field(
        ...,
        min_length=1,
        description="소스 파일의 상대 경로 (repo root 기준). 절대 경로는 허용하지 않는다.",
    )
    start_line: int = Field(..., ge=1)
    end_line: int = Field(..., ge=1)
    docstring: Optional[str] = None
    layer: LayerType = LayerType.unknown
    position_hint: Optional[PositionHint] = None

    @field_validator("file_path")
    @classmethod
    def validate_relative_path(cls, v: str) -> str:
        if _ABSOLUTE_PATH_RE.match(v):
            raise ValueError(
                f"file_path must be a relative path (repo root 기준), got: {v!r}"
            )
        return v

    @model_validator(mode="after")
    def validate_line_range(self) -> "NodeMetadata":
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class ASTNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        min_length=1,
        pattern=r"^[\w][\w.]*$",
        description="점(dot) 구분 식별자. 예: 'app.services.analysis_service'. 영문자·숫자·밑줄·점만 허용.",
    )
    type: NodeType
    metadata: NodeMetadata


class ASTEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    type: EdgeType

    @model_validator(mode="after")
    def validate_no_self_loop(self) -> "ASTEdge":
        if self.source == self.target:
            raise ValueError("self-loop edge is not allowed")
        return self


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_files: int = Field(..., ge=0)
    total_nodes: int = Field(..., ge=0)
    total_edges: int = Field(..., ge=0)


class ASTAnalysisSchema(BaseModel):
    """
    Stage 1 (Analysis) → Stage 2 (Layout/Prompt) 핸드오프 계약 스키마.

    downstream(임형준)이 이 객체를 수신하면 즉시 layout plan 생성에 착수할 수 있어야 한다.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default="1.0",
        description="스키마 버전 (호환성 관리용)",
    )
    repo: str = Field(..., min_length=1, description="분석 대상 repo 식별자 (이름 또는 경로)")
    generated_at: datetime = Field(..., description="분석 생성 시각 (ISO 8601)")
    summary: AnalysisSummary
    nodes: List[ASTNode] = Field(default_factory=list)
    edges: List[ASTEdge] = Field(default_factory=list)

    # ── downstream 소비 필드 ──────────────────────────────────────────────────
    arch_summary: str = Field(
        default="",
        description=(
            "전체 아키텍처 요약 텍스트. Stage 2 프롬프트 빌더가 슬라이드 도입부/개요 생성에 사용한다."
        ),
    )
    entry_points: List[str] = Field(
        default_factory=list,
        description="주요 진입점 node id 목록 (예: main 함수, CLI entrypoint). Stage 2 레이아웃 강조 처리에 사용된다.",
    )
    top_level_modules: List[str] = Field(
        default_factory=list,
        description="최상위 모듈 상대 경로 목록 (repo root 기준). Stage 2 슬라이드 구조 결정에 사용된다.",
    )

    # ── validators ───────────────────────────────────────────────────────────

    @field_validator("nodes")
    @classmethod
    def validate_unique_node_ids(cls, nodes: List[ASTNode]) -> List[ASTNode]:
        ids = [node.id for node in nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("node ids must be unique")
        return nodes

    @model_validator(mode="after")
    def validate_consistency(self) -> "ASTAnalysisSchema":
        node_ids = {node.id for node in self.nodes}

        # 엣지 참조 무결성
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"edge source not found in nodes: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"edge target not found in nodes: {edge.target}")

        # 방향성 비순환 그래프(DAG) 특성 검증: contains, inherits 엣지에 사이클이 있는지 확인
        def has_cycle(target_edge_type: EdgeType) -> bool:
            adj = {nid: set() for nid in node_ids}
            for e in self.edges:
                if e.type == target_edge_type:
                    adj[e.source].add(e.target)

            visited = set()
            rec_stack = set()

            def dfs(v: str) -> bool:
                visited.add(v)
                rec_stack.add(v)
                for neighbor in adj[v]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
                rec_stack.remove(v)
                return False

            for nid in node_ids:
                if nid not in visited:
                    if dfs(nid):
                        return True
            return False

        if has_cycle(EdgeType.contains):
            raise ValueError(f"circular reference detected in {EdgeType.contains.value} edges")
        if has_cycle(EdgeType.inherits):
            raise ValueError(f"circular reference detected in {EdgeType.inherits.value} edges")

        # summary count 일관성
        if self.summary.total_nodes != len(self.nodes):
            raise ValueError(
                f"summary.total_nodes ({self.summary.total_nodes}) "
                f"does not match actual node count ({len(self.nodes)})"
            )
        if self.summary.total_edges != len(self.edges):
            raise ValueError(
                f"summary.total_edges ({self.summary.total_edges}) "
                f"does not match actual edge count ({len(self.edges)})"
            )

        return self
"""
tests/test_ast_parser.py

ASTAnalysisSchema 유효성 검증 테스트.

REQ: REQ-AST-JSON-001, REQ-AST-JSON-002
Owner: 이수민 (Analysis Owner)
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.analysis_schema import (
    ASTAnalysisSchema,
    ASTEdge,
    ASTNode,
    AnalysisSummary,
    EdgeType,
    LayerType,
    NodeMetadata,
    NodeType,
    PositionHint,
)


# ── 공통 픽스처 ──────────────────────────────────────────────────────────────


def _node(node_id: str, file_path: str = "app/foo.py") -> ASTNode:
    return ASTNode(
        id=node_id,
        type=NodeType.module,
        metadata=NodeMetadata(
            name=node_id,
            file_path=file_path,
            start_line=1,
            end_line=10,
            layer=LayerType.application,
        ),
    )


def _edge(source: str, target: str) -> ASTEdge:
    return ASTEdge(source=source, target=target, type=EdgeType.imports)


def _summary(total_files: int = 1, total_nodes: int = 0, total_edges: int = 0) -> AnalysisSummary:
    return AnalysisSummary(
        total_files=total_files,
        total_nodes=total_nodes,
        total_edges=total_edges,
    )


def _valid_schema(**overrides) -> dict:
    node_a = _node("mod.a")
    node_b = _node("mod.b")
    base = dict(
        repo="test-repo",
        generated_at=datetime(2026, 4, 4, 22, 0, 0),
        summary=_summary(total_files=2, total_nodes=2, total_edges=1),
        nodes=[node_a, node_b],
        edges=[_edge("mod.a", "mod.b")],
        arch_summary="두 모듈 구조",
        entry_points=["mod.a"],
        top_level_modules=["app/a.py", "app/b.py"],
    )
    base.update(overrides)
    return base


# ── 정상 케이스 ──────────────────────────────────────────────────────────────


class TestValidSchema:
    def test_valid_payload_passes(self):
        """정상 payload가 ValidationError 없이 생성되어야 한다."""
        schema = ASTAnalysisSchema(**_valid_schema())
        assert schema.repo == "test-repo"
        assert schema.schema_version == "1.0"
        assert len(schema.nodes) == 2
        assert len(schema.edges) == 1

    def test_schema_version_default(self):
        """schema_version 미입력 시 기본값 '1.0' 이 적용된다."""
        schema = ASTAnalysisSchema(**_valid_schema())
        assert schema.schema_version == "1.0"

    def test_arch_summary_default_empty_string(self):
        """arch_summary 미입력 시 빈 문자열이 기본값이다."""
        data = _valid_schema()
        data.pop("arch_summary", None)
        schema = ASTAnalysisSchema(**data)
        assert schema.arch_summary == ""

    def test_entry_points_default_empty_list(self):
        """entry_points 미입력 시 빈 리스트가 기본값이다."""
        data = _valid_schema()
        data.pop("entry_points", None)
        schema = ASTAnalysisSchema(**data)
        assert schema.entry_points == []

    def test_empty_nodes_and_edges(self):
        """nodes/edges가 모두 비어 있어도 summary count가 일치하면 통과한다."""
        schema = ASTAnalysisSchema(
            repo="empty-repo",
            generated_at=datetime(2026, 4, 4, 0, 0, 0),
            summary=_summary(total_files=0, total_nodes=0, total_edges=0),
        )
        assert schema.nodes == []
        assert schema.edges == []


# ── NodeMetadata 유효성 ───────────────────────────────────────────────────────


class TestNodeMetadataValidation:
    def test_end_line_less_than_start_line_raises(self):
        """end_line < start_line 이면 ValidationError 가 발생해야 한다."""
        with pytest.raises(ValidationError, match="end_line must be greater than or equal to start_line"):
            NodeMetadata(
                name="bad_node",
                file_path="app/foo.py",
                start_line=10,
                end_line=5,
            )

    def test_start_line_equals_end_line_passes(self):
        """start_line == end_line 은 허용된다."""
        meta = NodeMetadata(name="x", file_path="app/x.py", start_line=3, end_line=3)
        assert meta.start_line == meta.end_line


# ── ASTEdge 유효성 ────────────────────────────────────────────────────────────


class TestASTEdgeValidation:
    def test_self_loop_raises(self):
        """source == target (셀프루프) 이면 ValidationError 가 발생해야 한다."""
        with pytest.raises(ValidationError, match="self-loop edge is not allowed"):
            _edge("mod.a", "mod.a")


# ── ASTAnalysisSchema 참조 무결성 ────────────────────────────────────────────


class TestEdgeReferenceIntegrity:
    def test_edge_source_not_in_nodes_raises(self):
        """존재하지 않는 source node 를 참조하는 edge 는 ValidationError 가 발생해야 한다."""
        data = _valid_schema()
        data["edges"] = [_edge("non_existent", "mod.b")]
        data["summary"] = _summary(total_files=2, total_nodes=2, total_edges=1)
        with pytest.raises(ValidationError, match="edge source not found in nodes"):
            ASTAnalysisSchema(**data)

    def test_edge_target_not_in_nodes_raises(self):
        """존재하지 않는 target node 를 참조하는 edge 는 ValidationError 가 발생해야 한다."""
        data = _valid_schema()
        data["edges"] = [_edge("mod.a", "non_existent")]
        data["summary"] = _summary(total_files=2, total_nodes=2, total_edges=1)
        with pytest.raises(ValidationError, match="edge target not found in nodes"):
            ASTAnalysisSchema(**data)


# ── Summary Count 일관성 ─────────────────────────────────────────────────────


class TestSummaryCountConsistency:
    def test_total_nodes_mismatch_raises(self):
        """summary.total_nodes 가 실제 nodes 수와 다르면 ValidationError 가 발생해야 한다."""
        data = _valid_schema()
        data["summary"] = _summary(total_files=2, total_nodes=99, total_edges=1)
        with pytest.raises(ValidationError, match="total_nodes"):
            ASTAnalysisSchema(**data)

    def test_total_edges_mismatch_raises(self):
        """summary.total_edges 가 실제 edges 수와 다르면 ValidationError 가 발생해야 한다."""
        data = _valid_schema()
        data["summary"] = _summary(total_files=2, total_nodes=2, total_edges=99)
        with pytest.raises(ValidationError, match="total_edges"):
            ASTAnalysisSchema(**data)


# ── Node ID 고유성 ────────────────────────────────────────────────────────────


class TestUniqueNodeIds:
    def test_duplicate_node_ids_raises(self):
        """동일한 id 를 가진 node 가 두 개 이상 존재하면 ValidationError 가 발생해야 한다."""
        data = _valid_schema()
        data["nodes"] = [_node("mod.a"), _node("mod.a")]  # 중복
        data["edges"] = []
        data["summary"] = _summary(total_files=1, total_nodes=2, total_edges=0)
        with pytest.raises(ValidationError, match="node ids must be unique"):
            ASTAnalysisSchema(**data)


# ══════════════════════════════════════════════════════════════════════════════
# REQ-AST-JSON-002 — 필수 필드 제약 조건
# ══════════════════════════════════════════════════════════════════════════════


class TestPositionHintConstraints:
    """PositionHint 좌표 제약 (REQ-AST-JSON-002)."""

    def test_negative_x_raises(self):
        """x 좌표가 음수이면 ValidationError."""
        with pytest.raises(ValidationError):
            PositionHint(x=-1.0, y=0.0)

    def test_negative_y_raises(self):
        """y 좌표가 음수이면 ValidationError."""
        with pytest.raises(ValidationError):
            PositionHint(x=0.0, y=-5.0)

    def test_zero_coordinates_passes(self):
        """x=0, y=0 은 허용된다."""
        hint = PositionHint(x=0.0, y=0.0, width=10.0, height=10.0)
        assert hint.x == 0.0
        assert hint.y == 0.0

    def test_positive_coordinates_passes(self):
        """양수 좌표는 정상 통과."""
        hint = PositionHint(x=100.0, y=200.0, width=50.0, height=30.0)
        assert hint.x == 100.0


class TestNodeIdPattern:
    """ASTNode.id 형식 제약 (REQ-AST-JSON-002)."""

    def test_valid_dot_separated_id(self):
        """점(dot) 구분 식별자는 통과."""
        node = _node("app.services.analysis_service")
        assert node.id == "app.services.analysis_service"

    def test_underscore_id_passes(self):
        """밑줄 포함 식별자는 통과."""
        node = _node("my_module")
        assert node.id == "my_module"

    def test_space_in_id_raises(self):
        """공백이 포함된 id 는 ValidationError."""
        with pytest.raises(ValidationError):
            _node("app foo")

    def test_special_chars_in_id_raises(self):
        """특수문자(@, -, /)가 포함된 id 는 ValidationError."""
        with pytest.raises(ValidationError):
            _node("app/foo")
        with pytest.raises(ValidationError):
            _node("app-bar")
        with pytest.raises(ValidationError):
            _node("app@baz")

    def test_dot_only_id_raises(self):
        """점(dot)으로 시작하는 id 는 ValidationError."""
        with pytest.raises(ValidationError):
            _node(".leading.dot")


class TestFilePathConstraints:
    """NodeMetadata.file_path 절대경로 금지 (REQ-AST-JSON-002)."""

    def test_relative_path_passes(self):
        """상대 경로는 정상 통과."""
        meta = NodeMetadata(
            name="foo", file_path="app/foo.py", start_line=1, end_line=10
        )
        assert meta.file_path == "app/foo.py"

    def test_unix_absolute_path_raises(self):
        """Unix 절대 경로(/로 시작)는 ValidationError."""
        with pytest.raises(ValidationError):
            NodeMetadata(
                name="foo", file_path="/home/user/foo.py",
                start_line=1, end_line=10,
            )

    def test_windows_absolute_path_raises(self):
        """Windows 절대 경로(C:\\)는 ValidationError."""
        with pytest.raises(ValidationError):
            NodeMetadata(
                name="foo", file_path="C:\\Users\\foo.py",
                start_line=1, end_line=10,
            )

    def test_backslash_absolute_path_raises(self):
        """백슬래시로 시작하는 경로는 ValidationError."""
        with pytest.raises(ValidationError):
            NodeMetadata(
                name="foo", file_path="\\server\\share\\foo.py",
                start_line=1, end_line=10,
            )

# ══════════════════════════════════════════════════════════════════════════════
# REQ-AST-JSON-003 — Analysis 결과 직렬화
# ══════════════════════════════════════════════════════════════════════════════

import json
from app.services.analysis_service import AnalysisService, _ANALYSIS_DIR

class TestAnalysisSerialization:
    """AnalysisService 직렬화/역직렬화 (REQ-AST-JSON-003)."""

    def test_save_and_load_roundtrip(self, monkeypatch, tmp_path):
        """저장 후 불러온 객체가 원본과 동일해야 한다."""
        monkeypatch.setattr("app.services.analysis_service._ANALYSIS_DIR", tmp_path)
        
        schema = ASTAnalysisSchema(**_valid_schema())
        
        # Save
        saved_path = AnalysisService.save(schema, "test_repo")
        assert saved_path.exists()
        assert saved_path.name == "test_repo.json"
        
        # Load
        loaded_schema = AnalysisService.load("test_repo")
        
        # Verify
        assert loaded_schema.repo == schema.repo
        assert len(loaded_schema.nodes) == len(schema.nodes)
        assert len(loaded_schema.edges) == len(schema.edges)
        assert loaded_schema.summary.total_nodes == schema.summary.total_nodes

    def test_save_creates_directory(self, monkeypatch, tmp_path):
        """저장 시 대상 디렉토리가 없으면 자동 생성된다."""
        target_dir = tmp_path / "deep" / "nested" / "dir"
        monkeypatch.setattr("app.services.analysis_service._ANALYSIS_DIR", target_dir)
        
        schema = ASTAnalysisSchema(**_valid_schema())
        assert not target_dir.exists()
        
        saved_path = AnalysisService.save(schema, "new_repo")
        assert target_dir.exists()
        assert saved_path.is_file()

    def test_invalid_repo_name_raises(self):
        """경로 순회 문자가 포함된 repo_name은 예외를 발생시켜야 한다."""
        schema = ASTAnalysisSchema(**_valid_schema())
        invalid_names = ["../my_repo", "repo/name", "file.json", " "]
        
        for name in invalid_names:
            with pytest.raises(ValueError, match="허용되지 않는 문자"):
                AnalysisService.save(schema, name)
            with pytest.raises(ValueError, match="허용되지 않는 문자"):
                AnalysisService.load(name)

    def test_load_missing_file_raises(self, monkeypatch, tmp_path):
        """존재하지 않는 repo_name을 로드하려 하면 FileNotFoundError 발생."""
        monkeypatch.setattr("app.services.analysis_service._ANALYSIS_DIR", tmp_path)
        
        with pytest.raises(FileNotFoundError, match="분석 아티팩트를 찾을 수 없음"):
            AnalysisService.load("non_existent_repo")

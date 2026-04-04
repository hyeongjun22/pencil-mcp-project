"""
constants.py — 프로젝트 전역 상수

소유자: 최지웅
"""
from __future__ import annotations

# ── Pencil DSL Operation 타입 ────────────────────────────────────────────────
OP_INSERT = "I"
OP_UPDATE = "U"
OP_COPY = "C"
OP_REPLACE = "R"
OP_DELETE = "D"
OP_IMAGE = "G"
OP_MOVE = "M"

VALID_OP_TYPES: frozenset[str] = frozenset(
    {OP_INSERT, OP_UPDATE, OP_COPY, OP_REPLACE, OP_DELETE, OP_IMAGE, OP_MOVE}
)

# ── 청크 관련 ────────────────────────────────────────────────────────────────
DEFAULT_MAX_CHUNK_SIZE = 25
CONSERVATIVE_MAX_CHUNK_SIZE = 24  # 보수적 상한

# ── 파이프라인 상태 ──────────────────────────────────────────────────────────
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

# ── 검증 임계값 ─────────────────────────────────────────────────────────────
FAILURE_RATE_THRESHOLD = 0.20  # 실패율 20% 초과 시 전체 failed로 판정

# ── MCP 도구 이름 ────────────────────────────────────────────────────────────
TOOL_BATCH_DESIGN = "batch_design"
TOOL_BATCH_GET = "batch_get"
TOOL_GET_EDITOR_STATE = "get_editor_state"

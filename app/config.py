"""
config.py — 환경 변수 및 경로 상수 관리

소유자: 최지웅 (REQ-ORCH-001)
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정. .env 파일 또는 환경 변수로 오버라이드 가능."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Pencil MCP 연결 설정 ─────────────────────────────────────────────
    pencil_mcp_command: str = Field(
        default="node",
        description="Pencil MCP 서버 실행 명령어",
    )
    pencil_mcp_args: list[str] = Field(
        default_factory=list,
        description="Pencil MCP 서버 실행 인자 목록",
    )
    pencil_mcp_timeout: float = Field(
        default=30.0,
        description="Pencil MCP 호출 타임아웃 (초)",
    )

    # ── SSE 서버 설정 ────────────────────────────────────────────────────
    server_host: str = Field(
        default="127.0.0.1",
        description="SSE 서버 바인딩 주소",
    )
    server_port: int = Field(
        default=8000,
        description="SSE 서버 포트",
    )

    # ── 데이터 경로 ──────────────────────────────────────────────────────
    data_output_dir: Path = Field(
        default=Path("data/output"),
        description="최종 출력 디렉토리",
    )
    data_render_ops_dir: Path = Field(
        default=Path("data/intermediate/render_ops"),
        description="렌더 ops 중간 아티팩트 디렉토리",
    )
    data_layout_plans_dir: Path = Field(
        default=Path("data/intermediate/layout_plans"),
        description="레이아웃 플랜 아티팩트 디렉토리 (임형준 산출물)",
    )
    data_analysis_dir: Path = Field(
        default=Path("data/intermediate/analysis"),
        description="분석 아티팩트 디렉토리 (이수민 산출물)",
    )

    # ── 청크 설정 ────────────────────────────────────────────────────────
    max_chunk_size: int = Field(
        default=25,
        description="한 청크당 최대 operation 수 (Pencil 안전 한계)",
    )
    max_retries: int = Field(
        default=2,
        description="청크 실패 시 최대 재시도 횟수",
    )


# 싱글턴 인스턴스
settings = Settings()

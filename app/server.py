"""
server.py — MCP 서버 진입점

소유자: 최지웅 (REQ-ORCH-001)

- stdio 모드(기본): python -m app.server
- SSE 모드:         python -m app.server --transport sse
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import click
from mcp.server import FastMCP

from app.adapters.pencil_client import PencilClient, PencilConnectionError
from app.config import settings
from app.constants import TOOL_BATCH_DESIGN, TOOL_GET_EDITOR_STATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Pencil 클라이언트 싱글턴 ──────────────────────────────────────────────────
_pencil_client: PencilClient | None = None


def get_pencil_client() -> PencilClient:
    if _pencil_client is None:
        raise RuntimeError("PencilClient가 초기화되지 않았습니다.")
    return _pencil_client


# ── FastMCP 앱 ────────────────────────────────────────────────────────────────

def create_app() -> FastMCP:
    """FastMCP 앱을 생성하고 도구를 등록한다."""

    mcp = FastMCP(
        name="pencil-orchestrator",
        instructions=(
            "Pencil .pen 파일에 레이아웃 플랜을 렌더링하는 오케스트레이터 서버입니다. "
            "batch_design 도구로 Pencil 캔버스에 디자인 오퍼레이션을 실행하세요."
        ),
    )

    # ── 도구 등록 ─────────────────────────────────────────────────────────────

    @mcp.tool(
        name=TOOL_BATCH_DESIGN,
        description="Pencil .pen 파일에 일련의 디자인 오퍼레이션을 순차 실행한다.",
    )
    async def batch_design(
        operations: str,
        file_path: str,
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> dict[str, Any]:
        """
        Pencil batch_design 도구 래퍼.

        Args:
            operations:    실행할 Pencil 오퍼레이션 코드 문자열 (I/U/C/R/D/G 명령)
            file_path:     대상 .pen 파일의 절대 경로
            chunk_index:   현재 청크 번호 (0-indexed)
            total_chunks:  전체 청크 수

        Returns:
            실행 결과 (바인딩 맵 포함)
        """
        logger.info(
            "batch_design 호출 (chunk=%d/%d, file=%s)",
            chunk_index,
            total_chunks,
            file_path,
        )
        client = get_pencil_client()
        result = await client.batch_design(operations, file_path)
        return {
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "result": result,
        }

    @mcp.tool(
        name=TOOL_GET_EDITOR_STATE,
        description="Pencil 에디터의 현재 상태(선택 노드, 열린 파일 등)를 조회한다.",
    )
    async def get_editor_state() -> dict[str, Any]:
        """Pencil 에디터 상태 패스스루."""
        client = get_pencil_client()
        return await client.get_editor_state()

    return mcp


# ── CLI 진입점 ────────────────────────────────────────────────────────────────

@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    show_default=True,
    help="MCP 전송 레이어 선택 (stdio | sse)",
)
@click.option(
    "--host",
    default=None,
    help=f"SSE 서버 바인딩 주소 (기본: {settings.server_host})",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help=f"SSE 서버 포트 (기본: {settings.server_port})",
)
def main(transport: str, host: str | None, port: int | None) -> None:
    """Pencil Orchestrator MCP 서버를 기동한다."""
    asyncio.run(_run(transport=transport, host=host, port=port))


async def _run(
    transport: str = "stdio",
    host: str | None = None,
    port: int | None = None,
) -> None:
    _host = host or settings.server_host
    _port = port or settings.server_port

    mcp = create_app()

    global _pencil_client
    _pencil_client = PencilClient()

    try:
        # PencilClient를 단일 제어 블록(TaskGroup) 안에서 유지하며 서버를 동작시킵니다.
        async with _pencil_client:
            logger.info("Pencil MCP 클라이언트 연결 완료 (Context 관리 중)")
            if transport == "sse":
                logger.info("SSE 서버 시작 (FastMCP 기본 포트)")
                await mcp.run_sse_async()
            else:
                logger.info("stdio 모드로 MCP 서버 시작")
                await mcp.run_stdio_async()
    except PencilConnectionError as exc:
        logger.warning(
            "Pencil MCP 연결 실패 (서버가 없거나 설정 미완료): %s — 연결 없이 계속 진행", exc
        )
        # PencilClient 없이 서버만 스탠드얼론으로 기동 (도구 호출 시 내부 연결 에러 발생)
        _pencil_client = PencilClient()
        if transport == "sse":
            logger.info("SSE 서버 시작 (FastMCP 기본 포트)")
            await mcp.run_sse_async()
        else:
            logger.info("stdio 모드로 MCP 서버 시작")
            await mcp.run_stdio_async()
    except Exception as e:
        logger.error("서버 실행 중 오류: %s", e)


if __name__ == "__main__":
    main()

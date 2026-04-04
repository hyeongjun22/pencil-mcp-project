"""
pencil_client.py — Pencil MCP 서버 연결 클라이언트 어댑터

소유자: 최지웅 (REQ-ORCH-001)

mcp Python SDK의 ClientSession + StdioServerParameters를 사용하여
로컬 Pencil MCP 서버에 연결하고 batch_design / batch_get 요청을 보낸다.
"""
from __future__ import annotations

import logging
from types import TracebackType
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings
from app.constants import TOOL_BATCH_DESIGN, TOOL_BATCH_GET, TOOL_GET_EDITOR_STATE

logger = logging.getLogger(__name__)


class PencilConnectionError(Exception):
    """Pencil MCP 서버 연결 또는 통신 실패 시 발생하는 예외."""


class PencilClient:
    """
    로컬 Pencil MCP 서버에 연결하는 클라이언트 어댑터.

    사용 예::

        async with PencilClient() as client:
            result = await client.batch_get("path/to/file.pen", [])
            print(result)
    """

    def __init__(
        self,
        command: str | None = None,
        args: list[str] | None = None,
        timeout: float | None = None,
    ) -> None:
        self._command = command or settings.pencil_mcp_command
        self._args = args if args is not None else settings.pencil_mcp_args
        self._timeout = timeout or settings.pencil_mcp_timeout

        self._exit_stack: Any = None
        self._session: ClientSession | None = None

    # ── 컨텍스트 매니저 (연결 관리) ──────────────────────────────────────────

    async def __aenter__(self) -> "PencilClient":
        """Pencil MCP 프로세스에 연결하고 세션을 초기화한다."""
        if self._session is not None:
            return self

        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()

        try:
            server_params = StdioServerParameters(
                command=self._command,
                args=self._args,
            )
            read, write = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self._session.initialize()
            logger.info("PencilClient connected (command=%s args=%s)", self._command, self._args)
            return self
        except Exception as exc:
            await self._exit_stack.__aexit__(None, None, None)
            self._exit_stack = None
            raise PencilConnectionError(f"Pencil 연결 실패: {exc}") from exc

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """연결을 종료하고 리소스를 정리한다."""
        if self._exit_stack is not None:
            try:
                await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
                logger.info("PencilClient disconnected")
            except Exception as e:
                logger.warning("PencilClient disconnect 오류: %s", e)
            finally:
                self._exit_stack = None
                self._session = None

    async def connect(self) -> None:
        """이전 코드 호환성을 위한 Pass-through (사용 자제, async with 권장)"""
        pass

    async def disconnect(self) -> None:
        """이전 코드 호환성을 위한 Pass-through"""
        pass

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────

    def _ensure_connected(self) -> ClientSession:
        if self._session is None:
            raise PencilConnectionError(
                "PencilClient가 연결되지 않았습니다. connect() 또는 async with를 사용하세요."
            )
        return self._session

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """MCP 도구를 호출하고 결과를 반환한다."""
        session = self._ensure_connected()
        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as exc:
            raise PencilConnectionError(
                f"도구 호출 실패 (tool={tool_name}): {exc}"
            ) from exc

    # ── 공개 API ─────────────────────────────────────────────────────────────

    async def batch_design(self, operations: str, file_path: str) -> dict:
        """
        Pencil batch_design 도구를 호출하여 디자인 오퍼레이션을 실행한다.

        Args:
            operations: Pencil DSL 오퍼레이션 코드 문자열 (I/U/C/R/D/G 명령)
            file_path:  대상 .pen 파일의 절대 경로

        Returns:
            도구 응답 내용 (바인딩 맵 포함)
        """
        result = await self._call_tool(
            TOOL_BATCH_DESIGN,
            {"operations": operations, "filePath": file_path},
        )
        # mcp SDK는 CallToolResult를 반환 — content 리스트에서 첫 번째 text 추출
        return _extract_result(result)

    async def batch_get(self, file_path: str, node_ids: list[str]) -> dict:
        """
        Pencil batch_get 도구를 호출하여 노드 정보를 조회한다.

        Args:
            file_path: 대상 .pen 파일의 절대 경로
            node_ids:  조회할 노드 ID 목록

        Returns:
            노드 정보 딕셔너리
        """
        result = await self._call_tool(
            TOOL_BATCH_GET,
            {"filePath": file_path, "nodeIds": node_ids},
        )
        return _extract_result(result)

    async def get_editor_state(self) -> dict:
        """Pencil 에디터 상태(현재 선택, 열린 파일 등)를 조회한다."""
        result = await self._call_tool(TOOL_GET_EDITOR_STATE, {"include_schema": False})
        return _extract_result(result)

    async def list_tools(self) -> list[dict]:
        """Pencil MCP 서버가 제공하는 도구 목록을 반환한다."""
        session = self._ensure_connected()
        response = await session.list_tools()
        return [t.model_dump() for t in response.tools]


# ── 내부 유틸 ─────────────────────────────────────────────────────────────────

def _extract_result(call_result: Any) -> dict:
    """CallToolResult에서 dict 데이터를 추출한다."""
    import json

    if hasattr(call_result, "content"):
        for item in call_result.content:
            if hasattr(item, "text"):
                try:
                    return json.loads(item.text)
                except (json.JSONDecodeError, TypeError):
                    return {"raw": item.text}
    # fallback
    if isinstance(call_result, dict):
        return call_result
    return {"raw": str(call_result)}

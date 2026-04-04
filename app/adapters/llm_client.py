"""
llm_client.py — LLM 클라이언트 기본 구조 (REQ-ORCH-001 기본 구조만)

소유자: 최지웅
실제 LLM 호출 로직은 REQ-ORCH-002 이후 단계에서 구현 예정.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class LLMClientBase(ABC):
    """LLM 클라이언트 추상 기반 클래스."""

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """프롬프트를 받아 LLM 응답 문자열을 반환한다."""


class StubLLMClient(LLMClientBase):
    """
    개발/테스트용 LLM 클라이언트 스텁.

    실제 LLM을 호출하지 않고 빈 응답을 반환한다.
    REQ-ORCH-002에서 실제 구현으로 교체 예정.
    """

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        logger.warning(
            "StubLLMClient.complete() called — 실제 LLM 클라이언트로 교체 필요 (REQ-ORCH-002)"
        )
        return ""


# 기본 클라이언트 (현재는 Stub)
default_llm_client: LLMClientBase = StubLLMClient()

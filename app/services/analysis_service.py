# app/services/analysis_service.py
"""
REQ-AST-JSON-003 — 분석 결과 JSON 직렬화

추출된 메타데이터를 ASTAnalysisSchema JSON으로 저장하고,
Stage 2(임형준)가 data/intermediate/analysis/<repo_name>.json을 읽어
즉시 layout plan에 착수할 수 있도록 한다.

Owner: 이수민 (Analysis Owner)
"""
from __future__ import annotations

import re
from pathlib import Path

from app.models.analysis_schema import ASTAnalysisSchema

# ── 상수 ─────────────────────────────────────────────────────────────────────

_ANALYSIS_DIR = Path("data/intermediate/analysis")

# 영문자·숫자·밑줄·하이픈만 허용 (경로 순회 공격 방지)
_SAFE_REPO_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────


def _validate_repo_name(repo_name: str) -> None:
    """repo_name이 안전한 식별자인지 검증한다.

    Args:
        repo_name: 검증할 repo 이름.

    Raises:
        ValueError: 허용되지 않는 문자가 포함된 경우.
    """
    if not _SAFE_REPO_NAME_RE.match(repo_name):
        raise ValueError(
            "repo_name은 영문자·숫자·밑줄·하이픈만 허용됩니다. "
            f"got: {repo_name!r}"
        )


# ── 서비스 ────────────────────────────────────────────────────────────────────


class AnalysisService:
    """ASTAnalysisSchema 직렬화/역직렬화 서비스.

    저장 경로: data/intermediate/analysis/<repo_name>.json
    """

    @staticmethod
    def save(schema: ASTAnalysisSchema, repo_name: str) -> Path:
        """ASTAnalysisSchema를 JSON 파일로 저장한다.

        Args:
            schema: 저장할 ASTAnalysisSchema 객체.
            repo_name: 아티팩트 파일명에 사용할 repo 식별자.
                       영문자·숫자·밑줄·하이픈만 허용.

        Returns:
            저장된 파일의 Path 객체.

        Raises:
            ValueError: repo_name에 허용되지 않는 문자가 포함된 경우.
        """
        _validate_repo_name(repo_name)

        out_dir = _ANALYSIS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = out_dir / f"{repo_name}.json"
        out_path.write_text(
            schema.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return out_path

    @staticmethod
    def load(repo_name: str) -> ASTAnalysisSchema:
        """JSON 파일에서 ASTAnalysisSchema를 불러온다.

        불러온 JSON은 Pydantic 스키마 검증(ValidationError)을 자동으로 통과해야 한다.

        Args:
            repo_name: 불러올 아티팩트의 repo 식별자.
                       영문자·숫자·밑줄·하이픈만 허용.

        Returns:
            검증을 통과한 ASTAnalysisSchema 객체.

        Raises:
            ValueError: repo_name에 허용되지 않는 문자가 포함된 경우.
            FileNotFoundError: 해당 repo_name의 JSON 파일이 없는 경우.
        """
        _validate_repo_name(repo_name)

        path = _ANALYSIS_DIR / f"{repo_name}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"분석 아티팩트를 찾을 수 없음: {path}"
            )

        return ASTAnalysisSchema.model_validate_json(
            path.read_text(encoding="utf-8")
        )

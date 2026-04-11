# REQ-AST-JSON-003 — 분석 결과 JSON 직렬화

## Metadata

| 항목 | 내용 |
|---|---|
| **ID** | REQ-AST-JSON-003 |
| **Owner** | 이수민 (Analysis Owner) |
| **Status** | ✅ Completed |
| **Branch** | `feat/REQ-AST-JSON-003-analysis-json-serializer` |
| **Created** | 2026-04-05 |
| **Upstream** | REQ-ANL-001 (`ASTAnalysisSchema` 스키마), REQ-ANL-002 (AST 추출 툴) |
| **Downstream** | 임형준 (Stage 2: Layout / Prompt Preparation) |

---

## Problem

`ASTAnalysisSchema`는 정의되어 있지만 (REQ-ANL-001), 실제로 JSON 파일로 저장하거나 불러오는 코드가 없다.

구체적인 문제:

- [x] 1. 추출된 분석 결과를 `ASTAnalysisSchema`로 조립하는 함수가 없음
- [x] 2. `ASTAnalysisSchema`를 JSON 파일로 저장하는 함수가 없음 (`data/intermediate/analysis/<repo>.json`)
- [x] 3. JSON 파일에서 `ASTAnalysisSchema`를 다시 읽어오는 함수가 없음
- [x] 4. 출력 디렉토리(`data/intermediate/analysis/`)가 없음
- [x] 5. `analysis_service.py`가 비어 있어 Stage 2가 아티팩트를 전달받을 진입점이 없음

---

## Goal

추출된 메타데이터를 `ASTAnalysisSchema` JSON으로 저장하고,
Stage 2가 `data/intermediate/analysis/<repo_name>.json`을 읽어 즉시 layout plan에 착수할 수 있게 한다.

구체적으로:
1. `analysis_service.py`에 직렬화/역직렬화 함수를 구현한다
2. `data/intermediate/analysis/` 디렉토리 구조를 생성한다
3. 테스트를 추가한다

---

## Acceptance Criteria

- [x] `AnalysisService.save(schema, repo_name)` — `ASTAnalysisSchema`를 JSON 파일로 저장한다
- [x] `AnalysisService.load(repo_name)` — JSON 파일에서 `ASTAnalysisSchema`를 불러와 Pydantic 검증을 통과한다
- [x] 저장 경로는 `data/intermediate/analysis/<repo_name>.json`이다
- [x] 저장 시 디렉토리가 없으면 자동 생성된다
- [x] `repo_name`에 경로 순회 문자(`..`, `/`, `\`)가 포함되어 있으면 `ValueError`를 발생시킨다
- [x] 저장된 JSON이 `ASTAnalysisSchema.model_validate_json()`으로 검증 통과한다
- [x] `tests/test_ast_parser.py`에 직렬화 관련 테스트 케이스가 추가된다

---

## Scope

### In Scope (이수민 소유 영역)
- `app/services/analysis_service.py` — 직렬화/역직렬화 서비스 구현
- `data/intermediate/analysis/.gitkeep` — 디렉토리 구조 생성
- `tests/test_ast_parser.py` — 직렬화 테스트 추가

### Out of Scope
- `app/tools/ast_parser.py`, `repo_scanner.py`, `arch_summarizer.py` — 실제 추출 로직 (별도 REQ-ANL-002)
- `app/models/analysis_schema.py` — 스키마 변경 없음
- Stage 2, Stage 3 코드 일체

---

## Affected Files

| 파일 | 변경 유형 | 사유 |
|---|---|---|
| `app/services/analysis_service.py` | MODIFY | 직렬화/역직렬화 함수 구현 |
| `data/intermediate/analysis/.gitkeep` | NEW | 아티팩트 디렉토리 생성 |
| `tests/test_ast_parser.py` | MODIFY | 직렬화 테스트 추가 |

---

## Implementation Plan

### 1. `analysis_service.py` 구현

```python
# app/services/analysis_service.py
import json
import re
from pathlib import Path
from app.models.analysis_schema import ASTAnalysisSchema

_ANALYSIS_DIR = Path("data/intermediate/analysis")
_SAFE_REPO_NAME = re.compile(r"^[A-Za-z0-9_\-]+$")


class AnalysisService:

    @staticmethod
    def save(schema: ASTAnalysisSchema, repo_name: str) -> Path:
        """ASTAnalysisSchema를 JSON 파일로 저장한다."""
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
        """JSON 파일에서 ASTAnalysisSchema를 불러온다."""
        _validate_repo_name(repo_name)
        path = _ANALYSIS_DIR / f"{repo_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"분석 아티팩트를 찾을 수 없음: {path}")
        return ASTAnalysisSchema.model_validate_json(path.read_text(encoding="utf-8"))


def _validate_repo_name(repo_name: str) -> None:
    if not _SAFE_REPO_NAME.match(repo_name):
        raise ValueError(
            f"repo_name은 영문자·숫자·밑줄·하이픈만 허용됩니다. got: {repo_name!r}"
        )
```

**핵심 결정 사항:**
- `model_dump_json(indent=2)` — Pydantic 내장 직렬화 사용 (datetime ISO 8601 자동 처리)
- `model_validate_json()` — 역직렬화 시 스키마 검증 자동 수행
- `repo_name` 정규식 검증 — 경로 순회 공격 방지
- 저장 경로는 프로젝트 루트 상대 경로 (`data/intermediate/analysis/`)

### 2. `data/intermediate/analysis/.gitkeep` 생성

빈 파일로 디렉토리를 Git에 추적.

### 3. `tests/test_ast_parser.py` 테스트 추가

```python
# ── Serialization (REQ-AST-JSON-003) ─────────────────────────
class TestAnalysisSerialization:
    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        """저장 후 불러온 객체가 원본과 동일해야 한다."""
        ...

    def test_save_creates_directory(self, tmp_path, monkeypatch):
        """저장 디렉토리가 없으면 자동 생성된다."""
        ...

    def test_load_validates_schema(self, tmp_path, monkeypatch):
        """불러온 JSON이 Pydantic 검증을 통과한다."""
        ...

    def test_invalid_repo_name_raises(self):
        """경로 순회 문자 포함 시 ValueError."""
        ...

    def test_load_missing_file_raises(self):
        """파일 없으면 FileNotFoundError."""
        ...
```

---

## Risk

| 리스크 | 영향 | 대응 |
|---|---|---|
| 업스트림 툴(ast_parser 등)이 비어 있음 | 실제 추출 데이터 없이 직렬화만 구현 | 테스트에서 `_valid_schema()` 픽스처로 대체 |
| `data/` 디렉토리가 Git에 없음 | 실행 시 경로 오류 | `.gitkeep` + `mkdir(parents=True, exist_ok=True)` |
| Windows/Unix 경로 차이 | `Path` 사용으로 OS 무관 처리 | `pathlib.Path` 일관 사용 |

---

## Validation Plan

```bash
pytest tests/test_ast_parser.py -v -k "Serialization"
# 전체 테스트도 함께 확인
pytest tests/test_ast_parser.py -v
```

모든 케이스가 PASS여야 한다.

---

## Docs Impact

- `docs/json_schema.md` — "Artifact Location" 섹션 이미 기술됨. 추가 수정 없음.

---

## Execution Log

- `2026-04-05` — `app/services/analysis_service.py` 내부 `AnalysisService.save()`, `load()` 메서드 및 경로 검증 정규식 구현
- `2026-04-05` — Git 추적을 위해 빈 `data/intermediate/analysis/.gitkeep` 생성
- `2026-04-05` — `tests/test_ast_parser.py`에 `TestAnalysisSerialization` 관련 테스트 4종 추가 (유효 경로/저장 및 로드 검증 확인)

---

## Final Outcome

- **변경된 파일**: `app/services/analysis_service.py`, `tests/test_ast_parser.py`, `data/intermediate/analysis/.gitkeep`
- **테스트 결과**: `pytest tests/test_ast_parser.py` PASS
- **다음 핸드오프**: 임형준(Stage 2) — 생성된 중간 JSON 아티팩트를 읽어들여 레이아웃 플랜 생성을 테스트해 볼 수 있습니다.

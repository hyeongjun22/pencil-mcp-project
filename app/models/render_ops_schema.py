from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field

class RenderOpType(str, Enum):
    INSERT = "I"
    COPY = "C"
    UPDATE = "U"
    REPLACE = "R"
    MOVE = "M"
    DELETE = "D"
    GENERATE_IMAGE = "G"

class RenderOpBase(BaseModel):
    """
    모든 렌더링 오퍼레이션의 공통 필드입니다.
    """
    op_type: RenderOpType
    # Pencil proxy에서 자식/참조 등을 사용하기 위한 연결변수(바인딩) 이름
    binding: Optional[str] = Field(default=None, description="오퍼레이션 결과에 할당할 식별자 (예: myElement)")

class InsertOp(RenderOpBase):
    op_type: Literal[RenderOpType.INSERT] = RenderOpType.INSERT
    parent: str = Field(..., description="부모 노드 ID 또는 사전에 선언된 바인딩 이름")
    node_data: Dict[str, Any] = Field(..., description="생성할 노드의 스키마 데이터")

class CopyOp(RenderOpBase):
    op_type: Literal[RenderOpType.COPY] = RenderOpType.COPY
    path: str = Field(..., description="복사할 원본 노드 ID")
    parent: str = Field(..., description="복사본이 배치될 부모 노드 ID 또는 바인딩 이름")
    copy_node_data: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="복사된 노드를 커스터마이즈할 속성 데이터 (positioning 및 descendants 등 포함 가능)"
    )

class UpdateOp(RenderOpBase):
    op_type: Literal[RenderOpType.UPDATE] = RenderOpType.UPDATE
    path: str = Field(..., description="업데이트 대상의 식별자")
    update_data: Dict[str, Any] = Field(..., description="수정할 노드 데이터")

class ReplaceOp(RenderOpBase):
    op_type: Literal[RenderOpType.REPLACE] = RenderOpType.REPLACE
    path: str = Field(..., description="교체 대상 노드의 경로")
    node_data: Dict[str, Any] = Field(..., description="새로운 노드의 데이터")

class MoveOp(RenderOpBase):
    op_type: Literal[RenderOpType.MOVE] = RenderOpType.MOVE
    node_id: str = Field(..., description="이동시킬 노드의 ID")
    parent: Optional[str] = Field(default=None, description="새로운 부모 노드 ID")
    index: Optional[int] = Field(default=None, description="새로운 부모 하위의 위치 인덱스")

class DeleteOp(RenderOpBase):
    op_type: Literal[RenderOpType.DELETE] = RenderOpType.DELETE
    node_id: str = Field(..., description="삭제할 노드의 ID")

class GenerateImageOp(RenderOpBase):
    op_type: Literal[RenderOpType.GENERATE_IMAGE] = RenderOpType.GENERATE_IMAGE
    node_id: str = Field(..., description="이미지 채우기를 적용시킬 대상 노드 ID")
    image_type: Literal["ai", "stock"] = Field(..., description="생성 소스 (AI 또는 분배 스톡)")
    prompt: str = Field(..., description="AI 생성 프롬프트 또는 스톡 검색 키워드")

# 다형성 지원 Union 모델
RenderOp = Annotated[
    Union[
        InsertOp,
        CopyOp,
        UpdateOp,
        ReplaceOp,
        MoveOp,
        DeleteOp,
        GenerateImageOp
    ],
    Field(discriminator='op_type')
]

class RenderChunk(BaseModel):
    """
    Pencil Batch Design을 위해 최대 용량 제한 묶음으로 스케줄링될 오퍼레이션의 Chunk 단위
    AGENTS.md에 따라 20~25개 단위로 나뉘어져야 함
    """
    chunk_index: int = Field(..., description="청크의 순서 인덱스 (0부터 시작)")
    operations: List[RenderOp] = Field(
        ..., 
        max_length=25, 
        description="최대 25개 이내의 오퍼레이션 리스트"
    )

class RenderPlan(BaseModel):
    """
    전체 렌더링 파이프라인의 작업 내역 명세 (여러 청크의 묶음)
    """
    plan_id: str = Field(..., description="렌더 플랜 고유 식별자")
    layout_plan_id: Optional[str] = Field(default=None, description="원본 레이아웃 플랜 식별자")
    total_chunks: int = Field(..., description="총 청크 수")
    chunks: List[RenderChunk] = Field(..., description="렌더를 실행할 청크 리스트")

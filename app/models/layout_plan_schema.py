from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.common import Alignment, LayoutDirection, VerticalAlignment


# ---------------------------------------------------------------------------
# 레이아웃 노드 크기 모드 (SizeMode)
# ---------------------------------------------------------------------------

class SizeMode(str, Enum):
    """노드의 폭이나 높이를 결정하는 방식."""

    FILL = "fill_container"
    HUG = "hug_contents"
    FIXED = "fixed"


# ---------------------------------------------------------------------------
# 레이아웃 래핑 (FlexWrap)
# ---------------------------------------------------------------------------

class FlexWrap(str, Enum):
    """자식 요소 래핑 여부."""

    NO_WRAP = "nowrap"
    WRAP = "wrap"


# ---------------------------------------------------------------------------
# 크기 정의 (SizeDefinition)
# ---------------------------------------------------------------------------

class SizeDefinition(BaseModel):
    """
    크기(Width/Height)를 지정하는 모델.
    모드가 FIXED일 때만 value 값이 의미를 가집니다.
    """
    mode: SizeMode
    value: Optional[int] = Field(default=None, description="고정 크기일 경우의 픽셀 값")


# ---------------------------------------------------------------------------
# 패딩 정의 (PaddingModel)
# ---------------------------------------------------------------------------

class PaddingModel(BaseModel):
    """상하좌우 개별 패딩 지정을 위한 모델."""
    top: int = 0
    right: int = 0
    bottom: int = 0
    left: int = 0


# ---------------------------------------------------------------------------
# 레이아웃 노드 (LayoutNode)
# ---------------------------------------------------------------------------

class LayoutNode(BaseModel):
    """
    UI의 계층적 공간 배치를 나타내는 핵심 노드.
    Flexbox 구조에 대응할 수 있도록 설계되었습니다.
    """
    node_id: str = Field(..., description="노드의 고유 식별자")
    node_type: str = Field(..., description="노드의 성격 (예: 'frame', 'text', 'image', 'component')")
    
    # 크기 속성
    width: SizeDefinition
    height: SizeDefinition
    
    # Flex 속성 (자식 컨테이너일 경우)
    direction: Optional[LayoutDirection] = Field(default=None, description="자식 노드들의 배치 방향")
    flex_wrap: Optional[FlexWrap] = Field(default=FlexWrap.NO_WRAP, description="자식 노드들의 래핑 여부")
    padding: Union[int, PaddingModel] = Field(default=0, description="내부 여백 (단일 int 또는 상하좌우 객체 지정)")
    gap: int = Field(default=0, description="자식 노드 간의 간격(gap)")
    
    # 정렬 속성
    alignment: Optional[Alignment] = Field(default=None, description="자식 노드의 수평 정렬 (수직 방향 시 교차축/주축 영향)")
    vertical_alignment: Optional[VerticalAlignment] = Field(default=None, description="자식 노드의 수직 정렬")
    
    # 부가 속성 (텍스트, src 등 실제 렌더링 값)
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="렌더링에 필요한 추가 속성값들")
    
    # 자식 노드
    children: List['LayoutNode'] = Field(default_factory=list, description="하위 레이아웃 노드 목록")

# 재귀 구조를 위해 업데이트
LayoutNode.model_rebuild()


# ---------------------------------------------------------------------------
# Layout Plan 루트 및 메타데이터
# ---------------------------------------------------------------------------

class LayoutPlanMeta(BaseModel):
    """레이아웃 플랜에 대한 메타데이터."""
    reference_id: Optional[str] = Field(default=None, description="기반이 된 레퍼런스 이미지 ID 등 참조 정보")
    target_platform: Optional[str] = Field(default=None, description="대상 플랫폼 (예: 'web', 'mobile')")
    generated_at: Optional[datetime] = Field(default=None, description="레이아웃 플랜 생성 시간")


class LayoutPlan(BaseModel):
    """
    시각화 파이프라인의 Stage 2에서 출력되는 레이아웃 구조체.
    Presentation 요소가 들어가기 전의 기하학적 공간 배치를 정의합니다.
    """
    meta: LayoutPlanMeta = Field(default_factory=LayoutPlanMeta)
    root: LayoutNode = Field(..., description="최상위 컨테이너 노드")

"""
Presentation 스키마 정의 모듈.

시각화 파이프라인 Stage 2(Layout / Prompt Preparation)의 중간 산출물 구조를
Pydantic v2 모델로 정의합니다.

계층 구조
---------
Presentation (루트)
├── PresentationMeta       — 메타정보 (제목, 설명, 원본 저장소 등)
├── StyleGuide             — 전역 스타일
│   ├── ColorPalette       — 색상 팔레트 (10색)
│   ├── Typography         — 타이포그래피 설정
│   └── Spacing            — 간격 기본값
└── Slide[]                — 슬라이드 목록
    ├── SlideLayout        — 레이아웃
    │   └── Section[]      — 섹션
    │       └── ContentBlock[]  — 콘텐츠 블록
    └── notes              — 발표자 노트 (문자열)

출력 경로
---------
``data/intermediate/presentation/``
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.common import (
    Alignment,
    ContentType,
    LayoutDirection,
    SlideRole,
    VerticalAlignment,
)


# ===================================================================
# 스타일 관련 모델
# ===================================================================


class ColorPalette(BaseModel):
    """프레젠테이션 전역 색상 팔레트(10색)."""

    primary: str = Field(
        ...,
        description="주 브랜드 색상 (예: '#1E40AF')",
    )
    secondary: str = Field(
        ...,
        description="보조 브랜드 색상 (예: '#7C3AED')",
    )
    accent: str = Field(
        ...,
        description="강조/액센트 색상 (예: '#F59E0B')",
    )
    background: str = Field(
        ...,
        description="배경 색상 (예: '#0F172A')",
    )
    surface: str = Field(
        ...,
        description="카드/패널 표면 색상 (예: '#1E293B')",
    )
    text_primary: str = Field(
        ...,
        description="주 텍스트 색상 (예: '#F8FAFC')",
    )
    text_secondary: str = Field(
        ...,
        description="보조 텍스트 색상 (예: '#94A3B8')",
    )
    success: str = Field(
        default="#10B981",
        description="성공 상태 색상",
    )
    warning: str = Field(
        default="#F59E0B",
        description="경고 상태 색상",
    )
    error: str = Field(
        default="#EF4444",
        description="에러 상태 색상",
    )


class Typography(BaseModel):
    """타이포그래피 설정.

    3종 폰트 패밀리(heading / body / code)와 6단계 크기 프리셋을 정의합니다.
    """

    font_family_heading: str = Field(
        default="Inter",
        description="제목용 폰트 패밀리",
    )
    font_family_body: str = Field(
        default="Inter",
        description="본문용 폰트 패밀리",
    )
    font_family_code: str = Field(
        default="JetBrains Mono",
        description="코드용 고정폭 폰트 패밀리",
    )
    font_size_title: int = Field(
        default=48,
        ge=12,
        le=120,
        description="타이틀 폰트 크기(px)",
    )
    font_size_heading: int = Field(
        default=32,
        ge=12,
        le=96,
        description="헤딩 폰트 크기(px)",
    )
    font_size_subheading: int = Field(
        default=24,
        ge=10,
        le=72,
        description="서브헤딩 폰트 크기(px)",
    )
    font_size_body: int = Field(
        default=16,
        ge=8,
        le=48,
        description="본문 폰트 크기(px)",
    )
    font_size_caption: int = Field(
        default=12,
        ge=6,
        le=36,
        description="캡션 폰트 크기(px)",
    )
    font_size_code: int = Field(
        default=14,
        ge=8,
        le=36,
        description="코드 폰트 크기(px)",
    )


class Spacing(BaseModel):
    """간격(패딩/갭) 기본값."""

    padding_slide: int = Field(
        default=48,
        ge=0,
        description="슬라이드 전체 패딩(px)",
    )
    padding_section: int = Field(
        default=24,
        ge=0,
        description="섹션 내부 패딩(px)",
    )
    padding_block: int = Field(
        default=16,
        ge=0,
        description="콘텐츠 블록 내부 패딩(px)",
    )
    gap_sections: int = Field(
        default=32,
        ge=0,
        description="섹션 간 갭(px)",
    )
    gap_blocks: int = Field(
        default=16,
        ge=0,
        description="콘텐츠 블록 간 갭(px)",
    )


class StyleGuide(BaseModel):
    """전역 스타일 가이드.

    ColorPalette, Typography, Spacing을 하나로 묶어
    프레젠테이션 전체에 일관된 시각적 규칙을 적용합니다.
    """

    color_palette: ColorPalette = Field(
        ...,
        description="색상 팔레트",
    )
    typography: Typography = Field(
        default_factory=Typography,
        description="타이포그래피 설정",
    )
    spacing: Spacing = Field(
        default_factory=Spacing,
        description="간격 기본값",
    )


# ===================================================================
# 콘텐츠 관련 모델
# ===================================================================


class ContentBlock(BaseModel):
    """개별 콘텐츠 요소.

    슬라이드 내 가장 작은 렌더링 단위입니다.
    텍스트, 코드, 이미지, 차트 등 다양한 유형을 ``content_type``으로 구분합니다.
    """

    block_id: str = Field(
        ...,
        min_length=1,
        description="블록 고유 식별자 (슬라이드 내에서 유일)",
    )
    content_type: ContentType = Field(
        ...,
        description="콘텐츠 유형",
    )
    content: str | list[str] = Field(
        ...,
        description="콘텐츠 본문. 단일 문자열 또는 항목 리스트(bullet_list 등)",
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description=(
            "콘텐츠 유형별 추가 메타데이터. "
            "예: code_block → {'language': 'python'}, "
            "image → {'alt': '아키텍처 다이어그램', 'src': '...'}"
        ),
    )
    style_overrides: dict[str, Any] | None = Field(
        default=None,
        description="전역 StyleGuide를 오버라이드하는 개별 스타일 속성",
    )


# ===================================================================
# 레이아웃 관련 모델
# ===================================================================


class Section(BaseModel):
    """콘텐츠 블록의 논리적 그룹.

    하나의 슬라이드 레이아웃 내에서 좌측 패널, 우측 패널 등
    독립적인 콘텐츠 영역을 나타냅니다.
    """

    section_id: str = Field(
        ...,
        min_length=1,
        description="섹션 고유 식별자",
    )
    weight: float = Field(
        default=1.0,
        gt=0.0,
        le=10.0,
        description="레이아웃 내 공간 비율 가중치 (예: 1.0 = 균등, 2.0 = 두 배)",
    )
    alignment: Alignment = Field(
        default=Alignment.LEFT,
        description="수평 정렬",
    )
    vertical_alignment: VerticalAlignment = Field(
        default=VerticalAlignment.TOP,
        description="수직 정렬",
    )
    content_blocks: list[ContentBlock] = Field(
        default_factory=list,
        description="이 섹션에 포함된 콘텐츠 블록 목록",
    )


class SlideLayout(BaseModel):
    """슬라이드 레이아웃 정의.

    섹션들의 배치 방향(수평/수직)과 포함된 섹션 목록을 기술합니다.
    """

    direction: LayoutDirection = Field(
        default=LayoutDirection.VERTICAL,
        description="섹션 배치 방향",
    )
    sections: list[Section] = Field(
        default_factory=list,
        min_length=1,
        description="레이아웃 내 섹션 목록 (최소 1개)",
    )


# ===================================================================
# 슬라이드 모델
# ===================================================================


class Slide(BaseModel):
    """단일 슬라이드.

    슬라이드의 역할(role), 제목, 레이아웃 구조, 발표자 노트를 포함합니다.
    """

    slide_index: int = Field(
        ...,
        ge=0,
        description="슬라이드 순서 인덱스 (0부터 시작)",
    )
    role: SlideRole = Field(
        ...,
        description="슬라이드의 용도/역할",
    )
    title: str = Field(
        ...,
        min_length=1,
        description="슬라이드 제목",
    )
    layout: SlideLayout = Field(
        ...,
        description="슬라이드 레이아웃 구조",
    )
    notes: str | None = Field(
        default=None,
        description="발표자 노트 (선택)",
    )


# ===================================================================
# 메타 정보
# ===================================================================


class PresentationMeta(BaseModel):
    """프레젠테이션 메타정보."""

    title: str = Field(
        ...,
        min_length=1,
        description="프레젠테이션 제목",
    )
    description: str | None = Field(
        default=None,
        description="프레젠테이션 설명",
    )
    source_repo: str | None = Field(
        default=None,
        description="원본 코드 저장소 이름/경로",
    )
    total_slides: int = Field(
        ...,
        ge=1,
        description="총 슬라이드 수",
    )
    target_audience: str | None = Field(
        default=None,
        description="대상 청중 (예: '개발 팀', '경영진')",
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="생성 시각 (ISO 8601)",
    )


# ===================================================================
# 루트 모델
# ===================================================================


class Presentation(BaseModel):
    """프레젠테이션 루트 모델.

    시각화 파이프라인 Stage 2의 최종 산출물이며,
    Stage 3(Render Execution)의 입력 계약(contract)입니다.

    사용 예시
    ---------
    >>> import json
    >>> data = json.loads(json_string)
    >>> presentation = Presentation.model_validate(data)
    >>> schema = Presentation.model_json_schema()
    """

    meta: PresentationMeta = Field(
        ...,
        description="프레젠테이션 메타정보",
    )
    style_guide: StyleGuide = Field(
        ...,
        description="전역 스타일 가이드",
    )
    slides: list[Slide] = Field(
        ...,
        min_length=1,
        description="슬라이드 목록 (최소 1개)",
    )

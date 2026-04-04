"""
공통 타입 정의 모듈.

파이프라인 전체에서 공유하는 기본 열거형(Enum)과 타입을 정의합니다.
모든 스키마 모듈(analysis, layout_plan, presentation, render_ops)에서
import하여 사용할 수 있습니다.
"""

from enum import Enum


# ---------------------------------------------------------------------------
# 콘텐츠 유형 (ContentType)
# ---------------------------------------------------------------------------


class ContentType(str, Enum):
    """슬라이드 내 개별 콘텐츠 블록의 유형."""

    TITLE = "title"
    SUBTITLE = "subtitle"
    HEADING = "heading"
    BODY_TEXT = "body_text"
    BULLET_LIST = "bullet_list"
    CODE_BLOCK = "code_block"
    IMAGE = "image"
    DIAGRAM = "diagram"
    TABLE = "table"
    CHART = "chart"
    ICON = "icon"
    QUOTE = "quote"
    METRIC = "metric"
    DIVIDER = "divider"


# ---------------------------------------------------------------------------
# 레이아웃 방향 (LayoutDirection)
# ---------------------------------------------------------------------------


class LayoutDirection(str, Enum):
    """섹션 배치 방향."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


# ---------------------------------------------------------------------------
# 수평 정렬 (Alignment)
# ---------------------------------------------------------------------------


class Alignment(str, Enum):
    """텍스트 또는 콘텐츠의 수평 정렬."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


# ---------------------------------------------------------------------------
# 수직 정렬 (VerticalAlignment)
# ---------------------------------------------------------------------------


class VerticalAlignment(str, Enum):
    """콘텐츠의 수직 정렬."""

    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


# ---------------------------------------------------------------------------
# 슬라이드 역할 (SlideRole)
# ---------------------------------------------------------------------------


class SlideRole(str, Enum):
    """슬라이드의 용도/역할 분류."""

    COVER = "cover"
    TOC = "toc"
    SECTION_DIVIDER = "section_divider"
    CONTENT = "content"
    COMPARISON = "comparison"
    ARCHITECTURE = "architecture"
    CODE_WALKTHROUGH = "code_walkthrough"
    METRICS_DASHBOARD = "metrics_dashboard"
    CLOSING = "closing"

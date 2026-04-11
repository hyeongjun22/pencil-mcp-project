"""
Presentation 스키마 단위 테스트.

테스트 범위
-----------
1. 유효한 JSON으로 모델 생성 검증
2. 필수 필드 누락 시 ValidationError 검증
3. 잘못된 enum 값 검증
4. JSON 직렬화 ↔ 역직렬화 라운드트립
5. model_json_schema() export 검증
6. 중첩 구조 검증 (Slide → Section → ContentBlock)
7. 엣지 케이스 (빈 슬라이드 목록, 최소/최대 값 등)
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.common import (
    Alignment,
    ContentType,
    LayoutDirection,
    SlideRole,
    VerticalAlignment,
)
from app.models.presentation_schema import (
    ColorPalette,
    ContentBlock,
    Presentation,
    PresentationMeta,
    Section,
    Slide,
    SlideLayout,
    Spacing,
    StyleGuide,
    Typography,
)


# ===================================================================
# 픽스처 (Fixture)
# ===================================================================


@pytest.fixture
def sample_color_palette() -> dict:
    """유효한 색상 팔레트 데이터."""
    return {
        "primary": "#1E40AF",
        "secondary": "#7C3AED",
        "accent": "#F59E0B",
        "background": "#0F172A",
        "surface": "#1E293B",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
    }


@pytest.fixture
def sample_style_guide(sample_color_palette: dict) -> dict:
    """유효한 스타일 가이드 데이터."""
    return {
        "color_palette": sample_color_palette,
    }


@pytest.fixture
def sample_content_block() -> dict:
    """유효한 콘텐츠 블록 데이터."""
    return {
        "block_id": "title_block",
        "content_type": "title",
        "content": "프로젝트 아키텍처",
    }


@pytest.fixture
def sample_section(sample_content_block: dict) -> dict:
    """유효한 섹션 데이터."""
    return {
        "section_id": "main",
        "content_blocks": [sample_content_block],
    }


@pytest.fixture
def sample_slide(sample_section: dict) -> dict:
    """유효한 슬라이드 데이터."""
    return {
        "slide_index": 0,
        "role": "cover",
        "title": "My Project Architecture",
        "layout": {
            "direction": "vertical",
            "sections": [sample_section],
        },
    }


@pytest.fixture
def sample_presentation(sample_style_guide: dict, sample_slide: dict) -> dict:
    """유효한 프레젠테이션 전체 데이터."""
    return {
        "meta": {
            "title": "Repository Architecture Overview",
            "description": "코드 저장소의 아키텍처를 시각적으로 설명",
            "source_repo": "my-project",
            "total_slides": 1,
            "target_audience": "개발 팀",
            "generated_at": "2026-04-04T00:00:00",
        },
        "style_guide": sample_style_guide,
        "slides": [sample_slide],
    }


# ===================================================================
# 1. 유효한 데이터로 모델 생성 테스트
# ===================================================================


class TestModelCreation:
    """유효한 JSON 데이터로 모델이 올바르게 생성되는지 검증."""

    def test_color_palette_creation(self, sample_color_palette: dict):
        """ColorPalette가 올바르게 생성되어야 함."""
        palette = ColorPalette(**sample_color_palette)
        assert palette.primary == "#1E40AF"
        assert palette.secondary == "#7C3AED"
        # 기본값 확인
        assert palette.success == "#10B981"
        assert palette.warning == "#F59E0B"
        assert palette.error == "#EF4444"

    def test_typography_defaults(self):
        """Typography가 기본값으로 올바르게 생성되어야 함."""
        typo = Typography()
        assert typo.font_family_heading == "Inter"
        assert typo.font_family_code == "JetBrains Mono"
        assert typo.font_size_title == 48
        assert typo.font_size_body == 16

    def test_spacing_defaults(self):
        """Spacing이 기본값으로 올바르게 생성되어야 함."""
        spacing = Spacing()
        assert spacing.padding_slide == 48
        assert spacing.gap_sections == 32

    def test_style_guide_creation(self, sample_style_guide: dict):
        """StyleGuide가 올바르게 생성되어야 함 (typography/spacing은 기본값)."""
        guide = StyleGuide(**sample_style_guide)
        assert guide.color_palette.primary == "#1E40AF"
        assert guide.typography.font_family_heading == "Inter"
        assert guide.spacing.padding_slide == 48

    def test_content_block_creation(self, sample_content_block: dict):
        """ContentBlock이 올바르게 생성되어야 함."""
        block = ContentBlock(**sample_content_block)
        assert block.block_id == "title_block"
        assert block.content_type == ContentType.TITLE
        assert block.content == "프로젝트 아키텍처"
        assert block.meta is None
        assert block.style_overrides is None

    def test_content_block_with_list_content(self):
        """ContentBlock이 리스트 타입 content를 지원해야 함."""
        block = ContentBlock(
            block_id="bullets",
            content_type=ContentType.BULLET_LIST,
            content=["항목 1", "항목 2", "항목 3"],
        )
        assert isinstance(block.content, list)
        assert len(block.content) == 3

    def test_content_block_with_meta(self):
        """ContentBlock이 meta 필드를 올바르게 처리해야 함."""
        block = ContentBlock(
            block_id="code",
            content_type=ContentType.CODE_BLOCK,
            content="print('hello')",
            meta={"language": "python", "line_numbers": True},
        )
        assert block.meta["language"] == "python"

    def test_section_creation(self, sample_section: dict):
        """Section이 올바르게 생성되어야 함."""
        section = Section(**sample_section)
        assert section.section_id == "main"
        assert section.weight == 1.0
        assert section.alignment == Alignment.LEFT
        assert section.vertical_alignment == VerticalAlignment.TOP
        assert len(section.content_blocks) == 1

    def test_slide_creation(self, sample_slide: dict):
        """Slide가 올바르게 생성되어야 함."""
        slide = Slide(**sample_slide)
        assert slide.slide_index == 0
        assert slide.role == SlideRole.COVER
        assert slide.title == "My Project Architecture"
        assert slide.layout.direction == LayoutDirection.VERTICAL
        assert slide.notes is None

    def test_presentation_creation(self, sample_presentation: dict):
        """Presentation 루트 모델이 올바르게 생성되어야 함."""
        pres = Presentation.model_validate(sample_presentation)
        assert pres.meta.title == "Repository Architecture Overview"
        assert pres.meta.total_slides == 1
        assert len(pres.slides) == 1
        assert pres.slides[0].role == SlideRole.COVER


# ===================================================================
# 2. 필수 필드 누락 시 ValidationError 테스트
# ===================================================================


class TestValidationErrors:
    """필수 필드 누락이나 잘못된 값에 대한 검증 실패를 확인."""

    def test_color_palette_missing_required(self):
        """ColorPalette 필수 필드 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            ColorPalette(primary="#1E40AF")  # secondary, accent 등 누락

    def test_content_block_missing_block_id(self):
        """ContentBlock에서 block_id 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            ContentBlock(content_type="title", content="test")

    def test_content_block_empty_block_id(self):
        """ContentBlock에서 빈 block_id 시 ValidationError."""
        with pytest.raises(ValidationError):
            ContentBlock(block_id="", content_type="title", content="test")

    def test_slide_missing_title(self, sample_section: dict):
        """Slide에서 title 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            Slide(
                slide_index=0,
                role="cover",
                layout={"direction": "vertical", "sections": [sample_section]},
            )

    def test_slide_layout_empty_sections(self):
        """SlideLayout에서 빈 sections 시 ValidationError."""
        with pytest.raises(ValidationError):
            SlideLayout(direction="vertical", sections=[])

    def test_presentation_empty_slides(self, sample_style_guide: dict):
        """Presentation에서 빈 slides 시 ValidationError."""
        with pytest.raises(ValidationError):
            Presentation.model_validate({
                "meta": {
                    "title": "Test",
                    "total_slides": 0,
                    "generated_at": "2026-04-04T00:00:00",
                },
                "style_guide": sample_style_guide,
                "slides": [],
            })

    def test_presentation_missing_meta(
        self, sample_style_guide: dict, sample_slide: dict
    ):
        """Presentation에서 meta 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            Presentation.model_validate({
                "style_guide": sample_style_guide,
                "slides": [sample_slide],
            })

    def test_meta_missing_title(self):
        """PresentationMeta에서 title 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            PresentationMeta(total_slides=1)

    def test_meta_total_slides_zero(self):
        """PresentationMeta에서 total_slides가 0 이하이면 ValidationError."""
        with pytest.raises(ValidationError):
            PresentationMeta(title="test", total_slides=0)


# ===================================================================
# 3. 잘못된 Enum 값 테스트
# ===================================================================


class TestInvalidEnumValues:
    """잘못된 enum 값을 입력할 때 검증 실패를 확인."""

    def test_invalid_content_type(self):
        """존재하지 않는 content_type 값."""
        with pytest.raises(ValidationError):
            ContentBlock(
                block_id="test",
                content_type="invalid_type",
                content="test",
            )

    def test_invalid_slide_role(self, sample_section: dict):
        """존재하지 않는 role 값."""
        with pytest.raises(ValidationError):
            Slide(
                slide_index=0,
                role="invalid_role",
                title="test",
                layout={"direction": "vertical", "sections": [sample_section]},
            )

    def test_invalid_layout_direction(self, sample_section: dict):
        """존재하지 않는 layout direction 값."""
        with pytest.raises(ValidationError):
            SlideLayout(
                direction="diagonal",
                sections=[sample_section],
            )

    def test_invalid_alignment(self, sample_content_block: dict):
        """존재하지 않는 alignment 값."""
        with pytest.raises(ValidationError):
            Section(
                section_id="test",
                alignment="middle_left",
                content_blocks=[sample_content_block],
            )


# ===================================================================
# 4. JSON 직렬화 ↔ 역직렬화 라운드트립 테스트
# ===================================================================


class TestRoundTrip:
    """JSON 직렬화 후 역직렬화하면 동일한 모델이 복원되는지 확인."""

    def test_presentation_round_trip(self, sample_presentation: dict):
        """Presentation 전체의 직렬화/역직렬화 라운드트립."""
        # 생성
        original = Presentation.model_validate(sample_presentation)

        # 직렬화 → JSON 문자열
        json_str = original.model_dump_json()

        # 역직렬화 → 새 모델
        restored = Presentation.model_validate_json(json_str)

        # 비교 (generated_at은 타입 때문에 dump로 비교)
        assert original.model_dump() == restored.model_dump()

    def test_slide_round_trip(self, sample_slide: dict):
        """Slide 단일 라운드트립."""
        original = Slide.model_validate(sample_slide)
        json_str = original.model_dump_json()
        restored = Slide.model_validate_json(json_str)
        assert original.model_dump() == restored.model_dump()

    def test_style_guide_round_trip(self, sample_style_guide: dict):
        """StyleGuide 라운드트립."""
        original = StyleGuide.model_validate(sample_style_guide)
        json_str = original.model_dump_json()
        restored = StyleGuide.model_validate_json(json_str)
        assert original.model_dump() == restored.model_dump()


# ===================================================================
# 5. model_json_schema() export 테스트
# ===================================================================


class TestJsonSchemaExport:
    """model_json_schema()로 JSON Schema가 올바르게 생성되는지 확인."""

    def test_presentation_json_schema(self):
        """Presentation의 JSON Schema가 올바른 구조를 가져야 함."""
        schema = Presentation.model_json_schema()

        assert isinstance(schema, dict)
        assert schema.get("type") == "object"
        assert "properties" in schema
        assert "meta" in schema["properties"]
        assert "style_guide" in schema["properties"]
        assert "slides" in schema["properties"]

    def test_json_schema_serializable(self):
        """JSON Schema가 JSON으로 직렬화 가능해야 함."""
        schema = Presentation.model_json_schema()
        json_str = json.dumps(schema, indent=2, ensure_ascii=False)
        assert len(json_str) > 0

        # 역직렬화도 가능한지 확인
        parsed = json.loads(json_str)
        assert parsed == schema

    def test_json_schema_contains_definitions(self):
        """JSON Schema에 하위 모델들의 정의($defs)가 포함되어야 함."""
        schema = Presentation.model_json_schema()

        # Pydantic v2에서는 "$defs"에 하위 모델 정의가 들어감
        defs = schema.get("$defs", {})
        assert "ColorPalette" in defs
        assert "Typography" in defs
        assert "Spacing" in defs
        assert "ContentBlock" in defs
        assert "Section" in defs
        assert "Slide" in defs


# ===================================================================
# 6. 중첩 구조 테스트
# ===================================================================


class TestNestedStructure:
    """Slide → Section → ContentBlock 중첩 구조의 올바른 동작을 확인."""

    def test_multiple_sections_in_slide(self):
        """하나의 슬라이드에 여러 섹션이 포함되는 경우."""
        slide = Slide(
            slide_index=0,
            role=SlideRole.COMPARISON,
            title="기술 스택 비교",
            layout=SlideLayout(
                direction=LayoutDirection.HORIZONTAL,
                sections=[
                    Section(
                        section_id="left",
                        weight=1.0,
                        content_blocks=[
                            ContentBlock(
                                block_id="left_title",
                                content_type=ContentType.HEADING,
                                content="옵션 A",
                            ),
                        ],
                    ),
                    Section(
                        section_id="right",
                        weight=1.0,
                        content_blocks=[
                            ContentBlock(
                                block_id="right_title",
                                content_type=ContentType.HEADING,
                                content="옵션 B",
                            ),
                        ],
                    ),
                ],
            ),
        )
        assert len(slide.layout.sections) == 2
        assert slide.layout.sections[0].section_id == "left"
        assert slide.layout.sections[1].section_id == "right"

    def test_multiple_content_blocks_in_section(self):
        """하나의 섹션에 여러 콘텐츠 블록이 포함되는 경우."""
        section = Section(
            section_id="content_area",
            content_blocks=[
                ContentBlock(
                    block_id="heading",
                    content_type=ContentType.HEADING,
                    content="모듈 구조",
                ),
                ContentBlock(
                    block_id="body",
                    content_type=ContentType.BODY_TEXT,
                    content="이 모듈은 핵심 비즈니스 로직을 담당합니다.",
                ),
                ContentBlock(
                    block_id="code",
                    content_type=ContentType.CODE_BLOCK,
                    content="class MyService:\n    pass",
                    meta={"language": "python"},
                ),
            ],
        )
        assert len(section.content_blocks) == 3
        assert section.content_blocks[2].meta["language"] == "python"

    def test_full_multi_slide_presentation(self, sample_style_guide: dict):
        """여러 슬라이드를 가진 전체 프레젠테이션 구성."""
        data = {
            "meta": {
                "title": "Full Test",
                "total_slides": 3,
                "generated_at": "2026-04-04T00:00:00",
            },
            "style_guide": sample_style_guide,
            "slides": [
                {
                    "slide_index": 0,
                    "role": "cover",
                    "title": "커버",
                    "layout": {
                        "sections": [
                            {
                                "section_id": "main",
                                "content_blocks": [
                                    {
                                        "block_id": "t",
                                        "content_type": "title",
                                        "content": "제목",
                                    }
                                ],
                            }
                        ]
                    },
                },
                {
                    "slide_index": 1,
                    "role": "content",
                    "title": "본문",
                    "layout": {
                        "sections": [
                            {
                                "section_id": "body",
                                "content_blocks": [
                                    {
                                        "block_id": "b",
                                        "content_type": "body_text",
                                        "content": "내용",
                                    }
                                ],
                            }
                        ]
                    },
                },
                {
                    "slide_index": 2,
                    "role": "closing",
                    "title": "마무리",
                    "layout": {
                        "sections": [
                            {
                                "section_id": "end",
                                "content_blocks": [
                                    {
                                        "block_id": "e",
                                        "content_type": "title",
                                        "content": "감사합니다",
                                    }
                                ],
                            }
                        ]
                    },
                },
            ],
        }
        pres = Presentation.model_validate(data)
        assert len(pres.slides) == 3
        assert pres.slides[0].role == SlideRole.COVER
        assert pres.slides[1].role == SlideRole.CONTENT
        assert pres.slides[2].role == SlideRole.CLOSING


# ===================================================================
# 7. 엣지 케이스 테스트
# ===================================================================


class TestEdgeCases:
    """경계값 및 특수 상황 테스트."""

    def test_typography_min_max_font_size(self):
        """폰트 크기 최소/최대 경계값 검증."""
        # 최소값 — 정상
        typo = Typography(font_size_title=12, font_size_body=8)
        assert typo.font_size_title == 12

        # 최소값 미만 — 에러
        with pytest.raises(ValidationError):
            Typography(font_size_title=11)

    def test_section_weight_bounds(self):
        """섹션 가중치의 경계값 검증."""
        # 유효한 최대값
        section = Section(section_id="test", weight=10.0, content_blocks=[])
        assert section.weight == 10.0

        # 0 이하 — 에러
        with pytest.raises(ValidationError):
            Section(section_id="test", weight=0.0, content_blocks=[])

        # 10 초과 — 에러
        with pytest.raises(ValidationError):
            Section(section_id="test", weight=10.1, content_blocks=[])

    def test_slide_index_negative(self, sample_section: dict):
        """슬라이드 인덱스가 음수이면 ValidationError."""
        with pytest.raises(ValidationError):
            Slide(
                slide_index=-1,
                role="content",
                title="test",
                layout={"direction": "vertical", "sections": [sample_section]},
            )

    def test_content_block_style_overrides(self):
        """style_overrides 필드가 dict로 올바르게 동작하는지."""
        block = ContentBlock(
            block_id="styled",
            content_type=ContentType.BODY_TEXT,
            content="스타일 오버라이드 텍스트",
            style_overrides={
                "font_size": 20,
                "color": "#FF0000",
                "bold": True,
            },
        )
        assert block.style_overrides["font_size"] == 20
        assert block.style_overrides["bold"] is True

    def test_presentation_meta_generated_at_auto(self):
        """생성 시각이 자동으로 지정되는지 확인."""
        meta = PresentationMeta(title="auto time test", total_slides=1)
        assert isinstance(meta.generated_at, datetime)

    def test_all_content_types_valid(self):
        """모든 ContentType enum 값으로 ContentBlock 생성 가능."""
        for ct in ContentType:
            block = ContentBlock(
                block_id=f"block_{ct.value}",
                content_type=ct,
                content="test content",
            )
            assert block.content_type == ct

    def test_all_slide_roles_valid(self, sample_section: dict):
        """모든 SlideRole enum 값으로 Slide 생성 가능."""
        for idx, role in enumerate(SlideRole):
            slide = Slide(
                slide_index=idx,
                role=role,
                title=f"Test {role.value}",
                layout=SlideLayout(
                    direction=LayoutDirection.VERTICAL,
                    sections=[Section(**sample_section)],
                ),
            )
            assert slide.role == role

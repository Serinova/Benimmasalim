"""Pydantic models for Gemini story generation output.

Split from gemini_service.py for maintainability.
"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass
class PageContent(BaseModel):
    """Single page content with text and scene description (NO STYLE - style added later)."""

    page_number: int = Field(..., ge=0, le=64, description="Sayfa numarası (0=Kapak)")
    text: str = Field(..., min_length=10, description="Sayfa metni (Türkçe)")
    scene_description: str = Field(
        ..., min_length=50, description="Scene description (English) - NO STYLE!"
    )


class StoryResponse(BaseModel):
    """Complete story structure with all pages - AI-Director mode."""

    title: str = Field(..., min_length=3, description="Hikaye başlığı")
    pages: list[PageContent] = Field(..., min_length=3, description="Kapak + sayfalar")


class FinalPageContent(BaseModel):
    """Final page content ready for Fal.ai - with style composed."""

    page_number: int
    text: str
    scene_description: str  # Raw scene from Gemini (no style)
    visual_prompt: str = ""  # Final prompt = scene + style (composed once); empty if two-phase
    negative_prompt: str = ""  # V3: pre-built negative prompt (skip downstream recomposition)
    v3_composed: bool = False  # True when V3 pipeline already composed the prompt
    v3_enhancement_skipped: bool = False  # True when enhance_all_pages failed but page is still usable
    page_type: str = "inner"  # "cover" | "dedication" | "inner" | "backcover"
    page_index: int = 0  # 0-based position in the book (cover=0, first inner=1, ...)
    story_page_number: int | None = None  # 1-based story page (cover/dedication/backcover=None, inner=1..N)
    composer_version: str = "v3"  # V3 single source of truth
    pipeline_version: str = "v3"  # V3 single source of truth


class PageManifestEntry(BaseModel):
    """Single page entry in the book manifest."""

    page_type: str  # "cover" | "dedication" | "story" | "backcover"
    page_index: int  # 0-based position in the physical book
    story_page_number: int | None = None  # 1-based story number (None for non-story pages)
    story_text: str = ""  # Turkish text for this page
    image_prompt: str = ""  # V3 visual prompt
    negative_prompt: str = ""  # Negative prompt for image generation
    image_id: str = ""  # Filled after image generation
    composer_version: str = "v3"
    pipeline_version: str = "v3"
    prompt_hash: str = ""  # SHA-256 prefix for dedup/audit


class PageManifest(BaseModel):
    """Full book page manifest — single source of truth for page ordering.

    Standard V3 ordering:
        [0] Cover
        [1] Dedication
        [2..N+1] Story pages 1..N
        [N+2] Back cover

    Example for 22-page story:
        [0] cover, [1] dedication, [2..23] story 1..22, [24] backcover = 25 pages total
    """

    title: str
    child_name: str
    pipeline_version: str = "v3"
    style_tag: str = ""
    total_physical_pages: int = 0
    story_page_count: int = 0
    pages: list[PageManifestEntry] = Field(default_factory=list)

    # Traceability fields (filled by PipelineTracer)
    trace_id: str = ""
    scenario_id: str = ""
    style_id: str = ""
    value_id: str = ""
    seed: int | None = None
    provider: str = ""

    @classmethod
    def from_final_pages(
        cls,
        *,
        title: str,
        child_name: str,
        final_pages: list["FinalPageContent"],
        pipeline_version: str = "v3",
        style_tag: str = "",
        include_dedication: bool = True,
        include_backcover: bool = True,
    ) -> "PageManifest":
        """Build manifest from generated FinalPageContent list.

        Inserts dedication and back cover slots if requested.
        """
        entries: list[PageManifestEntry] = []
        idx = 0

        from app.core.pipeline_events import compute_prompt_hash

        # Extract AI-generated dedication text from front_matter page (if any)
        _ai_dedication_text = ""
        for fp in final_pages:
            if fp.page_type == "front_matter":
                _ai_dedication_text = fp.text or ""
                break

        _backcover_from_final: PageManifestEntry | None = None

        for fp in final_pages:
            # Skip front_matter pages — they're represented by the dedication slot
            if fp.page_type == "front_matter":
                continue
            # backcover collected separately; appended at end
            if fp.page_type == "backcover":
                _backcover_from_final = PageManifestEntry(
                    page_type="backcover",
                    page_index=0,  # filled below
                    story_page_number=None,
                    story_text="",
                    image_prompt=fp.visual_prompt,
                    negative_prompt=fp.negative_prompt,
                    composer_version=fp.composer_version,
                    pipeline_version=fp.pipeline_version,
                    prompt_hash=compute_prompt_hash(fp.visual_prompt) if fp.visual_prompt else "",
                )
                continue

            _phash = compute_prompt_hash(fp.visual_prompt) if fp.visual_prompt else ""
            if fp.page_type == "cover":
                entries.append(PageManifestEntry(
                    page_type="cover",
                    page_index=idx,
                    story_page_number=None,
                    story_text=fp.text,
                    image_prompt=fp.visual_prompt,
                    negative_prompt=fp.negative_prompt,
                    composer_version=fp.composer_version,
                    pipeline_version=fp.pipeline_version,
                    prompt_hash=_phash,
                ))
                idx += 1
                if include_dedication:
                    entries.append(PageManifestEntry(
                        page_type="dedication",
                        page_index=idx,
                        story_page_number=None,
                        story_text=_ai_dedication_text,
                        pipeline_version=fp.pipeline_version,
                    ))
                    idx += 1
            else:
                entries.append(PageManifestEntry(
                    page_type="story",
                    page_index=idx,
                    story_page_number=fp.story_page_number,
                    story_text=fp.text,
                    image_prompt=fp.visual_prompt,
                    negative_prompt=fp.negative_prompt,
                    composer_version=fp.composer_version,
                    pipeline_version=fp.pipeline_version,
                    prompt_hash=_phash,
                ))
                idx += 1

        if include_backcover:
            if _backcover_from_final is not None:
                # Use the AI-generated back cover prompt from V3 pipeline
                _backcover_from_final.page_index = idx
                entries.append(_backcover_from_final)
            else:
                entries.append(PageManifestEntry(
                    page_type="backcover",
                    page_index=idx,
                    story_page_number=None,
                    pipeline_version=pipeline_version,
                ))
            idx += 1

        story_count = sum(1 for e in entries if e.page_type == "story")
        return cls(
            title=title,
            child_name=child_name,
            pipeline_version=pipeline_version,
            style_tag=style_tag,
            total_physical_pages=len(entries),
            story_page_count=story_count,
            pages=entries,
        )



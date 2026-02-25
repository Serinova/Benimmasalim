"""Try Before You Buy - Trial Service.

Implements staged generation:
- Phase 1: Generate full story + 3 preview images (FREE)
- Phase 2: After payment, generate remaining 13 images

This reduces Fal.ai costs for non-paying users while capturing high-quality leads.
"""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story_preview import PreviewStatus, StoryPreview

logger = structlog.get_logger()


class TrialService:
    """Service for Try Before You Buy flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _compute_outcomes_hash(outcomes: list[str] | None) -> str:
        """
        Compute a hash of learning outcomes for cache invalidation.

        If outcomes change, the cache should be regenerated.

        Args:
            outcomes: List of learning outcome names

        Returns:
            Hash string
        """
        import hashlib

        if not outcomes:
            return "none"
        # Sort for consistency, join with separator
        sorted_outcomes = sorted(outcomes)
        content = "|".join(sorted_outcomes)
        return hashlib.md5(content.encode()).hexdigest()[:12]

    # =========================================================================
    # PHASE 0: Quick Lead Capture (no Gemini call — returns < 1s)
    # =========================================================================

    async def create_trial_lead(
        self,
        # Lead info
        lead_user_id: uuid.UUID | None,
        parent_name: str,
        parent_email: str,
        parent_phone: str | None,
        # Child info
        child_name: str,
        child_age: int,
        child_gender: str | None,
        # Product info
        product_id: uuid.UUID | None,
        product_name: str | None,
        product_price: float | None,
        # Story options (stored for async generation)
        scenario_name: str | None,
        visual_style_name: str | None,
        learning_outcomes: list[str] | None,
        # Photo (needed for image generation)
        child_photo_url: str | None = None,
        visual_style: str | None = None,
        scenario_id: str | None = None,
        page_count: int | None = None,
        magic_items: list[str] | None = None,
    ) -> StoryPreview:
        """Create a trial with LEAD_CAPTURED status — no story yet.

        Story generation is deferred to an Arq worker so the HTTP request
        returns in < 1 s.  The worker will call ``update_trial_story`` once
        Gemini finishes.
        """
        import secrets

        trial = StoryPreview(
            confirmation_token=secrets.token_urlsafe(32),
            status=PreviewStatus.LEAD_CAPTURED.value,
            is_preview_mode=True,
            # Lead info
            lead_user_id=lead_user_id,
            parent_name=parent_name,
            parent_email=parent_email,
            parent_phone=parent_phone,
            # Child info
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            child_photo_url=child_photo_url,
            # Product info
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            # Placeholder story data — will be filled by worker
            story_title=f"{child_name}'in Masalı",
            scenario_name=scenario_name,
            visual_style_name=visual_style_name,
            learning_outcomes=learning_outcomes,
            story_pages=[],
            generated_prompts_cache={
                "pending": True,
                "visual_style": visual_style,
                "scenario_id": scenario_id,
                "page_count": page_count,
                "magic_items": magic_items,
            },
            preview_images={},
            page_images={},
            generation_progress={
                "stage": "queued",
                "message": "Hikaye kuyruğa alındı...",
            },
            expires_at=datetime.now(UTC) + timedelta(hours=48),
        )

        self.db.add(trial)
        await self.db.commit()
        await self.db.refresh(trial)

        logger.info(
            "Trial lead created (story deferred to worker)",
            trial_id=str(trial.id),
            child_name=child_name,
        )

        return trial

    async def update_trial_story(
        self,
        trial_id: uuid.UUID,
        story_title: str,
        story_pages: list[dict],
        generated_prompts: list[dict],
        clothing_description: str | None = None,
        blueprint_json: dict | None = None,
        pipeline_version: str = "v3",
        page_manifest: dict | None = None,
        style_id: str | None = None,
        scenario_id: str | None = None,
        outcomes_hash: str | None = None,
    ) -> StoryPreview | None:
        """Populate story data after Gemini finishes (called from Arq worker)."""
        result = await self.db.execute(
            select(StoryPreview).where(StoryPreview.id == trial_id)
        )
        trial = result.scalar_one_or_none()
        if not trial:
            return None

        trial.story_title = story_title
        trial.story_pages = story_pages
        trial.generated_prompts_cache = {
            "style_id": style_id,
            "scenario_id": scenario_id,
            "outcomes_hash": outcomes_hash or self._compute_outcomes_hash(
                trial.learning_outcomes
            ),
            "prompts": generated_prompts,
            "clothing_description": clothing_description or "",
            "pipeline_version": pipeline_version,
            "blueprint_json": blueprint_json,
            "page_manifest": page_manifest,
        }
        trial.clothing_description = clothing_description
        trial.generation_progress = {
            "stage": "story_ready",
            "message": "Hikaye hazır, görseller oluşturuluyor...",
        }

        await self.db.commit()
        await self.db.refresh(trial)

        logger.info(
            "Trial story populated by worker",
            trial_id=str(trial_id),
            story_title=story_title,
            pages_count=len(story_pages),
        )
        return trial

    # =========================================================================
    # PHASE 1: Preview Generation (FREE - 3 images)
    # =========================================================================

    async def create_trial(
        self,
        # Lead info
        lead_user_id: uuid.UUID | None,
        parent_name: str,
        parent_email: str,
        parent_phone: str | None,
        # Child info
        child_name: str,
        child_age: int,
        child_gender: str | None,
        # Product info
        product_id: uuid.UUID | None,
        product_name: str | None,
        product_price: float | None,
        # Story info
        story_title: str,
        scenario_name: str | None,
        visual_style_name: str | None,
        learning_outcomes: list[str] | None,
        # Generated content (from Gemini)
        story_pages: list[dict],  # Full 16 pages with text
        generated_prompts: list[dict],  # Full 16 prompts for images
        # Cache invalidation keys
        scenario_id: str | None = None,
        style_id: str | None = None,
        # Photo & clothing (needed for Phase 2 remaining images)
        child_photo_url: str | None = None,
        clothing_description: str | None = None,
        # V3 audit data
        blueprint_json: dict | None = None,
        pipeline_version: str = "v3",
        page_manifest: dict | None = None,
    ) -> StoryPreview:
        """
        Create a new trial with LEAD_CAPTURED status.

        Args:
            lead_user_id: User ID from contact form
            parent_name: Parent's name
            parent_email: Parent's email
            parent_phone: Parent's phone
            child_name: Child's name
            child_age: Child's age
            child_gender: Child's gender
            product_id: Selected product ID
            product_name: Product name
            product_price: Product price
            story_title: Generated story title
            scenario_name: Selected scenario
            visual_style_name: Selected visual style
            learning_outcomes: Selected learning outcomes
            story_pages: Full story pages (text only)
            generated_prompts: Full visual prompts (16 prompts)

        Returns:
            Created StoryPreview instance
        """
        import secrets

        trial = StoryPreview(
            # Token for URL access
            confirmation_token=secrets.token_urlsafe(32),
            # Status - Lead captured, ready for preview generation
            status=PreviewStatus.LEAD_CAPTURED.value,
            is_preview_mode=True,
            # Lead info
            lead_user_id=lead_user_id,
            parent_name=parent_name,
            parent_email=parent_email,
            parent_phone=parent_phone,
            # Child info
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            child_photo_url=child_photo_url,
            # Product info
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            # Story info
            story_title=story_title,
            scenario_name=scenario_name,
            visual_style_name=visual_style_name,
            learning_outcomes=learning_outcomes,
            # Full story pages (text)
            story_pages=story_pages,
            # CRITICAL: Cache all prompts for later use
            # Includes style_id, scenario_id, and outcomes_hash for cache invalidation
            generated_prompts_cache={
                "style_id": style_id,
                "scenario_id": scenario_id,
                "outcomes_hash": self._compute_outcomes_hash(learning_outcomes),
                "prompts": generated_prompts,
                "clothing_description": clothing_description or "",
                "pipeline_version": pipeline_version,
                "blueprint_json": blueprint_json,
                "page_manifest": page_manifest,
            },
            # Preview images will be filled after generation
            preview_images={},
            page_images={},
            # Expiry
            expires_at=datetime.now(UTC) + timedelta(hours=48),
        )

        self.db.add(trial)
        await self.db.commit()
        await self.db.refresh(trial)

        logger.info(
            "Trial created",
            trial_id=str(trial.id),
            child_name=child_name,
            pages_count=len(story_pages),
            prompts_count=len(generated_prompts),
        )

        return trial

    async def update_to_generating(self, trial_id: uuid.UUID) -> StoryPreview | None:
        """Update trial status to GENERATING."""
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if trial:
            trial.status = PreviewStatus.GENERATING.value
            await self.db.commit()
            await self.db.refresh(trial)

        return trial

    async def save_preview_images(
        self,
        trial_id: uuid.UUID,
        preview_images: dict[int | str, str],  # {0: "url", 1: "url", 2: "url", "dedication": "url"}
    ) -> StoryPreview | None:
        """
        Save the 3 preview images and update status to PREVIEW_GENERATED.

        Args:
            trial_id: Trial UUID
            preview_images: Dict of page_number -> image_url for first 3 pages

        Returns:
            Updated StoryPreview or None if not found
        """
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if not trial:
            return None

        # Save preview images
        trial.preview_images = {str(k): v for k, v in preview_images.items()}

        # Also add to page_images for consistency
        # CRITICAL: dict copy — SQLAlchemy JSONB in-place mutation algilanmaz
        current_images = dict(trial.page_images) if trial.page_images else {}
        for page_num, url in preview_images.items():
            current_images[str(page_num)] = url
        trial.page_images = current_images

        # Update status
        trial.status = PreviewStatus.PREVIEW_GENERATED.value
        trial.preview_shown_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(trial)

        logger.info(
            "Preview images saved",
            trial_id=str(trial_id),
            images_count=len(preview_images),
        )

        return trial

    # =========================================================================
    # PHASE 2: Completion (PAID - remaining 13 images)
    # =========================================================================

    async def get_cached_prompts(self, trial_id: uuid.UUID) -> list[dict] | None:
        """
        Get cached prompts for completion (DO NOT call Gemini again!).

        Returns:
            List of prompt dicts or None if not found
        """
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if not trial or not trial.generated_prompts_cache:
            return None

        return trial.generated_prompts_cache.get("prompts", [])

    async def get_remaining_prompts(self, trial_id: uuid.UUID) -> list[dict]:
        """
        Get prompts for pages 4-16 (remaining 13 images to generate).

        Returns:
            List of prompt dicts for pages not yet generated
        """
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if not trial or not trial.generated_prompts_cache:
            return []

        all_prompts = trial.generated_prompts_cache.get("prompts", [])
        generated_pages = set(trial.page_images.keys() if trial.page_images else [])

        # Return prompts for pages not yet generated
        remaining = []
        for prompt in all_prompts:
            page_num = str(prompt.get("page_number", ""))
            if page_num not in generated_pages:
                remaining.append(prompt)

        logger.info(
            "Getting remaining prompts",
            trial_id=str(trial_id),
            total_prompts=len(all_prompts),
            generated=len(generated_pages),
            remaining=len(remaining),
        )

        return remaining

    async def initiate_payment(self, trial_id: uuid.UUID) -> StoryPreview | None:
        """Update status to PAYMENT_PENDING when user clicks 'Buy'."""
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if trial:
            trial.status = PreviewStatus.PAYMENT_PENDING.value
            trial.payment_initiated_at = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(trial)

        return trial

    async def complete_payment(
        self,
        trial_id: uuid.UUID,
        payment_reference: str,
    ) -> StoryPreview | None:
        """
        Mark payment as completed and start completion phase.

        Args:
            trial_id: Trial UUID
            payment_reference: Payment transaction reference

        Returns:
            Updated StoryPreview
        """
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if trial:
            trial.status = PreviewStatus.COMPLETING.value
            trial.payment_completed_at = datetime.now(UTC)
            trial.payment_reference = payment_reference
            trial.is_preview_mode = False  # Now generating full book
            await self.db.commit()
            await self.db.refresh(trial)

            logger.info(
                "Payment completed, starting full generation",
                trial_id=str(trial_id),
                payment_reference=payment_reference,
            )

        return trial

    async def save_remaining_images(
        self,
        trial_id: uuid.UUID,
        images: dict[int, str],  # {page_num: url}
    ) -> StoryPreview | None:
        """
        Save remaining images and mark as COMPLETED.

        Args:
            trial_id: Trial UUID
            images: Dict of page_number -> image_url

        Returns:
            Updated StoryPreview
        """
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if not trial:
            return None

        # Add to existing page_images
        # CRITICAL: dict.copy() — SQLAlchemy JSONB kolon degisikligi algılamaz
        # eger ayni referans geri atanirsa. Yeni dict olusturulmali.
        current_images = dict(trial.page_images) if trial.page_images else {}
        for page_num, url in images.items():
            current_images[str(page_num)] = url
        trial.page_images = current_images

        # Mark as completed
        trial.status = PreviewStatus.COMPLETED.value
        trial.confirmed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(trial)

        logger.info(
            "Trial completed",
            trial_id=str(trial_id),
            total_images=len(current_images),
        )

        return trial

    # =========================================================================
    # ABANDONMENT TRACKING
    # =========================================================================

    async def mark_abandoned_trials(self, hours: int = 1) -> int:
        """
        Mark trials as abandoned if preview was shown but no payment after X hours.

        Args:
            hours: Hours after preview_shown_at to mark as abandoned

        Returns:
            Number of trials marked as abandoned
        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        result = await self.db.execute(
            update(StoryPreview)
            .where(
                StoryPreview.status == PreviewStatus.PREVIEW_GENERATED.value,
                StoryPreview.preview_shown_at < cutoff,
                StoryPreview.abandoned_at.is_(None),
            )
            .values(
                status=PreviewStatus.ABANDONED_TRIAL.value,
                abandoned_at=datetime.now(UTC),
            )
            .returning(StoryPreview.id)
        )

        abandoned_ids = result.scalars().all()
        await self.db.commit()

        if abandoned_ids:
            logger.info(
                "Marked trials as abandoned",
                count=len(abandoned_ids),
                trial_ids=[str(id) for id in abandoned_ids],
            )

        return len(abandoned_ids)

    async def mark_abandoned_previews(self, hours: int = 24) -> int:
        """
        Mark StoryPreview records as abandoned if they are in PENDING status
        (3 preview images generated, confirmation email sent) but user never
        clicked the confirmation link within `hours`.

        This handles the "orders/submit-preview-async" flow where previews stay
        in PENDING status until the user clicks the email confirmation link.

        Args:
            hours: Hours after creation to mark as abandoned (default 24h)

        Returns:
            Number of previews marked as abandoned
        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        result = await self.db.execute(
            update(StoryPreview)
            .where(
                StoryPreview.status == PreviewStatus.PENDING.value,
                StoryPreview.created_at < cutoff,
                StoryPreview.abandoned_at.is_(None),
                StoryPreview.confirmed_at.is_(None),
            )
            .values(
                status=PreviewStatus.ABANDONED_TRIAL.value,
                abandoned_at=datetime.now(UTC),
            )
            .returning(StoryPreview.id)
        )

        abandoned_ids = result.scalars().all()
        await self.db.commit()

        if abandoned_ids:
            logger.info(
                "Marked previews as abandoned (no confirmation within deadline)",
                count=len(abandoned_ids),
                preview_ids=[str(pid) for pid in abandoned_ids],
                hours=hours,
            )

        return len(abandoned_ids)

    async def get_abandoned_trials(
        self,
        limit: int = 50,
        offset: int = 0,
        include_followed_up: bool = False,
    ) -> list[StoryPreview]:
        """
        Get abandoned trials for admin follow-up.

        Includes:
        - ABANDONED_TRIAL status records (new flow)
        - PENDING status records older than 1 hour (old flow - didn't complete payment)

        Args:
            limit: Max number of results
            offset: Pagination offset
            include_followed_up: Include trials already followed up

        Returns:
            List of abandoned StoryPreview instances
        """
        from sqlalchemy import or_

        # Include both new ABANDONED_TRIAL and old PENDING records (not confirmed)
        cutoff = datetime.now(UTC) - timedelta(hours=1)

        query = select(StoryPreview).where(
            or_(
                # New flow: Explicitly marked as abandoned
                StoryPreview.status == PreviewStatus.ABANDONED_TRIAL.value,
                # Old flow: PENDING and older than 1 hour (didn't pay)
                (StoryPreview.status == PreviewStatus.PENDING.value)
                & (StoryPreview.created_at < cutoff),
            )
        )

        if not include_followed_up:
            query = query.where(StoryPreview.followed_up_at.is_(None))

        query = query.order_by(StoryPreview.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_followed_up(
        self,
        trial_id: uuid.UUID,
        admin_email: str,
        notes: str | None = None,
    ) -> StoryPreview | None:
        """
        Mark trial as followed up by admin.

        Args:
            trial_id: Trial UUID
            admin_email: Admin who followed up
            notes: Follow-up notes

        Returns:
            Updated StoryPreview
        """
        result = await self.db.execute(select(StoryPreview).where(StoryPreview.id == trial_id))
        trial = result.scalar_one_or_none()

        if trial:
            trial.followed_up_at = datetime.now(UTC)
            trial.followed_up_by = admin_email
            trial.follow_up_notes = notes
            await self.db.commit()
            await self.db.refresh(trial)

            logger.info(
                "Trial marked as followed up",
                trial_id=str(trial_id),
                admin=admin_email,
            )

        return trial

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_trial_stats(self) -> dict:
        """Get trial statistics for dashboard."""
        from sqlalchemy import func

        # Count by status
        status_counts = await self.db.execute(
            select(StoryPreview.status, func.count(StoryPreview.id)).group_by(StoryPreview.status)
        )

        stats = {
            "by_status": dict(status_counts.all()),
            "total_leads": 0,
            "preview_shown": 0,
            "converted": 0,
            "abandoned": 0,
            "conversion_rate": 0.0,
        }

        stats["total_leads"] = sum(stats["by_status"].values())
        stats["preview_shown"] = stats["by_status"].get(PreviewStatus.PREVIEW_GENERATED.value, 0)
        stats["converted"] = stats["by_status"].get(PreviewStatus.COMPLETED.value, 0)
        stats["abandoned"] = stats["by_status"].get(PreviewStatus.ABANDONED_TRIAL.value, 0)

        if stats["preview_shown"] > 0:
            stats["conversion_rate"] = round(stats["converted"] / stats["preview_shown"] * 100, 2)

        return stats


# Singleton-like factory
def get_trial_service(db: AsyncSession) -> TrialService:
    """Get trial service instance."""
    return TrialService(db)

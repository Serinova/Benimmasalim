"""Admin learning outcomes management endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import DbSession, SuperAdminUser
from app.core.exceptions import ConflictError, NotFoundError
from app.models.learning_outcome import LearningOutcome
from app.models.prompt_template import PromptTemplate

logger = structlog.get_logger()
router = APIRouter()


# ============ SYNC HELPERS ============


def normalize_key(name: str) -> str:
    """Normalize a name to a key for prompt templates."""
    # Turkish char mapping
    tr_map = {
        "ş": "s",
        "Ş": "S",
        "ı": "i",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ü": "u",
        "Ü": "U",
        "ğ": "g",
        "Ğ": "G",
        "ç": "c",
        "Ç": "C",
    }
    key = name.lower()
    for tr, en in tr_map.items():
        key = key.replace(tr, en.lower())
    # Remove special chars, keep alphanumeric and underscore
    key = "".join(c if c.isalnum() or c == "_" else "_" for c in key)
    # Remove multiple underscores
    while "__" in key:
        key = key.replace("__", "_")
    return key.strip("_")


async def sync_create_prompt_for_outcome(
    db: AsyncSession,
    outcome: LearningOutcome,
    admin_email: str,
) -> PromptTemplate | None:
    """
    Create a corresponding prompt template when a learning outcome is created.
    Returns the created prompt or None if it already exists.
    """
    key = f"EDUCATIONAL_{normalize_key(outcome.name)}"

    # Check if prompt already exists
    existing = await db.execute(select(PromptTemplate).where(PromptTemplate.key == key))
    if existing.scalar_one_or_none():
        logger.info("Prompt already exists for outcome", outcome_name=outcome.name, key=key)
        return None

    # Build prompt content from outcome
    theme = outcome.name.upper()
    instruction = (
        outcome.ai_prompt_instruction
        or outcome.ai_prompt
        or f"Çocuk '{outcome.name}' konusunda bir deneyim yaşamalı."
    )

    content = f"""⭐ {theme}

{instruction}"""

    prompt = PromptTemplate(
        key=key,
        name=outcome.name,
        category="educational",
        description=f"Eğitsel değer promptu: {outcome.name}",
        content=content,
        version=1,
        is_active=outcome.is_active,
        modified_by=admin_email,
    )

    db.add(prompt)
    logger.info("Created prompt for learning outcome", outcome_name=outcome.name, prompt_key=key)
    return prompt


async def sync_update_prompt_for_outcome(
    db: AsyncSession,
    outcome: LearningOutcome,
    admin_email: str,
) -> PromptTemplate | None:
    """
    Update the corresponding prompt template when a learning outcome is updated.
    """
    key = f"EDUCATIONAL_{normalize_key(outcome.name)}"

    result = await db.execute(select(PromptTemplate).where(PromptTemplate.key == key))
    prompt = result.scalar_one_or_none()

    if not prompt:
        # If prompt doesn't exist, create it
        return await sync_create_prompt_for_outcome(db, outcome, admin_email)

    # Update prompt content
    theme = outcome.name.upper()
    instruction = (
        outcome.ai_prompt_instruction
        or outcome.ai_prompt
        or f"Çocuk '{outcome.name}' konusunda bir deneyim yaşamalı."
    )

    prompt.content = f"""⭐ {theme}

{instruction}"""
    prompt.name = outcome.name
    prompt.description = f"Eğitsel değer promptu: {outcome.name}"
    prompt.is_active = outcome.is_active
    prompt.modified_by = admin_email
    prompt.version += 1

    logger.info("Updated prompt for learning outcome", outcome_name=outcome.name, prompt_key=key)
    return prompt


async def get_linked_prompt_key(outcome_name: str) -> str:
    """Get the expected prompt key for a learning outcome."""
    return f"EDUCATIONAL_{normalize_key(outcome_name)}"


# ============ PYDANTIC SCHEMAS ============


class LearningOutcomeCreate(BaseModel):
    """Create learning outcome request."""

    # Basic Info
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

    # UI Visual Assets
    icon_url: str | None = Field(None, description="URL of icon (SVG/PNG)")
    color_theme: str | None = Field(
        None, max_length=20, description="Hex color code (e.g., #FF5733)"
    )

    # AI Logic
    ai_prompt_instruction: str | None = Field(
        None, description="Exact AI instruction with {child_name} placeholder"
    )
    ai_prompt: str | None = Field(None, description="Legacy AI prompt field")

    # V2: banned words
    banned_words_tr: str | None = Field(
        None,
        description="V2: Comma-separated TR words banned from story output (e.g. 'anne,baba,aile')",
    )

    # Categorization
    category: str = Field(..., max_length=50)
    category_label: str | None = Field(None, max_length=100)
    age_group: str = Field(default="3-10", max_length=20)

    # Display Settings
    display_order: int = 0
    is_active: bool = True

    @field_validator("color_theme")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        """Validate hex color format."""
        if v is None:
            return v
        v = v.strip()
        if not v.startswith("#"):
            v = f"#{v}"
        if len(v) not in (4, 7):  # #RGB or #RRGGBB
            raise ValueError("Invalid hex color format. Use #RGB or #RRGGBB")
        return v.upper()


class LearningOutcomeUpdate(BaseModel):
    """Update learning outcome request."""

    name: str | None = None
    description: str | None = None
    icon_url: str | None = None
    color_theme: str | None = None
    ai_prompt_instruction: str | None = None
    ai_prompt: str | None = None
    banned_words_tr: str | None = None
    category: str | None = None
    category_label: str | None = None
    age_group: str | None = None
    display_order: int | None = None
    is_active: bool | None = None

    @field_validator("color_theme")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        """Validate hex color format."""
        if v is None:
            return v
        v = v.strip()
        if not v.startswith("#"):
            v = f"#{v}"
        if len(v) not in (4, 7):
            raise ValueError("Invalid hex color format. Use #RGB or #RRGGBB")
        return v.upper()


class LearningOutcomeResponse(BaseModel):
    """Full learning outcome response."""

    id: str
    name: str
    description: str | None

    # UI Assets
    icon_url: str | None
    color_theme: str | None

    # AI Logic
    ai_prompt: str | None
    ai_prompt_instruction: str | None
    effective_ai_instruction: str | None
    banned_words_tr: str | None = None

    # Categorization
    category: str
    category_label: str | None
    age_group: str

    # Display
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class LearningOutcomeBulkUpdate(BaseModel):
    """Bulk update for reordering outcomes."""

    items: list[dict]  # [{"id": "uuid", "display_order": 1}, ...]


# ============ HELPER FUNCTIONS ============


def outcome_to_response(outcome: LearningOutcome) -> dict:
    """Convert LearningOutcome model to response dict."""
    return {
        "id": str(outcome.id),
        "name": outcome.name,
        "description": outcome.description,
        # UI Assets
        "icon_url": outcome.icon_url,
        "color_theme": outcome.color_theme,
        # AI Logic
        "ai_prompt": outcome.ai_prompt,
        "ai_prompt_instruction": outcome.ai_prompt_instruction,
        "effective_ai_instruction": outcome.effective_ai_instruction,
        "banned_words_tr": getattr(outcome, "banned_words_tr", None),
        # Categorization
        "category": outcome.category,
        "category_label": outcome.category_label,
        "age_group": outcome.age_group,
        # Display
        "display_order": outcome.display_order,
        "is_active": outcome.is_active,
    }


# ============ ENDPOINTS ============


@router.get("")
async def list_learning_outcomes(
    db: DbSession,
    admin: SuperAdminUser,
    include_inactive: bool = Query(default=True, description="Include inactive outcomes"),
    category: str | None = Query(default=None, description="Filter by category"),
) -> list[dict]:
    """List all learning outcomes (admin view with all fields)."""
    query = select(LearningOutcome).order_by(
        LearningOutcome.category, LearningOutcome.display_order, LearningOutcome.name
    )

    if not include_inactive:
        query = query.where(LearningOutcome.is_active == True)

    if category:
        query = query.where(LearningOutcome.category == category)

    result = await db.execute(query)
    outcomes = result.scalars().all()

    return [outcome_to_response(o) for o in outcomes]


@router.get("/categories")
async def list_categories(
    db: DbSession,
    admin: SuperAdminUser,
) -> list[dict]:
    """List all unique categories with their labels."""
    result = await db.execute(
        select(LearningOutcome.category, LearningOutcome.category_label)
        .distinct()
        .order_by(LearningOutcome.category)
    )
    rows = result.all()

    return [{"category": row.category, "category_label": row.category_label} for row in rows]


@router.get("/{outcome_id}")
async def get_learning_outcome(
    outcome_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Get a single learning outcome with full details."""
    result = await db.execute(select(LearningOutcome).where(LearningOutcome.id == outcome_id))
    outcome = result.scalar_one_or_none()

    if not outcome:
        raise NotFoundError("Kazanım", outcome_id)

    # Check for linked prompt
    prompt_key = await get_linked_prompt_key(outcome.name)
    prompt_result = await db.execute(select(PromptTemplate).where(PromptTemplate.key == prompt_key))
    linked_prompt = prompt_result.scalar_one_or_none()

    return {
        **outcome_to_response(outcome),
        "linked_prompt_key": prompt_key,
        "linked_prompt_exists": linked_prompt is not None,
        "linked_prompt_id": str(linked_prompt.id) if linked_prompt else None,
    }


@router.post("")
async def create_learning_outcome(
    request: LearningOutcomeCreate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Create a new learning outcome."""
    # Check for duplicate name
    result = await db.execute(select(LearningOutcome).where(LearningOutcome.name == request.name))
    if result.scalar_one_or_none():
        raise ConflictError(f"'{request.name}' adında bir kazanım zaten var")

    outcome = LearningOutcome(
        name=request.name,
        description=request.description,
        # UI Assets
        icon_url=request.icon_url,
        color_theme=request.color_theme,
        # AI Logic
        ai_prompt=request.ai_prompt,
        ai_prompt_instruction=request.ai_prompt_instruction,
        banned_words_tr=request.banned_words_tr,
        # Categorization
        category=request.category,
        category_label=request.category_label,
        age_group=request.age_group,
        # Display
        display_order=request.display_order,
        is_active=request.is_active,
    )

    db.add(outcome)

    # SYNC: Create corresponding prompt template
    prompt = await sync_create_prompt_for_outcome(db, outcome, admin.email)
    prompt_key = await get_linked_prompt_key(outcome.name)

    await db.commit()
    await db.refresh(outcome)

    logger.info(
        "Learning outcome created",
        outcome_id=str(outcome.id),
        name=outcome.name,
        category=outcome.category,
        synced_prompt=prompt_key if prompt else None,
    )

    return {
        **outcome_to_response(outcome),
        "linked_prompt_key": prompt_key,
        "prompt_created": prompt is not None,
        "message": "Kazanım oluşturuldu" + (" ve prompt şablonu eklendi" if prompt else ""),
    }


@router.patch("/{outcome_id}")
async def update_learning_outcome(
    outcome_id: UUID,
    request: LearningOutcomeUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Update a learning outcome."""
    result = await db.execute(select(LearningOutcome).where(LearningOutcome.id == outcome_id))
    outcome = result.scalar_one_or_none()

    if not outcome:
        raise NotFoundError("Kazanım", outcome_id)

    # Check name conflict if changing
    if request.name and request.name != outcome.name:
        existing = await db.execute(
            select(LearningOutcome).where(LearningOutcome.name == request.name)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"'{request.name}' adında bir kazanım zaten var")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(outcome, field, value)

    # SYNC: Update corresponding prompt template if AI fields changed
    prompt_synced = False
    if any(f in update_data for f in ["ai_prompt", "ai_prompt_instruction", "name", "is_active"]):
        await sync_update_prompt_for_outcome(db, outcome, admin.email)
        prompt_synced = True

    await db.commit()
    await db.refresh(outcome)

    prompt_key = await get_linked_prompt_key(outcome.name)

    logger.info(
        "Learning outcome updated",
        outcome_id=str(outcome_id),
        updated_fields=list(update_data.keys()),
        prompt_synced=prompt_synced,
    )

    return {
        **outcome_to_response(outcome),
        "linked_prompt_key": prompt_key,
        "prompt_synced": prompt_synced,
        "message": "Kazanım güncellendi"
        + (" ve prompt senkronize edildi" if prompt_synced else ""),
    }


@router.delete("/{outcome_id}")
async def delete_learning_outcome(
    outcome_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
    hard_delete: bool = Query(default=False, description="Permanently delete"),
) -> dict:
    """Delete a learning outcome (soft delete by default)."""
    result = await db.execute(select(LearningOutcome).where(LearningOutcome.id == outcome_id))
    outcome = result.scalar_one_or_none()

    if not outcome:
        raise NotFoundError("Kazanım", outcome_id)

    if hard_delete:
        await db.delete(outcome)
        await db.commit()
        logger.info("Learning outcome hard-deleted", outcome_id=str(outcome_id))
        return {"message": "Kazanım kalıcı olarak silindi"}
    else:
        outcome.is_active = False
        await db.commit()
        logger.info("Learning outcome soft-deleted", outcome_id=str(outcome_id))
        return {"message": "Kazanım devre dışı bırakıldı"}


@router.post("/{outcome_id}/duplicate")
async def duplicate_learning_outcome(
    outcome_id: UUID,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Duplicate a learning outcome."""
    result = await db.execute(select(LearningOutcome).where(LearningOutcome.id == outcome_id))
    original = result.scalar_one_or_none()

    if not original:
        raise NotFoundError("Kazanım", outcome_id)

    # Generate unique name
    base_name = f"{original.name} (Kopya)"
    new_name = base_name
    counter = 1

    while True:
        existing = await db.execute(select(LearningOutcome).where(LearningOutcome.name == new_name))
        if not existing.scalar_one_or_none():
            break
        counter += 1
        new_name = f"{base_name} {counter}"

    duplicate = LearningOutcome(
        name=new_name,
        description=original.description,
        icon_url=original.icon_url,
        color_theme=original.color_theme,
        ai_prompt=original.ai_prompt,
        ai_prompt_instruction=original.ai_prompt_instruction,
        category=original.category,
        category_label=original.category_label,
        age_group=original.age_group,
        display_order=original.display_order + 1,
        is_active=False,  # Start as draft
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    logger.info(
        "Learning outcome duplicated",
        original_id=str(outcome_id),
        duplicate_id=str(duplicate.id),
    )

    return {
        **outcome_to_response(duplicate),
        "message": f"Kazanım '{new_name}' olarak kopyalandı",
    }


@router.post("/reorder")
async def reorder_learning_outcomes(
    request: LearningOutcomeBulkUpdate,
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """Bulk update display order for learning outcomes."""
    updated_count = 0

    for item in request.items:
        outcome_id = item.get("id")
        new_order = item.get("display_order")

        if outcome_id and new_order is not None:
            result = await db.execute(
                select(LearningOutcome).where(LearningOutcome.id == UUID(outcome_id))
            )
            outcome = result.scalar_one_or_none()
            if outcome:
                outcome.display_order = new_order
                updated_count += 1

    await db.commit()

    logger.info("Learning outcomes reordered", count=updated_count)

    return {
        "message": f"{updated_count} kazanım sıralaması güncellendi",
        "updated_count": updated_count,
    }


@router.get("/sync/status")
async def get_sync_status(
    db: DbSession,
    admin: SuperAdminUser,
) -> dict:
    """
    Analyze sync status between learning_outcomes and prompt_templates.
    Shows which outcomes have prompts and which prompts are orphaned.
    """
    # Get all learning outcomes
    result = await db.execute(
        select(LearningOutcome).order_by(LearningOutcome.category, LearningOutcome.name)
    )
    outcomes = result.scalars().all()

    # Get all educational prompts
    result = await db.execute(
        select(PromptTemplate)
        .where(PromptTemplate.category == "educational")
        .order_by(PromptTemplate.key)
    )
    prompts = result.scalars().all()

    # Build mappings
    outcome_data = []
    for o in outcomes:
        expected_key = f"EDUCATIONAL_{normalize_key(o.name)}"
        has_prompt = any(p.key == expected_key for p in prompts)
        outcome_data.append(
            {
                "id": str(o.id),
                "name": o.name,
                "category": o.category,
                "expected_prompt_key": expected_key,
                "has_prompt": has_prompt,
            }
        )

    # Find orphan prompts (no matching outcome)
    outcome_keys = {f"EDUCATIONAL_{normalize_key(o.name)}" for o in outcomes}
    orphan_prompts = []
    for p in prompts:
        if p.key not in outcome_keys:
            orphan_prompts.append(
                {
                    "id": str(p.id),
                    "key": p.key,
                    "name": p.name,
                    "is_active": p.is_active,
                }
            )

    return {
        "total_outcomes": len(outcomes),
        "total_educational_prompts": len(prompts),
        "outcomes_with_prompt": sum(1 for o in outcome_data if o["has_prompt"]),
        "outcomes_without_prompt": sum(1 for o in outcome_data if not o["has_prompt"]),
        "orphan_prompts": len(orphan_prompts),
        "outcomes": outcome_data,
        "orphan_prompt_list": orphan_prompts,
    }


@router.post("/sync/execute")
async def execute_sync(
    db: DbSession,
    admin: SuperAdminUser,
    delete_orphans: bool = Query(default=True, description="Delete orphan prompts"),
    create_missing: bool = Query(default=True, description="Create missing prompts"),
) -> dict:
    """
    Execute sync between learning_outcomes and prompt_templates.

    - Deletes orphan prompts (educational prompts without matching outcome)
    - Creates missing prompts for outcomes that don't have one
    """
    # Get all learning outcomes
    result = await db.execute(select(LearningOutcome))
    outcomes = result.scalars().all()

    # Get all educational prompts
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.category == "educational")
    )
    prompts = result.scalars().all()

    # Build mappings
    outcome_keys = {f"EDUCATIONAL_{normalize_key(o.name)}": o for o in outcomes}
    prompt_keys = {p.key: p for p in prompts}

    deleted_prompts = []
    created_prompts = []

    # Delete orphan prompts
    if delete_orphans:
        for key, prompt in prompt_keys.items():
            if key not in outcome_keys:
                deleted_prompts.append(prompt.key)
                await db.delete(prompt)
                logger.info("Deleted orphan prompt", key=prompt.key)

    # Create missing prompts
    if create_missing:
        for key, outcome in outcome_keys.items():
            if key not in prompt_keys:
                # Build prompt content
                theme = outcome.name.upper()
                instruction = (
                    outcome.ai_prompt_instruction
                    or outcome.ai_prompt
                    or f"Hikayede çocuk '{outcome.name}' konusunu deneyimlesin."
                )
                content = f"""⭐ {theme}

{instruction}"""

                prompt = PromptTemplate(
                    key=key,
                    name=outcome.name,
                    category="educational",
                    description=f"Eğitsel değer promptu: {outcome.name}",
                    content=content,
                    version=1,
                    is_active=outcome.is_active,
                    modified_by=admin.email,
                )
                db.add(prompt)
                created_prompts.append(key)
                logger.info("Created prompt for outcome", outcome=outcome.name, key=key)

    await db.commit()

    logger.info(
        "Sync executed",
        deleted=len(deleted_prompts),
        created=len(created_prompts),
    )

    return {
        "success": True,
        "deleted_prompts": deleted_prompts,
        "created_prompts": created_prompts,
        "message": f"{len(deleted_prompts)} orphan prompt silindi, {len(created_prompts)} yeni prompt oluşturuldu",
    }

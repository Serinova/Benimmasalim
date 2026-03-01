"""Iyzico payment helpers for the Trial (Try Before You Buy) flow.

These functions contain the Iyzico SDK logic extracted from the API router
so the endpoint handlers stay thin.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.story_preview import PreviewStatus, StoryPreview

logger = structlog.get_logger()


def norm_iyzico_host(url: str | None) -> str:
    """Iyzico SDK için sadece hostname (şema/path/baştaki // yok). 'nonnumeric port' hatasını önler."""
    raw = (url or "sandbox-api.iyzipay.com").strip()
    host = raw.removeprefix("https://").removeprefix("http://").strip("/").split("/")[0]
    return host or "sandbox-api.iyzipay.com"


def get_iyzico_options() -> dict[str, str]:
    """Return iyzico SDK options dict, validated.

    Raises:
        ValueError: If API key or secret key is not configured.
    """
    s = get_settings()
    if not s.iyzico_api_key or not s.iyzico_secret_key:
        raise ValueError("Ödeme sistemi yapılandırılmamış")
    return {
        "api_key": s.iyzico_api_key,
        "secret_key": s.iyzico_secret_key,
        "base_url": norm_iyzico_host(s.iyzico_base_url),
    }


async def resolve_trial_price(
    trial: StoryPreview,
    db: AsyncSession,
) -> Decimal:
    """Resolve the base book price for a trial, using multiple fallback strategies."""
    from app.models.product import Product
    from app.models.scenario import Scenario

    if trial.product_price and Decimal(str(trial.product_price)) > Decimal("0"):
        logger.info("Price from trial.product_price", price=str(trial.product_price))
        return Decimal(str(trial.product_price))

    trial_product_id = getattr(trial, "product_id", None)
    if trial_product_id:
        try:
            prod_result = await db.execute(select(Product).where(Product.id == trial_product_id))
            prod_obj = prod_result.scalar_one_or_none()
            if prod_obj and (prod_obj.base_price is not None or prod_obj.discounted_price is not None):
                price = Decimal(str(prod_obj.discounted_price or prod_obj.base_price))
                logger.info(
                    "trial.product_price resolved via trial.product_id",
                    trial_id=str(trial.id),
                    product_id=str(trial_product_id),
                    resolved_price=str(price),
                )
                return price
        except Exception:
            pass

    try:
        scenario_name = getattr(trial, "scenario_name", None)
        scenario_obj = None
        if scenario_name:
            sc_result = await db.execute(
                select(Scenario).where(Scenario.name == scenario_name).limit(1)
            )
            scenario_obj = sc_result.scalar_one_or_none()

        if scenario_obj:
            from app.services.order_config_service import get_effective_order_config
            config = await get_effective_order_config(
                db,
                product_id=str(scenario_obj.linked_product_id) if getattr(scenario_obj, "linked_product_id", None) else None,
                scenario_id=str(scenario_obj.id),
            )
            if config.base_price > Decimal("0"):
                logger.info(
                    "trial.product_price resolved via scenario/linked_product",
                    trial_id=str(trial.id),
                    scenario_name=scenario_name,
                    resolved_price=str(config.base_price),
                    price_source=config.price_source,
                )
                return config.base_price
            raise ValueError(
                f"Scenario has no price (linked_product_id={getattr(scenario_obj, 'linked_product_id', None)}, "
                f"price_source={config.price_source})"
            )
        raise ValueError(f"No scenario found for name: {scenario_name!r}")

    except Exception as _cfg_err:
        try:
            from app.models.product import Product
            prod_result = await db.execute(
                select(Product).where(Product.slug == "a4-yatay").limit(1)
            )
            product_obj = prod_result.scalar_one_or_none()
            if product_obj and product_obj.base_price:
                price = Decimal(str(product_obj.base_price))
                logger.warning(
                    "Price resolved via a4-yatay product fallback",
                    trial_id=str(trial.id),
                    price=str(price),
                    original_error=str(_cfg_err),
                )
                return price
            raise ValueError("a4-yatay product not found")
        except Exception as _prod_err:
            logger.error(
                "ALL price fallbacks failed — using hardcoded 1250 TL",
                trial_id=str(trial.id),
                scenario_error=str(_cfg_err),
                product_error=str(_prod_err),
            )
            return Decimal("1250")


def build_iyzico_buyer(
    trial: StoryPreview,
    client_ip: str,
) -> dict[str, Any]:
    """Build Iyzico buyer dict from trial data."""
    buyer_name = (trial.parent_name or "Misafir Kullanıcı").strip()
    buyer_email = (trial.parent_email or "misafir@benimmasalim.com").strip()
    buyer_phone = (trial.parent_phone or "").strip()
    name_parts = buyer_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else "Misafir"
    last_name = name_parts[1] if len(name_parts) > 1 else "."

    buyer: dict[str, Any] = {
        "id": str(trial.id),
        "name": first_name,
        "surname": last_name,
        "email": buyer_email,
        "identityNumber": "11111111111",
        "registrationAddress": "Adres belirtilmedi",
        "city": "Istanbul",
        "country": "Turkey",
        "ip": client_ip,
    }
    if buyer_phone:
        buyer["gsmNumber"] = buyer_phone
    return buyer


async def create_iyzico_checkout(
    trial: StoryPreview,
    db: AsyncSession,
    client_ip: str,
    promo_code_str: str = "",
) -> dict[str, Any]:
    """Build and submit an Iyzico CheckoutFormInitialize request for a trial.

    Returns a dict with ``payment_url`` and ``trial_id`` on success.
    Raises HTTPException on any failure.
    """
    import iyzipay

    try:
        options = get_iyzico_options()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    settings = get_settings()

    if trial.status not in [
        PreviewStatus.PREVIEW_GENERATED.value,
        PreviewStatus.PAYMENT_PENDING.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trial bu durumda ödeme başlatılamaz: {trial.status}",
        )

    base_book_price = await resolve_trial_price(trial, db)
    # Persist resolved price back to trial
    if base_book_price > Decimal("0") and not trial.product_price:
        trial.product_price = float(base_book_price)
        await db.commit()

    final_amount = base_book_price

    # ── Sesli kitap fiyatı ──
    audio_addon_price = Decimal("0")
    audio_type_val = ""
    has_audio = getattr(trial, "has_audio_book", False)
    if has_audio:
        audio_type_val = getattr(trial, "audio_type", "system") or "system"
        audio_addon_price = Decimal("300") if audio_type_val == "cloned" else Decimal("150")
        final_amount += audio_addon_price
        logger.info("Audio addon added to payment", trial_id=str(trial.id), audio_type=audio_type_val, price=str(audio_addon_price))

    # ── Boyama kitabı fiyatı ──
    coloring_book_price = Decimal("0")
    if getattr(trial, "has_coloring_book", False):
        from app.models.coloring_book import ColoringBookProduct
        coloring_config_result = await db.execute(
            select(ColoringBookProduct).where(ColoringBookProduct.active == True).limit(1)
        )
        coloring_config = coloring_config_result.scalar_one_or_none()
        if coloring_config:
            coloring_book_price = Decimal(str(coloring_config.discounted_price or coloring_config.base_price))
            final_amount += coloring_book_price
            logger.info(
                "Coloring book added to payment",
                trial_id=str(trial.id),
                coloring_book_price=str(coloring_book_price),
            )

    # ── Kupon indirimi ──
    promo_discount = Decimal("0")
    if promo_code_str:
        try:
            from app.services.promo_code_service import calculate_discount, validate_promo_code
            promo_obj = await validate_promo_code(promo_code_str, final_amount, db)
            promo_discount = calculate_discount(promo_obj, final_amount)
            if promo_discount > Decimal("0"):
                final_amount = max(final_amount - promo_discount, Decimal("0"))
                logger.info(
                    "Promo discount applied to payment",
                    trial_id=str(trial.id),
                    promo_code=promo_code_str,
                    discount=str(promo_discount),
                    final_amount=str(final_amount),
                    original_base=str(base_book_price),
                )
        except HTTPException:
            raise
        except Exception as promo_err:
            logger.warning(
                "Promo validation failed in create-payment, continuing without discount",
                trial_id=str(trial.id),
                promo_code=promo_code_str,
                error=str(promo_err),
            )

    if final_amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ürün ücretsiz — promo kodu ile tamamlayın.",
        )

    if "localhost" in settings.frontend_url or "127.0.0.1" in settings.frontend_url:
        logger.error(
            "TRIAL_IYZICO_CALLBACK_URL_LOCALHOST",
            trial_id=str(trial.id),
            frontend_url=settings.frontend_url,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ödeme callback adresi yapılandırılmamış (FRONTEND_URL). Yöneticiyle iletişime geçin.",
        )

    buyer = build_iyzico_buyer(trial, client_ip)
    address = {
        "contactName": (trial.parent_name or "Misafir Kullanıcı").strip(),
        "city": "Istanbul",
        "country": "Turkey",
        "address": "Adres belirtilmedi",
    }

    _tt = trial.confirmation_token or ""
    callback_url = f"{settings.frontend_url}/api/payment/callback?trialId={trial.id}&tt={_tt}"

    book_item_price = max(base_book_price - promo_discount, Decimal("0"))

    iyzico_request: dict[str, Any] = {
        "locale": "tr",
        "conversationId": str(trial.id),
        "price": str(final_amount),
        "paidPrice": str(final_amount),
        "currency": "TRY",
        "basketId": str(trial.id)[:16],
        "paymentGroup": "PRODUCT",
        "callbackUrl": callback_url,
        "enabledInstallments": [1, 2, 3, 6],
        "buyer": buyer,
        "shippingAddress": address,
        "billingAddress": address,
        "basketItems": [
            {
                "id": str(trial.id)[:16],
                "name": "Kişiselleştirilmiş Hikaye Kitabı",
                "category1": "Kitap",
                "category2": "Çocuk Kitabı",
                "itemType": "VIRTUAL",
                "price": str(book_item_price),
            }
        ],
    }

    if audio_addon_price > Decimal("0"):
        audio_label = "Sesli Kitap - Klonlanmış Ses" if audio_type_val == "cloned" else "Sesli Kitap - Profesyonel Ses"
        iyzico_request["basketItems"].append({
            "id": f"{str(trial.id)[:12]}_aud",
            "name": audio_label,
            "category1": "Dijital Hizmet",
            "category2": "Sesli Kitap",
            "itemType": "VIRTUAL",
            "price": str(audio_addon_price),
        })

    if coloring_book_price > Decimal("0"):
        iyzico_request["basketItems"].append({
            "id": f"{str(trial.id)[:12]}_clr",
            "name": "Boyama Kitabı",
            "category1": "Kitap",
            "category2": "Çocuk Kitabı",
            "itemType": "VIRTUAL",
            "price": str(coloring_book_price),
        })

    try:
        checkout_form = iyzipay.CheckoutFormInitialize().create(iyzico_request, options)
        import json as _json
        result_dict = _json.loads(checkout_form.read().decode("utf-8"))
    except Exception as exc:
        err_str = str(exc).lower()
        if "timeout" in err_str or "timed out" in err_str:
            detail_msg = "Ödeme sayfası oluşturulamadı: Ödeme sağlayıcısı yanıt vermedi (zaman aşımı). Lütfen tekrar deneyin."
        elif "connection" in err_str or "connect" in err_str or "ssl" in err_str or "certificate" in err_str:
            detail_msg = "Ödeme sayfası oluşturulamadı: Ödeme sağlayıcısına bağlanılamadı. Lütfen tekrar deneyin."
        else:
            detail_msg = "Ödeme sayfası oluşturulamadı. Lütfen tekrar deneyin."
        logger.error(
            "TRIAL_IYZICO_CHECKOUT_ERROR",
            trial_id=str(trial.id),
            error=str(exc),
            error_type=type(exc).__name__,
            iyzico_base_url=settings.iyzico_base_url or "",
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail_msg,
        ) from exc

    if result_dict.get("status") != "success":
        error_msg = result_dict.get("errorMessage", "Bilinmeyen hata")
        error_code = result_dict.get("errorCode", "")
        logger.error(
            "TRIAL_IYZICO_CHECKOUT_FAILED",
            trial_id=str(trial.id),
            error=error_msg,
            error_code=error_code,
            full_response=result_dict,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ödeme sayfası oluşturulamadı: {error_msg}",
        )

    iyzico_token = result_dict.get("token", "")
    payment_page_url = result_dict.get("paymentPageUrl", "")

    # Store pending token so verify-payment can confirm it
    trial.payment_reference = f"iyzico_pending:{iyzico_token}"
    trial.status = PreviewStatus.PAYMENT_PENDING.value
    await db.commit()

    logger.info(
        "TRIAL_IYZICO_CHECKOUT_CREATED",
        trial_id=str(trial.id),
        token_prefix=iyzico_token[:10] if iyzico_token else "N/A",
    )

    return {
        "success": True,
        "payment_url": payment_page_url,
        "trial_id": str(trial.id),
    }


async def verify_iyzico_payment(
    trial: StoryPreview,
    token: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Verify an Iyzico payment token and mark the trial as paid.

    Returns a result dict. Does not raise on payment failure — returns
    ``{"success": False, "error": ...}`` instead.
    """
    import json as _json

    import iyzipay

    try:
        options = get_iyzico_options()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    settings = get_settings()

    try:
        verify_result = iyzipay.CheckoutForm().retrieve(
            {"locale": "tr", "conversationId": str(trial.id), "token": token},
            options,
        )
        result_dict = _json.loads(verify_result.read().decode("utf-8"))
    except Exception as exc:
        logger.error("TRIAL_IYZICO_VERIFY_ERROR", trial_id=str(trial.id), error=str(exc))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ödeme doğrulanamadı") from exc

    iyzico_status = result_dict.get("paymentStatus")

    if iyzico_status != "SUCCESS":
        error_msg = result_dict.get("errorMessage", "Ödeme başarısız")
        logger.warning("TRIAL_IYZICO_VERIFY_FAILED", trial_id=str(trial.id), status=iyzico_status, error=error_msg)
        return {"success": False, "error": error_msg}

    trial.payment_reference = f"iyzico_paid:{token}"
    await db.commit()

    logger.info("TRIAL_IYZICO_VERIFY_OK", trial_id=str(trial.id))

    return {"success": True, "trial_id": str(trial.id), "payment_reference": f"iyzico_paid:{token}"}

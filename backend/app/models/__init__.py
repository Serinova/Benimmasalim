"""SQLAlchemy models."""

from app.models.app_setting import AppSetting
from app.models.audit_log import AuditLog
from app.models.book_template import AIGenerationConfig, BookTemplate, PageTemplate
from app.models.child_profile import ChildProfile
from app.models.coloring_book import ColoringBookProduct
from app.models.consent import ConsentRecord
from app.models.homepage import HomepageSection, SectionType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_download_token import InvoiceDownloadToken
from app.models.notification_outbox import NotificationOutbox, OutboxStatus
from app.models.notification_preference import NotificationPreference
from app.models.order import Order, OrderStatus
from app.models.order_page import OrderPage
from app.models.product import Product
from app.models.promo_code import DiscountType, PromoCode
from app.models.prompt_template import PromptTemplate
from app.models.scenario import Scenario
from app.models.story_preview import PreviewStatus, StoryPreview
from app.models.user import User, UserRole
from app.models.user_address import UserAddress
from app.models.visual_style import VisualStyle

__all__ = [
    "AppSetting",
    "User",
    "UserRole",
    "UserAddress",
    "NotificationOutbox",
    "OutboxStatus",
    "NotificationPreference",
    "ChildProfile",
    "Product",
    "Scenario",
    "VisualStyle",
    "Order",
    "OrderStatus",
    "OrderPage",
    "AuditLog",
    "ConsentRecord",
    "BookTemplate",
    "PageTemplate",
    "AIGenerationConfig",
    "StoryPreview",
    "PreviewStatus",
    "PromptTemplate",
    "PromoCode",
    "DiscountType",
    "HomepageSection",
    "SectionType",
    "ColoringBookProduct",
    "Invoice",
    "InvoiceStatus",
    "InvoiceDownloadToken",
]

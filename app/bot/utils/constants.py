"""
Constants for MAX VPN Bot

Application-wide constants.
"""

from enum import Enum


# Bot settings
DEFAULT_LANGUAGE = "ru"
I18N_DOMAIN = "bot"

# Webhook paths
MAX_WEBHOOK = "/webhook"
YOOKASSA_WEBHOOK = "/yookassa"
YOOMONEY_WEBHOOK = "/yoomoney"

# Transaction/Payment status
class TransactionStatus(Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# Currency
class Currency(Enum):
    RUB = {"code": "RUB", "symbol": "₽"}
    USD = {"code": "USD", "symbol": "$"}
    EUR = {"code": "EUR", "symbol": "€"}


# Navigation constants
class NavMainMenu:
    """Main menu navigation callbacks."""
    PROFILE = "menu_profile"
    SUBSCRIPTION = "menu_subscription"
    SUPPORT = "menu_support"
    REFERRAL = "menu_referral"


class NavSubscription:
    """Subscription navigation callbacks."""
    CHOOSE_PLAN = "sub_choose_plan"
    PERSONAL_PLAN = "sub_personal_{duration}"
    CORPORATE_PLAN = "sub_corporate_{slots}"
    PAYMENT_METHOD = "sub_payment_method"
    PAY_YOOKASSA = "sub_pay_yookassa"
    PAY_YOOMONEY = "sub_pay_yoomoney"
    ENTER_COUPON = "sub_enter_coupon"
    APPLY_COUPON = "sub_apply_coupon"
    SKIP_COUPON = "sub_skip_coupon"


class NavProfile:
    """Profile navigation callbacks."""
    VIEW_KEY = "profile_view_key"
    RENEW = "profile_renew"
    PAYMENT_HISTORY = "profile_payment_history"


class NavReferral:
    """Referral navigation callbacks."""
    MY_REFERRALS = "ref_my_referrals"
    MY_COUPONS = "ref_my_coupons"
    COPY_LINK = "ref_copy_link"


class NavSupport:
    """Support navigation callbacks."""
    AI_SUPPORT = "support_ai"
    ESCALATE = "support_escalate"
    CONTACT_OWNER = "support_contact_owner"


class NavAdmin:
    """Admin navigation callbacks."""
    SERVERS = "admin_servers"
    USERS = "admin_users"
    STATISTICS = "admin_stats"
    NOTIFICATIONS = "admin_notify"
    CORPORATE_SERVERS = "admin_corp_servers"
    GRANT_DISCOUNT = "admin_grant_discount"


# Database
DB_DRIVER = "postgresql+asyncpg"

# Logging
LOG_ZIP_ARCHIVE_FORMAT = "zip"
LOG_GZ_ARCHIVE_FORMAT = "gz"

# Bot states tags
BOT_STARTED_TAG = "🟢 Bot started"
BOT_STOPPED_TAG = "🔴 Bot stopped"

# Referral settings
REFERRAL_DISCOUNT_PERCENT = 10  # 10% per referral
REFERRAL_MAX_DISCOUNT = 50  # Max 50% discount
REFERRAL_COUPON_VALID_DAYS = 365  # Coupon valid for 1 year

# Corporate settings
CORPORATE_SLOTS_OPTIONS = [100, 500]
CORPORATE_PRICES = {
    100: 9899,
    500: 19499,
}

# DeepSeek
DEEPSEEK_UNCERTAIN_KEYWORDS = ["НЕ УВЕРЕН", "не уверен", "not sure", "don't know"]

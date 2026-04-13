import logging
from dataclasses import dataclass
from logging.handlers import MemoryHandler
from pathlib import Path

from environs import Env
from marshmallow.validate import OneOf, Range

from app.bot.utils.constants import (
    LOG_GZ_ARCHIVE_FORMAT,
    LOG_ZIP_ARCHIVE_FORMAT,
    Currency,
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_LOCALES_DIR = BASE_DIR / "locales"
DEFAULT_PLANS_DIR = DEFAULT_DATA_DIR / "plans.json"

DEFAULT_BOT_HOST = "0.0.0.0"
DEFAULT_BOT_PORT = 8080

DEFAULT_SHOP_EMAIL = "support@vpn-shop.ru"
DEFAULT_SHOP_CURRENCY = Currency.RUB.code

# Payment defaults
DEFAULT_SHOP_PAYMENT_YOOKASSA_ENABLED = False
DEFAULT_SHOP_PAYMENT_YOOMONEY_ENABLED = False

# Database defaults
DEFAULT_DB_NAME = "vpn_shop"
DEFAULT_DB_HOST = "postgres"
DEFAULT_DB_PORT = 5432

# Redis defaults
DEFAULT_REDIS_DB_NAME = "0"
DEFAULT_REDIS_HOST = "redis"
DEFAULT_REDIS_PORT = 6379

# 3X-UI defaults
DEFAULT_SUBSCRIPTION_PORT = 2096
DEFAULT_SUBSCRIPTION_PATH = "/user/"

# DeepSeek defaults
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_DEEPSEEK_MAX_TOKENS = 500
DEFAULT_DEEPSEEK_TEMPERATURE = 0.3

# Logging defaults
DEFAULT_LOG_LEVEL = "DEBUG"
DEFAULT_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DEFAULT_LOG_ARCHIVE_FORMAT = LOG_ZIP_ARCHIVE_FORMAT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
memory_handler = MemoryHandler(capacity=100, flushLevel=logging.ERROR)
memory_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
logger.addHandler(memory_handler)


@dataclass
class BotConfig:
    """MAX Bot configuration."""
    TOKEN: str
    ADMINS: list[int]
    DEV_ID: int
    DOMAIN: str
    PORT: int


@dataclass
class ShopConfig:
    """Shop/payment configuration."""
    EMAIL: str
    CURRENCY: str
    PAYMENT_YOOKASSA_ENABLED: bool
    PAYMENT_YOOMONEY_ENABLED: bool


@dataclass
class XUIConfig:
    USERNAME: str
    PASSWORD: str
    TOKEN: str | None
    SUBSCRIPTION_PORT: int
    SUBSCRIPTION_PATH: str


@dataclass
class DeepSeekConfig:
    """DeepSeek AI configuration."""
    API_KEY: str | None
    MODEL: str
    MAX_TOKENS: int
    TEMPERATURE: float

@dataclass
class YooKassaConfig:
    TOKEN: str | None
    SHOP_ID: int | None


@dataclass
class YooMoneyConfig:
    NOTIFICATION_SECRET: str | None
    WALLET_ID: str | None


@dataclass
class DeepSeekConfig:
    """DeepSeek AI configuration."""
    API_KEY: str | None
    MODEL: str
    MAX_TOKENS: int
    TEMPERATURE: float


@dataclass
class EncryptionConfig:
    """Encryption configuration for sensitive data."""
    KEY: str | None


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    HOST: str
    PORT: int
    NAME: str
    USERNAME: str
    PASSWORD: str

    def url(self, driver: str = "postgresql+asyncpg") -> str:
        """Generate database URL for SQLAlchemy."""
        return f"{driver}://{self.USERNAME}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


@dataclass
class RedisConfig:
    HOST: str
    PORT: int
    DB_NAME: str
    USERNAME: str | None
    PASSWORD: str | None

    def url(self) -> str:
        if self.USERNAME and self.PASSWORD:
            return f"redis://{self.USERNAME}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB_NAME}"
        return f"redis://{self.HOST}:{self.PORT}/{self.DB_NAME}"


@dataclass
class LoggingConfig:
    LEVEL: str
    FORMAT: str
    ARCHIVE_FORMAT: str


@dataclass
class Config:
    """Main configuration container."""
    bot: BotConfig
    shop: ShopConfig
    xui: XUIConfig
    yookassa: YooKassaConfig
    yoomoney: YooMoneyConfig
    deepseek: DeepSeekConfig
    encryption: EncryptionConfig
    database: DatabaseConfig
    redis: RedisConfig
    logging: LoggingConfig


def load_config() -> Config:
    """Load and validate configuration from environment variables."""
    env = Env()
    env.read_env()

    # Bot admins
    bot_admins = env.list("BOT_ADMINS", subcast=int, default=[], required=False)
    if not bot_admins:
        logger.warning("BOT_ADMINS list is empty.")

    # Payment validation
    payment_yookassa_enabled = env.bool(
        "SHOP_PAYMENT_YOOKASSA_ENABLED",
        default=DEFAULT_SHOP_PAYMENT_YOOKASSA_ENABLED,
    )
    if payment_yookassa_enabled:
        yookassa_token = env.str("YOOKASSA_TOKEN", default=None)
        yookassa_shop_id = env.int("YOOKASSA_SHOP_ID", default=None)
        if not yookassa_token or not yookassa_shop_id:
            logger.error(
                "YOOKASSA_TOKEN or YOOKASSA_SHOP_ID is not set. Payment YooKassa is disabled."
            )
            payment_yookassa_enabled = False

    payment_yoomoney_enabled = env.bool(
        "SHOP_PAYMENT_YOOMONEY_ENABLED",
        default=DEFAULT_SHOP_PAYMENT_YOOMONEY_ENABLED,
    )
    if payment_yoomoney_enabled:
        yoomoney_notification_secret = env.str("YOOMONEY_NOTIFICATION_SECRET", default=None)
        yoomoney_wallet_id = env.str("YOOMONEY_WALLET_ID", default=None)
        if not yoomoney_notification_secret or not yoomoney_wallet_id:
            logger.error(
                "YOOMONEY_NOTIFICATION_SECRET or YOOMONEY_WALLET_ID is not set. Payment YooMoney is disabled."
            )
            payment_yoomoney_enabled = False

    # Check at least one payment method is enabled
    if not payment_yookassa_enabled and not payment_yoomoney_enabled:
        logger.warning("No payment methods are enabled. Please enable at least one.")

    # DeepSeek validation
    deepseek_api_key = env.str("DEEPSEEK_API_KEY", default=None)
    if not deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY is not set. AI support will be disabled.")

    # Encryption key validation
    encryption_key = env.str("ENCRYPTION_KEY", default=None)
    if not encryption_key:
        logger.warning("ENCRYPTION_KEY is not set. Corporate server encryption will be disabled.")

    return Config(
        bot=BotConfig(
            TOKEN=env.str("MAX_BOT_TOKEN"),
            ADMINS=bot_admins,
            DEV_ID=env.int("MAX_DEV_ID"),
            DOMAIN=f"https://{env.str('BOT_DOMAIN')}",
            PORT=env.int("BOT_PORT", default=DEFAULT_BOT_PORT),
        ),
        shop=ShopConfig(
            EMAIL=env.str("SHOP_EMAIL", default=DEFAULT_SHOP_EMAIL),
            CURRENCY=env.str(
                "SHOP_CURRENCY",
                default=DEFAULT_SHOP_CURRENCY,
                validate=OneOf(
                    [currency.code for currency in Currency]
                    + [currency.code.lower() for currency in Currency],
                    error="SHOP_CURRENCY must be one of: {choices}",
                ),
            ).upper(),
            PAYMENT_YOOKASSA_ENABLED=payment_yookassa_enabled,
            PAYMENT_YOOMONEY_ENABLED=payment_yoomoney_enabled,
        ),
        xui=XUIConfig(
            USERNAME=env.str("XUI_USERNAME"),
            PASSWORD=env.str("XUI_PASSWORD"),
            TOKEN=env.str("XUI_TOKEN", default=None),
            SUBSCRIPTION_PORT=env.int("XUI_SUBSCRIPTION_PORT", default=DEFAULT_SUBSCRIPTION_PORT),
            SUBSCRIPTION_PATH=env.str(
                "XUI_SUBSCRIPTION_PATH",
                default=DEFAULT_SUBSCRIPTION_PATH,
            ),
        ),
        yookassa=YooKassaConfig(
            TOKEN=env.str("YOOKASSA_TOKEN", default=None),
            SHOP_ID=env.int("YOOKASSA_SHOP_ID", default=None),
        ),
        yoomoney=YooMoneyConfig(
            NOTIFICATION_SECRET=env.str("YOOMONEY_NOTIFICATION_SECRET", default=None),
            WALLET_ID=env.str("YOOMONEY_WALLET_ID", default=None),
        ),
        deepseek=DeepSeekConfig(
            API_KEY=deepseek_api_key,
            MODEL=env.str("DEEPSEEK_MODEL", default=DEFAULT_DEEPSEEK_MODEL),
            MAX_TOKENS=env.int("DEEPSEEK_MAX_TOKENS", default=DEFAULT_DEEPSEEK_MAX_TOKENS),
            TEMPERATURE=env.float("DEEPSEEK_TEMPERATURE", default=DEFAULT_DEEPSEEK_TEMPERATURE),
        ),
        encryption=EncryptionConfig(
            KEY=encryption_key,
        ),
        database=DatabaseConfig(
            HOST=env.str("POSTGRES_HOST", default=DEFAULT_DB_HOST),
            PORT=env.int("POSTGRES_PORT", default=DEFAULT_DB_PORT),
            USERNAME=env.str("POSTGRES_USER"),
            PASSWORD=env.str("POSTGRES_PASSWORD"),
            NAME=env.str("POSTGRES_DB", default=DEFAULT_DB_NAME),
        ),
        redis=RedisConfig(
            HOST=env.str("REDIS_HOST", default=DEFAULT_REDIS_HOST),
            PORT=env.int("REDIS_PORT", default=DEFAULT_REDIS_PORT),
            DB_NAME=env.str("REDIS_DB_NAME", default=DEFAULT_REDIS_DB_NAME),
            USERNAME=env.str("REDIS_USERNAME", default=None),
            PASSWORD=env.str("REDIS_PASSWORD", default=None),
        ),
        logging=LoggingConfig(
            LEVEL=env.str("LOG_LEVEL", default=DEFAULT_LOG_LEVEL),
            FORMAT=env.str("LOG_FORMAT", default=DEFAULT_LOG_FORMAT),
            ARCHIVE_FORMAT=env.str(
                "LOG_ARCHIVE_FORMAT",
                default=DEFAULT_LOG_ARCHIVE_FORMAT,
                validate=OneOf(
                    [LOG_ZIP_ARCHIVE_FORMAT, LOG_GZ_ARCHIVE_FORMAT],
                    error="LOG_ARCHIVE_FORMAT must be one of: {choices}",
                ),
            ),
        ),
    )

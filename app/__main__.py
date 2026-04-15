"""
MAX VPN Bot - Main Entry Point

Application initialization and startup.
"""

import asyncio
import logging
from urllib.parse import urljoin

from aiohttp.web import Application, _run_app

from app import logger
from app.bot.max_api import MAXBot, MAXDispatcher
from app.bot.max_api.types import Update
from app.bot.models import ServicesContainer
from app.bot.utils.constants import BOT_STARTED_TAG, BOT_STOPPED_TAG
from app.config import Config, load_config
from app.db.database import Database

logger = logging.getLogger(__name__)


async def on_startup(
    config: Config,
    bot: MAXBot,
    services: ServicesContainer,
    db: Database,
) -> None:
    """
    Handle bot startup.
    
    Args:
        config: Application configuration.
        bot: MAX Bot instance.
        services: Services container.
        db: Database instance.
    """
    await services.notification.notify_developer(BOT_STARTED_TAG)
    logger.info("🚀 MAX VPN Bot started successfully!")
    logger.info(f"Database: {config.db.NAME}")
    logger.info(f"Bot domain: {config.bot.DOMAIN}")


async def on_shutdown(
    config: Config,
    bot: MAXBot,
    services: ServicesContainer,
    db: Database,
) -> None:
    """
    Handle bot shutdown.
    
    Args:
        config: Application configuration.
        bot: MAX Bot instance.
        services: Services container.
        db: Database instance.
    """
    await services.notification.notify_developer(BOT_STOPPED_TAG)
    await db.close()
    logger.info("🛑 MAX VPN Bot stopped.")


async def main() -> None:
    """Main application entry point."""
    
    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")
    
    # Initialize database
    db = Database(config)
    await db.initialize()
    logger.info("Database initialized")
    
    # Create services container
    bot = MAXBot(token=config.bot.TOKEN)
    services = ServicesContainer.create(
        config=config,
        bot=bot,
        session=db.session,
    )
    logger.info("Services initialized")
    
    # Create dispatcher
    dispatcher = MAXDispatcher()
    
    # Register handlers
    await register_handlers(dispatcher, bot, services, config)
    
    # Setup startup/shutdown handlers
    async def startup_handler():
        await on_startup(config, bot, services, db)
    
    async def shutdown_handler():
        await on_shutdown(config, bot, services, db)
    
    # Add lifecycle handlers
    dispatcher.on_startup(startup_handler)
    dispatcher.on_shutdown(shutdown_handler)
    
    # Start polling
    logger.info("Starting polling...")
    await dispatcher.start_polling(bot)


async def register_handlers(
    dispatcher: MAXDispatcher,
    bot: MAXBot,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Register all bot handlers.
    
    Args:
        dispatcher: MAX Dispatcher instance.
        bot: MAX Bot instance.
        services: Services container.
        config: Application configuration.
    """
    from app.bot.routers.main_menu.handler import handle_start, handle_menu
    from app.bot.routers.subscription.subscription_handler import (
        handle_subscription_menu,
        handle_plan_selection,
        handle_payment_method_selection,
        handle_apply_coupon,
    )
    from app.bot.routers.subscription.receipt_handler import (
        handle_receipt_submission,
        handle_receipt_photo,
        handle_receipt_text,
    )
    from app.bot.routers.profile.handler import (
        handle_profile,
        handle_show_key,
        handle_payment_history,
    )
    from app.bot.routers.referral.handler import (
        handle_referral,
        handle_referral_coupons,
        handle_referral_stats,
    )
    from app.bot.routers.support.handler import (
        handle_support,
        handle_faq,
        handle_support_contact,
    )
    from app.bot.routers.admin_tools.payment_approval import (
        handle_admin_approve,
        handle_admin_reject,
        handle_rejection_reason,
        handle_admin_cancel_rejection,
    )
    
    # ===== COMMANDS =====
    
    # /start command
    @dispatcher.message_handler(commands=["start"])
    async def start_handler(update: Update):
        await handle_start(
            bot=bot,
            update=update,
            services=services,
            config=config,
            new_user=True,
        )
    
    # /menu command
    @dispatcher.message_handler(commands=["menu"])
    async def menu_handler(update: Update):
        await handle_menu(
            bot=bot,
            update=update,
            services=services,
            config=config,
        )
    
    # /subscription command
    @dispatcher.message_handler(commands=["subscription"])
    async def subscription_handler(update: Update):
        await handle_subscription_menu(
            bot=bot,
            update=update,
            services=services,
            config=config,
        )
    
    # /profile command
    @dispatcher.message_handler(commands=["profile"])
    async def profile_handler(update: Update):
        await handle_profile(
            bot=bot,
            update=update,
            services=services,
            config=config,
        )
    
    # /referral command
    @dispatcher.message_handler(commands=["referral"])
    async def referral_handler(update: Update):
        await handle_referral(
            bot=bot,
            update=update,
            services=services,
            config=config,
        )
    
    # /support command
    @dispatcher.message_handler(commands=["support"])
    async def support_handler(update: Update):
        await handle_support(
            bot=bot,
            update=update,
            services=services,
            config=config,
        )
    
    # /cancel command
    @dispatcher.message_handler(commands=["cancel"])
    async def cancel_handler(update: Update):
        await handle_admin_cancel_rejection(bot, update, services, config)
    
    # ===== PHOTO/TEXT HANDLERS (for receipts) =====
    
    @dispatcher.message_handler(content_types=["photo"])
    async def photo_handler(update: Update):
        """Handle photo messages (receipt screenshots)."""
        await handle_receipt_photo(bot, update, services, config)
    
    @dispatcher.message_handler(content_types=["text"])
    async def text_handler(update: Update):
        """Handle text messages (check if it's a receipt)."""
        # Ignore commands
        if update.message.text.startswith('/'):
            return
        await handle_receipt_text(bot, update, services, config)
    
    # ===== CALLBACK HANDLERS =====
    
    @dispatcher.callback_query_handler(lambda c: True)
    async def callback_router(update: Update):
        """Route all callback queries to appropriate handlers."""
        callback_data = update.callback_query.data
        
        # Main menu callbacks
        if callback_data == "menu":
            await handle_menu(bot, update, services, config)
        elif callback_data == "menu_subscription":
            await handle_subscription_menu(bot, update, services, config)
        elif callback_data == "menu_profile":
            await handle_profile(bot, update, services, config)
        elif callback_data == "menu_referral":
            await handle_referral(bot, update, services, config)
        elif callback_data == "menu_support":
            await handle_support(bot, update, services, config)
        
        # Subscription callbacks
        elif callback_data.startswith("plan_"):
            # Parse plan_{duration}_{price}
            parts = callback_data.split("_")
            duration = int(parts[1])
            price = float(parts[2])
            await handle_plan_selection(bot, update, services, config, duration, price)
        elif callback_data == "payment_sber_qr":
            await handle_payment_method_selection(bot, update, services, config, "sber_qr")
        elif callback_data == "payment_yookassa":
            await handle_payment_method_selection(bot, update, services, config, "yookassa")
        elif callback_data == "payment_yoomoney":
            await handle_payment_method_selection(bot, update, services, config, "yoomoney")
        elif callback_data == "apply_coupon":
            await handle_apply_coupon(bot, update, services, config)
        
        # Profile callbacks
        elif callback_data == "profile":
            await handle_profile(bot, update, services, config)
        elif callback_data == "profile_show_key":
            await handle_show_key(bot, update, services, config)
        elif callback_data == "profile_payments":
            await handle_payment_history(bot, update, services, config)
        
        # Referral callbacks
        elif callback_data == "referral":
            await handle_referral(bot, update, services, config)
        elif callback_data == "referral_coupons":
            await handle_referral_coupons(bot, update, services, config)
        elif callback_data == "referral_stats":
            await handle_referral_stats(bot, update, services, config)
        
        # Support callbacks
        elif callback_data == "support":
            await handle_support(bot, update, services, config)
        elif callback_data == "support_faq":
            await handle_faq(bot, update, services, config)
        elif callback_data == "support_contact":
            await handle_support_contact(bot, update, services, config)
        
        # Receipt callbacks
        elif callback_data == "send_receipt":
            await handle_receipt_submission(bot, update, services, config)
        
        # Admin payment approval callbacks
        elif callback_data.startswith("admin_approve_"):
            payment_id = int(callback_data.split("_")[-1])
            await handle_admin_approve(bot, update, services, config, payment_id)
        elif callback_data.startswith("admin_reject_"):
            payment_id = int(callback_data.split("_")[-1])
            await handle_admin_reject(bot, update, services, config, payment_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

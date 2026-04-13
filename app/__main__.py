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
    
    # Callback handler for menu buttons
    @dispatcher.callback_query_handler(lambda c: c.data.startswith("menu_"))
    async def menu_callback_handler(update: Update):
        callback_data = update.callback_query.data
        
        if callback_data == "menu_subscription":
            await bot.send_message(
                chat_id=update.callback_query.from_user.id,
                text="💳 Раздел подписки (в разработке)",
                parse_mode="html",
            )
        elif callback_data == "menu_profile":
            await bot.send_message(
                chat_id=update.callback_query.from_user.id,
                text="👤 Раздел профиля (в разработке)",
                parse_mode="html",
            )
        elif callback_data == "menu_referral":
            await bot.send_message(
                chat_id=update.callback_query.from_user.id,
                text="🎁 Реферальная программа (в разработке)",
                parse_mode="html",
            )
        elif callback_data == "menu_support":
            await bot.send_message(
                chat_id=update.callback_query.from_user.id,
                text="💬 Поддержка (в разработке)",
                parse_mode="html",
            )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

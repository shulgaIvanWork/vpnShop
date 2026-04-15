"""
Main Menu Handler

Handles /start command and main menu navigation.
"""

import logging

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup, Update
from app.bot.services import ServicesContainer
from app.config import Config
from app.db.models import User

logger = logging.getLogger(__name__)


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Create main menu keyboard.
    
    Returns:
        InlineKeyboardMarkup with main menu buttons.
    """
    keyboard = InlineKeyboardMarkup()
    
    # Row 1: Subscription & Profile
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("💳 Подписка", "menu_subscription"),
        InlineKeyboardMarkup.callback_button("👤 Профиль", "menu_profile"),
    ])
    
    # Row 2: Referral & Support
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("🎁 Рефералка", "menu_referral"),
        InlineKeyboardMarkup.callback_button("💬 Поддержка", "menu_support"),
    ])
    
    return keyboard


async def handle_start(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
    new_user: bool = False,
) -> None:
    """
    Handle /start command.
    
    Creates user in database if not exists.
    Processes referral link if present.
    
    Args:
        bot: MAX Bot instance.
        update: Update object from MAX.
        services: Services container.
        config: Application configuration.
        new_user: True if this is a new user.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    # Extract referrer ID from start command
    # Format: /start ref_12345
    referrer_id = None
    if update.message.text and update.message.text.startswith('/start ref_'):
        try:
            referrer_id = int(update.message.text.split('ref_')[1])
        except (ValueError, IndexError):
            pass
    
    # Create or get user from database
    async with config.db.session() as session:
        user, created = await User.get_or_create(
            session=session,
            max_user_id=user_id,
            username=username,
        )
        
        if not user:
            logger.error(f"Failed to create/get user {user_id}")
            await bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка при регистрации. Попробуйте ещё раз.",
                parse_mode="html",
            )
            return
        
        # If referred and user is new, create referral record
        if referrer_id and created:
            from app.db.models.referral import Referral
            
            # Don't allow self-referral
            if referrer_id != user_id:
                referral = await Referral.create(
                    session=session,
                    referrer_id=referrer_id,
                    referred_id=user.id,
                    referred_type="individual",
                )
                
                if referral:
                    logger.info(
                        f"Referral created: {referrer_id} -> {user.id} "
                        f"(user {user_id})"
                    )
        
        await session.commit()
    
    # Show welcome message
    if created:
        text = (
            f"🎉 <b>Добро пожаловать, {username or 'друг'}!</b>\n\n"
            f"🚀 <b>MAX VPN Shop</b> - ваш надёжный VPN сервис\n\n"
            f"✨ <b>Преимущества:</b>\n"
            f"• 🌍 Неограниченный трафик\n"
            f"• ⚡ Высокая скорость\n"
            f"• 🔒 Полная анонимность\n"
            f"• 📱 До 5 устройств\n"
            f"• 🎁 Скидки за рефералов\n\n"
            f"Выберите действие в меню ниже 👇"
        )
    else:
        text = (
            f"👋 <b>С возвращением, {username or 'друг'}!</b>\n\n"
            f"Выберите действие:"
        )
    
    keyboard = create_main_menu_keyboard()
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Main menu shown to user {user_id}")


async def handle_menu(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle /menu command or menu callback.
    
    Args:
        bot: MAX Bot instance.
        update: Update object from MAX.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    
    text = "📱 <b>Главное меню</b>\n\nВыберите действие:"
    keyboard = create_main_menu_keyboard()
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )

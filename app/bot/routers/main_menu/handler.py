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
    
    Args:
        bot: MAX Bot instance.
        update: Update object from MAX.
        services: Services container.
        config: Application configuration.
        new_user: True if this is a new user.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Пользователь"
    
    if new_user:
        text = (
            f"🎉 <b>Добро пожаловать, {username}!</b>\n\n"
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
            f"👋 <b>С возвращением, {username}!</b>\n\n"
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

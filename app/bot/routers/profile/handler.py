"""
Profile Handler

Handles user profile viewing and management.
"""

import logging
from datetime import datetime

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup, Update
from app.bot.services import ServicesContainer
from app.config import Config
from app.db.models import User

logger = logging.getLogger(__name__)


def create_profile_keyboard(has_subscription: bool) -> InlineKeyboardMarkup:
    """
    Create profile keyboard.
    
    Args:
        has_subscription: True if user has active subscription.
        
    Returns:
        InlineKeyboardMarkup with profile options.
    """
    keyboard = InlineKeyboardMarkup()
    
    if has_subscription:
        keyboard.add_row([
            InlineKeyboardMarkup.callback_button("🔑 Показать ключ", "profile_show_key"),
        ])
    
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("💳 История платежей", "profile_payments"),
    ])
    
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "menu"),
    ])
    
    return keyboard


async def handle_profile(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle profile command.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    
    # Get user from database
    # TODO: Replace with actual database call
    # async with config.db.session() as session:
    #     user = await User.get(session, max_user_id=user_id)
    
    # Placeholder user data
    has_subscription = False
    subscription_end = None
    device_limit = 1
    
    # Build profile text
    text = f"👤 <b>Ваш профиль</b>\n\n"
    text += f"🆔 User ID: <code>{user_id}</code>\n\n"
    
    if has_subscription and subscription_end:
        days_left = (subscription_end - datetime.now()).days
        
        text += f"✅ <b>Подписка активна</b>\n"
        text += f"📅 Истекает: {subscription_end.strftime('%d.%m.%Y')}\n"
        text += f"⏳ Осталось дней: {days_left}\n"
        text += f"📱 Устройств: {device_limit}\n\n"
    else:
        text += f"❌ <b>Подписка не активна</b>\n\n"
        text += f"💡 Купите подписку, чтобы получить доступ к VPN\n\n"
    
    keyboard = create_profile_keyboard(has_subscription)
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Profile shown to user {user_id}")


async def handle_show_key(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle show VPN key request.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # TODO: Get actual VPN key from service
    # key = await services.vpn.get_key(user)
    
    key = "vless://your-key-here@server.example.com:443"
    
    text = (
        f"🔑 <b>Ваш VPN ключ:</b>\n\n"
        f"<code>{key}</code>\n\n"
        f"📱 <b>Как использовать:</b>\n"
        f"1. Скопируйте ключ (кнопка ниже)\n"
        f"2. Откройте V2rayNG/V2rayU\n"
        f"3. Нажмите '+' → 'Import from clipboard'\n"
        f"4. Подключитесь\n\n"
        f"💡 Не передавайте ключ третьим лицам!"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.clipboard_button("📋 Копировать ключ", key),
    ])
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "profile"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"VPN key shown to user {user_id}")


async def handle_payment_history(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle payment history request.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # TODO: Fetch actual payment history
    # payments = await Payment.get_user_payments(session, user_id)
    
    text = (
        f"💳 <b>История платежей</b>\n\n"
        f"⚠️ Функция в разработке\n\n"
        f"Здесь будет отображаться история всех ваших платежей."
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "profile"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Payment history requested by user {user_id}")

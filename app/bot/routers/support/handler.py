"""
Support Handler

Handles user support requests.
TODO: Integrate with DeepSeek AI for automated support.
"""

import logging

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup, Update
from app.bot.services import ServicesContainer
from app.config import Config

logger = logging.getLogger(__name__)


def create_support_keyboard() -> InlineKeyboardMarkup:
    """
    Create support keyboard.
    
    Returns:
        InlineKeyboardMarkup with support options.
    """
    keyboard = InlineKeyboardMarkup()
    
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("📖 FAQ", "support_faq"),
        InlineKeyboardMarkup.callback_button("💬 Написать в поддержку", "support_contact"),
    ])
    
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "menu"),
    ])
    
    return keyboard


async def handle_support(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle support command.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    
    text = (
        f"💬 <b>Поддержка</b>\n\n"
        f"Мы всегда готовы помочь!\n\n"
        f"🤖 <b>AI помощник</b> (скоро)\n"
        f"• Мгновенные ответы на вопросы\n"
        f"• Инструкции по подключению\n"
        f"• Помощь с настройкой\n\n"
        f"👨‍💻 <b>Человеческая поддержка</b>\n"
        f"• Email: support@example.com\n"
        f"• Время работы: 24/7\n\n"
        f"Выберите вариант помощи:"
    )
    
    keyboard = create_support_keyboard()
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Support menu shown to user {user_id}")


async def handle_faq(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle FAQ request.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    text = (
        f"📖 <b>Часто задаваемые вопросы</b>\n\n"
        
        f"<b>❓ Как подключиться к VPN?</b>\n"
        f"1. Скачайте V2rayNG (Android) или V2rayU (iOS)\n"
        f"2. Откройте раздел Профиль → Показать ключ\n"
        f"3. Скопируйте ключ\n"
        f"4. В приложении нажмите '+' → 'Import from clipboard'\n"
        f"5. Подключитесь\n\n"
        
        f"<b>❓ Сколько устройств можно подключить?</b>\n"
        f"Зависит от вашего тарифа (1-5 устройств)\n\n"
        
        f"<b>❓ Как продлить подписку?</b>\n"
        f"Нажмите /subscription и выберите тариф\n\n"
        
        f"<b>❓ Как работает реферальная программа?</b>\n"
        f"Приглашайте друзей и получайте скидки до 50%\n\n"
        
        f"<b>❓ Какие способы оплаты доступны?</b>\n"
        f"• ЮKassa (карты, СБП)\n"
        f"• YooMoney\n\n"
        
        f"Не нашли ответ? Напишите в поддержку!"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("💬 Написать в поддержку", "support_contact"),
    ])
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "support"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"FAQ shown to user {user_id}")


async def handle_support_contact(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle support contact request.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    text = (
        f"💬 <b>Связаться с поддержкой</b>\n\n"
        f"📧 Email: <code>support@example.com</code>\n"
        f"⏰ Время ответа: до 24 часов\n\n"
        f"📝 <b>Опишите вашу проблему:</b>\n"
        f"• Что произошло?\n"
        f"• Когда это началось?\n"
        f"• Какой у вас тариф?\n\n"
        f"Мы ответим вам как можно скорее! 🚀"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "support"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Support contact info shown to user {user_id}")

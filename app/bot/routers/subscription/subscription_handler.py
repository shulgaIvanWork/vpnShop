"""
Subscription Handler

Handles subscription plan selection and purchase flow.
"""

import logging

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup, Update
from app.bot.models import ServicesContainer, SubscriptionData
from app.bot.services import ServicesContainer
from app.config import Config
from app.db.models import User

logger = logging.getLogger(__name__)


def create_plans_keyboard() -> InlineKeyboardMarkup:
    """
    Create subscription plans keyboard.
    
    Returns:
        InlineKeyboardMarkup with plan options.
    """
    keyboard = InlineKeyboardMarkup()
    
    # Plan options (will be loaded from plans.json in production)
    plans = [
        {"duration": 30, "price": 299, "label": "1 месяц"},
        {"duration": 180, "price": 1499, "label": "6 месяцев"},
        {"duration": 365, "price": 2499, "label": "1 год"},
    ]
    
    for plan in plans:
        keyboard.add_row([
            InlineKeyboardMarkup.callback_button(
                f"📅 {plan['label']} - {plan['price']}₽",
                f"plan_{plan['duration']}_{plan['price']}",
            )
        ])
    
    # Back button
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "menu"),
    ])
    
    return keyboard


async def handle_subscription_menu(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle subscription menu command.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    
    # Get user from database
    async with config.db.session() as session:
        user = await User.get(session, max_user_id=user_id)
    
    text = (
        "💳 <b>Выберите тарифный план</b>\n\n"
        "📊 <b>Доступные планы:</b>\n"
        "• 1 месяц - 299₽\n"
        "• 6 месяцев - 1499₽ (экономия 295₽)\n"
        "• 1 год - 2499₽ (экономия 1089₽)\n\n"
        "✨ <b>Все планы включают:</b>\n"
        "• 🌍 Неограниченный трафик\n"
        "• ⚡ Высокая скорость\n"
        "• 🔒 Полная анонимность\n"
        "• 📱 До 5 устройств\n"
        "• 🎁 Реферальные скидки"
    )
    
    keyboard = create_plans_keyboard()
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Subscription plans shown to user {user_id}")


async def handle_plan_selection(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
    duration: int,
    price: float,
) -> None:
    """
    Handle plan selection callback.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
        duration: Selected plan duration in days.
        price: Selected plan price.
    """
    user_id = update.callback_query.from_user.id
    
    # Acknowledge callback
    await bot.answer_callback_query(update.callback_query.id)
    
    # Create subscription data
    subscription_data = SubscriptionData.create(
        user_id=user_id,
        duration=duration,
        price=price,
    )
    
    text = (
        f"✅ <b>Вы выбрали план:</b>\n\n"
        f"📅 Duration: {duration} дней\n"
        f"💰 Price: {price}₽\n\n"
        f"Выберите способ оплаты:"
    )
    
    # Create payment method keyboard
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("💳 ЮKassa", "payment_yookassa"),
        InlineKeyboardMarkup.callback_button("💰 YooMoney", "payment_yoomoney"),
    ])
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("🎫 Применить купон", "apply_coupon"),
    ])
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "menu_subscription"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"User {user_id} selected plan: {duration} days, {price} RUB")


async def handle_payment_method_selection(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
    method: str,
) -> None:
    """
    Handle payment method selection.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
        method: Selected payment method (yookassa/yoomoney).
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # TODO: Create payment with selected gateway
    # For now, show placeholder message
    
    text = (
        f"💳 <b>Оплата через {method}</b>\n\n"
        f"⚠️ Функция в разработке\n\n"
        f"В ближайшее время здесь появится ссылка на оплату."
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "menu_subscription"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"User {user_id} selected payment method: {method}")


async def handle_apply_coupon(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle coupon application request.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    text = (
        "🎫 <b>Применить купон</b>\n\n"
        "Введите код купона:\n"
        "(Например: VPN-ABC123XYZ)"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "menu_subscription"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"User {user_id} requested coupon application")

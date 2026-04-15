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
    
    Saves plan data to FSM for later use in payment flow.
    
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
    
    # Save plan data to FSM
    await services.fsm.set_data(user_id, {
        'plan_duration': duration,
        'plan_price': int(price),
        'original_price': int(price),
        'discount_percent': 0,
        'final_price': int(price),
        'payment_state': 'choosing_payment_method',
    })
    
    text = (
        f"✅ <b>Вы выбрали план:</b>\n\n"
        f"📅 Duration: {duration} дней\n"
        f"💰 Price: {price}₽\n\n"
        f"Выберите способ оплаты:"
    )
    
    # Create payment method keyboard - ONLY SBER QR FOR NOW
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("🏦 Сбербанк (QR)", "payment_sber_qr"),
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
    
    logger.info(f"User {user_id} selected plan: {duration} days, {price} RUB, saved to FSM")


async def handle_payment_method_selection(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
    method: str,
) -> None:
    """
    Handle payment method selection.
    
    For now, only Sber QR is available (manual payment).
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
        method: Selected payment method (sber_qr).
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # Get FSM storage from services
    fsm_data = await services.fsm.get_data(user_id)
    
    if not fsm_data or 'plan_duration' not in fsm_data:
        await bot.send_message(
            chat_id=user_id,
            text="❌ Ошибка: данные о тарифе не найдены. Выберите тариф заново.",
            parse_mode="html",
        )
        return
    
    plan_duration = fsm_data['plan_duration']
    original_price = fsm_data['plan_price']
    discount_percent = fsm_data.get('discount_percent', 0)
    final_price = fsm_data.get('final_price', original_price)
    
    # For now, only Sber QR is available
    if method == "sber_qr":
        await _show_sber_payment(
            bot=bot,
            user_id=user_id,
            plan_duration=plan_duration,
            final_price=final_price,
            original_price=original_price,
            discount_percent=discount_percent,
            config=config,
            services=services,
        )
    else:
        # Fallback for yookassa/yoomoney (not implemented yet)
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"💳 <b>Оплата через {method}</b>\n\n"
                f"⚠️ Временно недоступно\n\n"
                f"Используйте оплату через Сбербанк (QR код)"
            ),
            parse_mode="html",
        )
    
    logger.info(f"User {user_id} selected payment method: {method}")


async def _show_sber_payment(
    bot: MAXBot,
    user_id: int,
    plan_duration: int,
    final_price: int,
    original_price: int,
    discount_percent: int,
    config: Config,
    services: ServicesContainer = None,
) -> None:
    """
    Show Sber QR payment instructions.
    
    Args:
        bot: MAX Bot instance.
        user_id: User ID.
        plan_duration: Subscription duration in days.
        final_price: Final price after discount.
        original_price: Original price before discount.
        discount_percent: Discount percentage applied.
        config: Application configuration.
    """
    from app.bot.services.sber_payment import SberPaymentService
    
    sber_service = SberPaymentService(config)
    
    # Save payment state to FSM
    await services.fsm.update_data(user_id, {
        'payment_state': 'waiting_for_receipt',
        'payment_method': 'sber_qr',
    })
    
    # Send payment instructions
    instructions = sber_service.get_payment_instructions(final_price)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("✅ Я оплатил (прикрепить чек)", "send_receipt"),
    ])
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Отмена", "menu_subscription"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=instructions,
        parse_mode="markdown",
        reply_markup=keyboard,
    )
    
    # Send payment link button
    keyboard_link = InlineKeyboardMarkup()
    keyboard_link.add_row([
        InlineKeyboardMarkup.link_button(
            "💳 Оплатить через Сбербанк",
            sber_service.payment_url,
        ),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text="👆 Нажмите на кнопку ниже для быстрой оплаты:",
        reply_markup=keyboard_link,
    )
    
    logger.info(f"Sber payment link shown to user {user_id}, amount={final_price}₽")


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

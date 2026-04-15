"""
Receipt Handler

Handles payment receipt uploads from users.
Users send screenshot/photo of payment confirmation.
"""

import logging

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup, Update
from app.bot.models import ServicesContainer
from app.config import Config
from app.db.models.user import User

logger = logging.getLogger(__name__)


async def handle_receipt_submission(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle receipt submission (when user clicks "I paid" button).
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # Get FSM data
    fsm_data = await services.fsm.get_data(user_id)
    
    if not fsm_data or 'plan_duration' not in fsm_data:
        await bot.send_message(
            chat_id=user_id,
            text="❌ Ошибка: данные о тарифе не найдены. Выберите тариф заново.",
            parse_mode="html",
        )
        return
    
    # Update FSM state
    await services.fsm.update_data(user_id, {
        'payment_state': 'waiting_for_receipt',
    })
    
    text = (
        "📸 <b>Прикрепите чек об оплате</b>\n\n"
        "Отправьте скриншот или фото чека из приложения Сбербанк.\n\n"
        "✅ <b>Что должно быть видно на чеке:</b>\n"
        "• Сумма перевода\n"
        "• Дата и время\n"
        "• Номер получателя\n\n"
        "⏱️ После проверки администратором (обычно 5-15 минут) "
        "вам будет выдан ключ VPN."
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Отмена", "menu_subscription"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"User {user_id} prompted to send receipt")


async def handle_receipt_photo(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle receipt photo upload.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    # Check if message has photo
    if not update.message or not update.message.photo:
        return
    
    user_id = update.message.from_user.id
    
    # Check FSM state
    fsm_data = await services.fsm.get_data(user_id)
    
    if fsm_data.get('payment_state') != 'waiting_for_receipt':
        # User sent photo outside payment flow
        return
    
    # Get photo file_id (largest size)
    photo = update.message.photo[-1]
    photo_file_id = photo.file_id
    
    # Get caption if any
    caption = update.message.caption or ""
    
    # Get payment data from FSM
    plan_duration = fsm_data['plan_duration']
    original_price = fsm_data['original_price']
    final_price = fsm_data['final_price']
    discount_percent = fsm_data.get('discount_percent', 0)
    
    # Create manual payment in database
    async with config.db.session() as session:
        from app.db.models.manual_payment import ManualPayment
        
        payment = await ManualPayment.create(
            session=session,
            user_id=user_id,
            plan_duration=plan_duration,
            original_price=original_price,
            final_price=final_price,
            discount_applied=discount_percent,
            receipt_message_id=photo_file_id,
            receipt_text=caption,
        )
        
        if not payment:
            await bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка при сохранении чека. Попробуйте ещё раз.",
                parse_mode="html",
            )
            return
        
        await session.commit()
        
        # Get user info for admin notification
        user = await User.get(session, max_user_id=user_id)
        username = user.username if user else "Unknown"
    
    # Update FSM state
    await services.fsm.update_data(user_id, {
        'payment_state': 'payment_pending',
        'payment_id': payment.id,
    })
    
    # Notify user
    text = (
        "✅ <b>Чек получен!</b>\n\n"
        "Ваш чек отправлен на проверку администратору.\n\n"
        f"📋 <b>Детали платежа:</b>\n"
        f"• Тариф: {plan_duration} дней\n"
        f"• Сумма: {final_price}₽\n"
        f"• ID платежа: #{payment.id}\n\n"
        "⏱️ Ожидайте подтверждения (обычно 5-15 минут).\n"
        "После подтверждения вам будет выдан ключ VPN."
    )
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
    )
    
    # Notify admin
    admin_text = (
        f"🔔 <b>Новый чек на проверку</b>\n\n"
        f"👤 Пользователь: {user_id} (@{username})\n"
        f"💰 Сумма: {final_price}₽\n"
        f"📅 Тариф: {plan_duration} дней\n"
        f"🎫 Скидка: {discount_percent}%\n"
        f"🆔 ID платежа: #{payment.id}\n\n"
        f"📸 Чек: (photo file_id: {photo_file_id})"
    )
    
    # Send notification to all admins
    for admin_id in config.bot.ADMINS:
        try:
            # Send receipt photo to admin
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=admin_text,
                parse_mode="html",
            )
            
            # Send approval buttons
            keyboard = InlineKeyboardMarkup()
            keyboard.add_row([
                InlineKeyboardMarkup.callback_button(
                    "✅ Подтвердить",
                    f"admin_approve_{payment.id}",
                ),
                InlineKeyboardMarkup.callback_button(
                    "❌ Отклонить",
                    f"admin_reject_{payment.id}",
                ),
            ])
            
            await bot.send_message(
                chat_id=admin_id,
                text="Выберите действие:",
                reply_markup=keyboard,
            )
            
            logger.info(f"Admin {admin_id} notified about payment {payment.id}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    logger.info(
        f"Receipt received from user {user_id}, payment {payment.id} created, "
        f"amount={final_price}₽"
    )


async def handle_receipt_text(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle receipt text message (if user sends text instead of photo).
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    # Check if message has text
    if not update.message or not update.message.text:
        return
    
    user_id = update.message.from_user.id
    
    # Check FSM state
    fsm_data = await services.fsm.get_data(user_id)
    
    if fsm_data.get('payment_state') != 'waiting_for_receipt':
        return
    
    # Ask for photo instead
    await bot.send_message(
        chat_id=user_id,
        text=(
            "⚠️ Пожалуйста, отправьте <b>фото или скриншот чека</b>,\n"
            "а не текстовое сообщение.\n\n"
            "Это должен быть скриншот из приложения Сбербанк "
            "с подтверждением оплаты."
        ),
        parse_mode="html",
    )
    
    logger.info(f"User {user_id} sent text instead of receipt photo")

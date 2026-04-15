"""
Admin Payment Approval Handler

Handles admin approval/rejection of manual payments.
"""

import logging

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup, Update
from app.bot.models import ServicesContainer
from app.config import Config
from app.db.models.user import User
from app.db.models.manual_payment import ManualPayment

logger = logging.getLogger(__name__)


async def handle_admin_approve(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
    payment_id: int,
) -> None:
    """
    Handle admin payment approval.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
        payment_id: Manual payment ID to approve.
    """
    admin_id = update.callback_query.from_user.id
    
    # Check if user is admin
    if admin_id not in config.bot.ADMINS:
        await bot.answer_callback_query(
            update.callback_query.id,
            text="❌ У вас нет прав администратора",
        )
        return
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # Approve payment
    async with config.db.session() as session:
        success, message = await services.sber_payment.approve_payment(
            session=session,
            payment_id=payment_id,
            admin_id=admin_id,
        )
        
        if not success:
            await bot.send_message(
                chat_id=admin_id,
                text=f"❌ Ошибка: {message}",
                parse_mode="html",
            )
            return
        
        # Get payment details for notification
        payment = await ManualPayment.get(session, payment_id)
        user = await User.get(session, max_user_id=payment.user_id)
        
        await session.commit()
    
    # Notify admin
    await bot.send_message(
        chat_id=admin_id,
        text=(
            f"✅ <b>Платёж #{payment_id} подтверждён!</b>\n\n"
            f"👤 Пользователь: {payment.user_id}\n"
            f"💰 Сумма: {payment.final_price}₽\n"
            f"📅 Тариф: {payment.plan_duration} дней\n\n"
            f"Подписка активирована, ключ отправлен пользователю."
        ),
        parse_mode="html",
    )
    
    # Notify user
    user_text = (
        f"🎉 <b>Оплата подтверждена!</b>\n\n"
        f"Ваша подписка VPN активирована.\n\n"
        f"📋 <b>Детали:</b>\n"
        f"• Тариф: {payment.plan_duration} дней\n"
        f"• Сумма: {payment.final_price}₽\n\n"
        f"🔑 <b>Ваш ключ VPN:</b>\n"
        f"<code>Ключ будет сгенерирован после подключения 3X-UI панели</code>\n\n"
        f"📱 <b>Инструкция по подключению:</b>\n"
        f"1. Скачайте приложение V2rayNG (Android) или Shadowrocket (iOS)\n"
        f"2. Импортируйте ключ\n"
        f"3. Подключитесь\n\n"
        f"⚠️ Ключ также доступен в разделе /profile"
    )
    
    try:
        await bot.send_message(
            chat_id=payment.user_id,
            text=user_text,
            parse_mode="html",
        )
        logger.info(f"User {payment.user_id} notified about payment approval")
    except Exception as e:
        logger.error(f"Failed to notify user {payment.user_id}: {e}")
    
    logger.info(f"Payment {payment_id} approved by admin {admin_id}")


async def handle_admin_reject(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
    payment_id: int,
) -> None:
    """
    Handle admin payment rejection.
    
    Asks admin for rejection reason.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
        payment_id: Manual payment ID to reject.
    """
    admin_id = update.callback_query.from_user.id
    
    # Check if user is admin
    if admin_id not in config.bot.ADMINS:
        await bot.answer_callback_query(
            update.callback_query.id,
            text="❌ У вас нет прав администратора",
        )
        return
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # Save payment ID to FSM for rejection reason
    await services.fsm.set_data(admin_id, {
        'admin_action': 'rejecting_payment',
        'payment_id': payment_id,
    })
    
    await bot.send_message(
        chat_id=admin_id,
        text=(
            f"❌ <b>Отклонение платежа #{payment_id}</b>\n\n"
            f"Введите причину отклонения:\n"
            f"(например: неверная сумма, чек не читается и т.д.)\n\n"
            f"Или отправьте /cancel для отмены."
        ),
        parse_mode="html",
    )
    
    logger.info(f"Admin {admin_id} requested rejection reason for payment {payment_id}")


async def handle_rejection_reason(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle admin's rejection reason text.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    admin_id = update.message.from_user.id
    
    # Check FSM state
    fsm_data = await services.fsm.get_data(admin_id)
    
    if fsm_data.get('admin_action') != 'rejecting_payment':
        return
    
    payment_id = fsm_data['payment_id']
    reason = update.message.text
    
    # Reject payment
    async with config.db.session() as session:
        success, message = await services.sber_payment.reject_payment(
            session=session,
            payment_id=payment_id,
            admin_id=admin_id,
            reason=reason,
        )
        
        if not success:
            await bot.send_message(
                chat_id=admin_id,
                text=f"❌ Ошибка: {message}",
                parse_mode="html",
            )
            return
        
        # Get payment details
        payment = await ManualPayment.get(session, payment_id)
        
        await session.commit()
    
    # Clear FSM
    await services.fsm.delete_data(admin_id)
    
    # Notify admin
    await bot.send_message(
        chat_id=admin_id,
        text=f"✅ Платёж #{payment_id} отклонен с причиной: {reason}",
        parse_mode="html",
    )
    
    # Notify user
    user_text = (
        f"❌ <b>Оплата отклонена</b>\n\n"
        f"Ваш платёж #{payment_id} был отклонён.\n\n"
        f"📝 <b>Причина:</b>\n"
        f"{reason}\n\n"
        f"Если вы считаете это ошибкой, пожалуйста:\n"
        f"1. Проверьте правильность суммы\n"
        f"2. Пришлите чёткий скриншот чека\n"
        f"3. Попробуйте снова через /subscription"
    )
    
    try:
        await bot.send_message(
            chat_id=payment.user_id,
            text=user_text,
            parse_mode="html",
        )
        logger.info(f"User {payment.user_id} notified about payment rejection")
    except Exception as e:
        logger.error(f"Failed to notify user {payment.user_id}: {e}")
    
    logger.info(f"Payment {payment_id} rejected by admin {admin_id}: {reason}")


async def handle_admin_cancel_rejection(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle admin cancellation of rejection.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.message.from_user.id
    
    # Check FSM state
    fsm_data = await services.fsm.get_data(user_id)
    
    if fsm_data.get('admin_action') != 'rejecting_payment':
        return
    
    # Clear FSM
    await services.fsm.delete_data(user_id)
    
    await bot.send_message(
        chat_id=user_id,
        text="✅ Отменено. Платёж остаётся в ожидании.",
        parse_mode="html",
    )
    
    logger.info(f"Admin {user_id} cancelled payment rejection")

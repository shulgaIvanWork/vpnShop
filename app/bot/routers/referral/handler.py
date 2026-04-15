"""
Referral Handler

Handles referral program and coupon management.
"""

import logging

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup, Update
from app.bot.services import ServicesContainer
from app.config import Config
from app.db.models import User

logger = logging.getLogger(__name__)


def create_referral_keyboard() -> InlineKeyboardMarkup:
    """
    Create referral program keyboard.
    
    Returns:
        InlineKeyboardMarkup with referral options.
    """
    keyboard = InlineKeyboardMarkup()
    
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("🎁 Мои купоны", "referral_coupons"),
        InlineKeyboardMarkup.callback_button("📊 Статистика", "referral_stats"),
    ])
    
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "menu"),
    ])
    
    return keyboard


async def handle_referral(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle referral program command.
    
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
        
        if not user:
            await bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка: пользователь не найден. Используйте /start",
                parse_mode="html",
            )
            return
        
        # Get referral stats
        from app.db.models.referral import Referral
        referral_stats = await Referral.get_referrer_stats(session, user.id)
        
        # Get total discount from coupons
        from app.db.models.coupon import Coupon
        total_discount = await Coupon.get_total_user_discount(session, user.id)
    
    # Generate referral link
    bot_username = "id720212246590_1_bot"
    referral_link = f"https://max.ru/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"🎁 <b>Реферальная программа</b>\n\n"
        f"👥 Приглашено друзей: <b>{referral_stats['total_referrals']}</b>\n"
        f"✅ Получено скидок: <b>{referral_stats['rewarded']}</b>\n"
        f"⏳ Ожидается: <b>{referral_stats['pending']}</b>\n"
        f"💰 Ваша текущая скидка: <b>{total_discount}%</b>\n"
        f"📈 Максимальная скидка: <b>50%</b>\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"💡 <b>Как это работает:</b>\n"
        f"• Поделитесь ссылкой с друзьями\n"
        f"• Когда друг оплатит подписку, вы получите купон на 10%\n"
        f"• Купоны суммируются до 50%\n"
        f"• Купон действует 1 год\n\n"
        f"🎫 Ваши активные купоны можно посмотреть ниже!"
    )
    
    keyboard = create_referral_keyboard()
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Referral program shown to user {user_id}")


async def handle_referral_coupons(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle user's coupons display.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # Get user's coupons
    coupons = await services.coupon.get_user_coupons(user_id, include_used=False)
    
    if not coupons:
        text = (
            f"🎫 <b>Ваши купоны</b>\n\n"
            f"❌ У вас пока нет активных купонов\n\n"
            f"💡 Пригласите друзей, чтобы получить купоны со скидкой!"
        )
    else:
        text = f"🎫 <b>Ваши купоны ({len(coupons)})</b>\n\n"
        
        for coupon in coupons:
            status = "✅ Активен" if coupon.is_valid else "❌ Истёк"
            text += (
                f"📝 Код: <code>{coupon.code}</code>\n"
                f"💰 Скидка: {coupon.discount_percent}%\n"
                f"📅 Действует до: {coupon.valid_until.strftime('%d.%m.%Y')}\n"
                f"Статус: {status}\n\n"
            )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "referral"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Coupons shown to user {user_id}: {len(coupons) if coupons else 0}")


async def handle_referral_stats(
    bot: MAXBot,
    update: Update,
    services: ServicesContainer,
    config: Config,
) -> None:
    """
    Handle referral statistics display.
    
    Args:
        bot: MAX Bot instance.
        update: Update object.
        services: Services container.
        config: Application configuration.
    """
    user_id = update.callback_query.from_user.id
    
    await bot.answer_callback_query(update.callback_query.id)
    
    # TODO: Get actual referral statistics
    # referrals = await Referral.get_user_referrals(session, user_id)
    
    total_referrals = 0
    active_referrals = 0
    coupons_earned = 0
    
    text = (
        f"📊 <b>Реферальная статистика</b>\n\n"
        f"👥 Всего приглашено: <b>{total_referrals}</b>\n"
        f"✅ Активных рефералов: <b>{active_referrals}</b>\n"
        f"🎫 Купонов получено: <b>{coupons_earned}</b>\n\n"
        f"💡 <b>Система наград:</b>\n"
        f"• 1 реферал = 10% скидка\n"
        f"• 2 реферала = 20% скидка\n"
        f"• 3 реферала = 30% скидка\n"
        f"• 4 реферала = 40% скидка\n"
        f"• 5+ рефералов = 50% скидка (максимум)"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add_row([
        InlineKeyboardMarkup.callback_button("⬅️ Назад", "referral"),
    ])
    
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="html",
        reply_markup=keyboard,
    )
    
    logger.info(f"Referral stats shown to user {user_id}")

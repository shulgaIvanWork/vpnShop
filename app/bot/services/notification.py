"""
Notification Service

Handles all notifications to users and developers.
"""

import logging

from app.bot.max_api import MAXBot
from app.bot.max_api.types import InlineKeyboardMarkup
from app.config import Config

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications to users and developers.
    
    Handles:
    - Purchase confirmations
    - Subscription expiry warnings
    - Payment notifications
    - Error reports
    - Developer alerts
    """
    
    def __init__(self, bot: MAXBot, config: Config) -> None:
        """
        Initialize Notification Service.
        
        Args:
            bot: MAX Bot instance.
            config: Application configuration.
        """
        self.bot = bot
        self.config = config
        
        logger.info("Notification Service initialized")
    
    async def send_message(
        self,
        user_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        parse_mode: str = "html",
    ) -> bool:
        """
        Send message to user.
        
        Args:
            user_id: MAX user ID.
            text: Message text.
            reply_markup: Optional keyboard.
            parse_mode: Message format (html/markdown).
            
        Returns:
            True if message sent successfully.
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            return False
    
    async def notify_purchase_success(
        self,
        user_id: int,
        key: str,
        duration: int,
    ) -> bool:
        """
        Notify user about successful purchase.
        
        Args:
            user_id: User ID.
            key: VPN subscription key.
            duration: Subscription duration in days.
            
        Returns:
            True if notification sent.
        """
        text = (
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"🎉 Ваша VPN подписка активирована\n"
            f"📅 Срок: {duration} дней\n\n"
            f"🔑 <b>Ваш ключ доступа:</b>\n"
            f"<code>{key}</code>\n\n"
            f"📱 <b>Инструкция по подключению:</b>\n"
            f"1. Скачайте приложение V2rayNG (Android) или V2rayU (iOS)\n"
            f"2. Нажмите '+' → 'Import from clipboard'\n"
            f"3. Подключитесь к серверу\n\n"
            f"💡 Если возникнут вопросы - нажмите /support"
        )
        
        return await self.send_message(user_id, text, parse_mode="html")
    
    async def notify_extend_success(
        self,
        user_id: int,
        duration: int,
    ) -> bool:
        """
        Notify user about successful subscription extension.
        
        Args:
            user_id: User ID.
            duration: Extension duration in days.
            
        Returns:
            True if notification sent.
        """
        text = (
            f"✅ <b>Подписка продлена!</b>\n\n"
            f"📅 Добавлено: {duration} дней\n"
            f"💡 Ваш ключ доступа не изменился\n\n"
            f"Приятного использования! 🚀"
        )
        
        return await self.send_message(user_id, text, parse_mode="html")
    
    async def notify_expiry_warning(
        self,
        user_id: int,
        days_left: int,
    ) -> bool:
        """
        Warn user about subscription expiry.
        
        Args:
            user_id: User ID.
            days_left: Days remaining.
            
        Returns:
            True if notification sent.
        """
        text = (
            f"⚠️ <b>Внимание! Подписка истекает</b>\n\n"
            f"📅 До окончания: {days_left} дней\n\n"
            f"💡 Продлите подписку, чтобы не потерять доступ:\n"
            f"Нажмите /subscription для выбора тарифа"
        )
        
        return await self.send_message(user_id, text, parse_mode="html")
    
    async def notify_developer(self, text: str) -> bool:
        """
        Send notification to developer/admin.
        
        Args:
            text: Notification text.
            
        Returns:
            True if notification sent.
        """
        if not self.config.bot.ADMINS:
            logger.warning("No admins configured, skipping developer notification")
            return False
        
        # Send to first admin (developer)
        admin_id = self.config.bot.ADMINS[0]
        
        try:
            await self.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="html",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to notify developer: {e}")
            return False
    
    async def notify_coupon_received(
        self,
        user_id: int,
        coupon_code: str,
        discount_percent: int,
    ) -> bool:
        """
        Notify user about receiving a coupon.
        
        Args:
            user_id: User ID.
            coupon_code: Coupon code.
            discount_percent: Discount percentage.
            
        Returns:
            True if notification sent.
        """
        text = (
            f"🎁 <b>Вам начислен купон!</b>\n\n"
            f"📝 Код: <code>{coupon_code}</code>\n"
            f"💰 Скидка: {discount_percent}%\n"
            f"📅 Действует 1 год\n\n"
            f"Используйте купон при следующей оплате!"
        )
        
        return await self.send_message(user_id, text, parse_mode="html")
    
    async def notify_referral_success(
        self,
        user_id: int,
        referral_count: int,
    ) -> bool:
        """
        Notify user about successful referral.
        
        Args:
            user_id: User ID.
            referral_count: Total referrals count.
            
        Returns:
            True if notification sent.
        """
        text = (
            f"🎉 <b>Реферал активирован!</b>\n\n"
            f"👥 Всего приглашено: {referral_count}\n"
            f"💰 Ваша скидка: {referral_count * 10}%\n\n"
            f"Продолжайте приглашать друзей! "
            f"Максимальная скидка: 50%"
        )
        
        return await self.send_message(user_id, text, parse_mode="html")

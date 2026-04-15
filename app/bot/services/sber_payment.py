"""
Sber QR Payment Service.

Handles manual payment flow via Sber QR code.
Users send payment receipt screenshots, admin approves/rejects.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Config
from app.db.models.manual_payment import ManualPayment
from app.db.models.user import User

logger = logging.getLogger(__name__)


class SberPaymentService:
    """Service for managing Sber QR manual payments."""
    
    def __init__(self, config: Config):
        self.config = config
        self.payment_url = config.sber.PAYMENT_URL
        self.phone_number = config.sber.PHONE_NUMBER
        self.receipt_name = config.sber.RECEIPT_NAME
    
    def get_payment_details(self) -> dict[str, str]:
        """Get Sber payment details for display."""
        return {
            "phone": self.phone_number,
            "name": self.receipt_name,
            "payment_url": self.payment_url,
        }
    
    def get_payment_instructions(self, amount: int) -> str:
        """
        Generate payment instructions text.
        
        Args:
            amount: Payment amount in rubles.
        
        Returns:
            Formatted instruction text.
        """
        return (
            f"💳 *Оплата через Сбербанк*\n\n"
            f"💰 *Сумма:* {amount}₽\n\n"
            f"🔗 *Ссылка для оплаты:*\n"
            f"{self.payment_url}\n\n"
            f"📱 *Или по номеру телефона:*\n"
            f"• Телефон: `{self.phone_number}`\n"
            f"• Получатель: {self.receipt_name}\n\n"
            f"📋 *Инструкция:*\n"
            f"1. Перейдите по ссылке выше ИЛИ\n"
            f"2. Откройте Сбербанк → Платежи → По номеру телефона\n"
            f"3. Введите номер {self.phone_number} и сумму {amount}₽\n"
            f"4. Оплатите и прикрепите чек сюда\n\n"
            f"⏱️ После проверки администратором вам будет выдан ключ VPN"
        )
    
    async def create_manual_payment(
        self,
        session: AsyncSession,
        user_id: int,
        plan_duration: int,
        original_price: int,
        final_price: int,
        discount_applied: int = 0,
        receipt_message_id: str = None,
        receipt_text: str = None,
    ) -> ManualPayment | None:
        """
        Create a new manual payment record.
        
        Args:
            session: Database session.
            user_id: User ID making the payment.
            plan_duration: Subscription duration in days.
            original_price: Price before discount.
            final_price: Price after discount.
            discount_applied: Discount percentage applied.
            receipt_message_id: MAX message ID with receipt.
            receipt_text: User's comment with payment.
        
        Returns:
            ManualPayment instance or None if failed.
        """
        payment = await ManualPayment.create(
            session=session,
            user_id=user_id,
            plan_duration=plan_duration,
            original_price=original_price,
            final_price=final_price,
            discount_applied=discount_applied,
            receipt_message_id=receipt_message_id,
            receipt_text=receipt_text,
        )
        
        if payment:
            logger.info(
                f"Manual payment created: {payment.id} for user {user_id}, "
                f"amount={final_price}₽, duration={plan_duration} days"
            )
        
        return payment
    
    async def approve_payment(
        self,
        session: AsyncSession,
        payment_id: int,
        admin_id: int,
    ) -> tuple[bool, str]:
        """
        Approve a manual payment and activate subscription.
        
        Args:
            session: Database session.
            payment_id: Manual payment ID to approve.
            admin_id: Admin ID approving the payment.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get payment
        payment = await ManualPayment.get(session, payment_id)
        if not payment:
            return False, "Платёж не найден"
        
        if payment.status != "pending":
            return False, f"Платёж уже {payment.status}"
        
        # Approve payment
        approved = await ManualPayment.approve(session, payment_id, admin_id)
        if not approved:
            return False, "Ошибка при подтверждении"
        
        # Get user
        user = await User.get(session, payment.user_id)
        if not user:
            return False, "Пользователь не найден"
        
        # Calculate subscription end date
        subscription_end = datetime.now() + timedelta(days=payment.plan_duration)
        
        # TODO: Create VPN client in 3X-UI panel
        # For now, just update user subscription
        # uuid = await vpn_service.create_client(...)
        
        # Update user subscription
        await user.update_subscription(
            session=session,
            subscription_end=subscription_end,
            # uuid=uuid,  # Will be set when 3X-UI is integrated
            # assigned_server=server_ip,  # Will be set when server pool is ready
        )
        
        await session.commit()
        
        logger.info(
            f"Payment {payment_id} approved by admin {admin_id}. "
            f"User {user.max_user_id} subscription activated until {subscription_end}"
        )
        
        return True, "Оплата подтверждена, подписка активирована"
    
    async def reject_payment(
        self,
        session: AsyncSession,
        payment_id: int,
        admin_id: int,
        reason: str = None,
    ) -> tuple[bool, str]:
        """
        Reject a manual payment.
        
        Args:
            session: Database session.
            payment_id: Manual payment ID to reject.
            admin_id: Admin ID rejecting the payment.
            reason: Reason for rejection.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get payment
        payment = await ManualPayment.get(session, payment_id)
        if not payment:
            return False, "Платёж не найден"
        
        if payment.status != "pending":
            return False, f"Платёж уже {payment.status}"
        
        # Reject payment
        rejected = await ManualPayment.reject(session, payment_id, admin_id, reason)
        if not rejected:
            return False, "Ошибка при отклонении"
        
        await session.commit()
        
        logger.info(
            f"Payment {payment_id} rejected by admin {admin_id}. "
            f"Reason: {reason or 'Not specified'}"
        )
        
        return True, "Оплата отклонена"

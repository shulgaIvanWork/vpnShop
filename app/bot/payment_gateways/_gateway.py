"""
Payment Gateway Base Class

Abstract base class for all payment gateways.
Provides common functionality for payment processing.
"""

import logging
from abc import ABC, abstractmethod

from aiohttp.web import Application
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.max_api import MAXBot
from app.bot.models import ServicesContainer, SubscriptionData
from app.bot.utils.constants import (
    EVENT_PAYMENT_CANCELED_TAG,
    EVENT_PAYMENT_SUCCEEDED_TAG,
    Currency,
    TransactionStatus,
)
from app.config import Config
from app.db.models import Payment, User

logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    """
    Abstract base class for payment gateways.
    
    All payment gateways (YooKassa, YooMoney) must inherit from this class
    and implement the abstract methods.
    """
    
    name: str
    currency: Currency
    callback: str
    
    def __init__(
        self,
        app: Application,
        config: Config,
        session: async_sessionmaker,
        bot: MAXBot,
        services: ServicesContainer,
    ) -> None:
        """
        Initialize payment gateway.
        
        Args:
            app: aiohttp web application.
            config: Application configuration.
            session: SQLAlchemy async session maker.
            bot: MAX Bot instance.
            services: Services container.
        """
        self.app = app
        self.config = config
        self.session = session
        self.bot = bot
        self.services = services
    
    @abstractmethod
    async def create_payment(self, data: SubscriptionData) -> str:
        """
        Create a payment and return payment URL.
        
        Args:
            data: Subscription data with user info and plan details.
            
        Returns:
            Payment URL for user to complete payment.
        """
        pass
    
    @abstractmethod
    async def handle_payment_succeeded(self, payment_id: str) -> None:
        """
        Handle successful payment.
        
        Args:
            payment_id: Payment identifier from gateway.
        """
        pass
    
    @abstractmethod
    async def handle_payment_canceled(self, payment_id: str) -> None:
        """
        Handle canceled payment.
        
        Args:
            payment_id: Payment identifier from gateway.
        """
        pass
    
    async def _on_payment_succeeded(self, payment_id: str) -> None:
        """
        Internal handler for successful payment.
        
        Processes the payment, creates/extends subscription, and notifies user.
        
        Args:
            payment_id: Payment identifier.
        """
        logger.info(f"Payment succeeded: {payment_id}")
        
        async with self.session() as session:
            # Get payment record
            payment = await Payment.get_by_payment_gateway_id(
                session=session,
                gateway_payment_id=payment_id,
            )
            
            if not payment:
                logger.error(f"Payment {payment_id} not found in database")
                return
            
            # Unpack subscription data
            data = SubscriptionData.unpack(payment.user_id)
            logger.debug(f"Subscription data unpacked for user {payment.user_id}")
            
            # Get user
            user = await User.get(session=session, max_user_id=data.user_id)
            if not user:
                logger.error(f"User {data.user_id} not found")
                return
            
            # Update payment status
            await Payment.update_status(
                session=session,
                payment_id=payment.id,
                status=TransactionStatus.SUCCEEDED.value,
            )
            
            # Issue referral reward if enabled
            if payment.discount_applied == 0:  # Only if no coupon was used
                await self._process_referral_reward(session, user, data)
        
        # Notify developer
        await self.services.notification.notify_developer(
            text=EVENT_PAYMENT_SUCCEEDED_TAG + "\n\n"
            f"💰 Payment Succeeded\n"
            f"Payment ID: {payment_id}\n"
            f"User ID: {user.max_user_id}\n"
            f"Duration: {payment.plan_duration} days\n"
            f"Amount: {payment.amount} {payment.currency}\n"
            f"Discount: {payment.discount_applied}%"
        )
        
        # Create or extend subscription
        try:
            success = await self.services.vpn.create_subscription(
                user=user,
                devices=user.device_limit,
                duration=payment.plan_duration,
            )
            
            if success:
                logger.info(f"Subscription created for user {user.max_user_id}")
                key = await self.services.vpn.get_key(user)
                await self.services.notification.notify_purchase_success(
                    user_id=user.max_user_id,
                    key=key,
                    duration=payment.plan_duration,
                )
            else:
                logger.error(f"Failed to create subscription for user {user.max_user_id}")
                
        except Exception as e:
            logger.error(f"Error processing payment {payment_id}: {e}")
    
    async def _on_payment_canceled(self, payment_id: str) -> None:
        """
        Internal handler for canceled payment.
        
        Args:
            payment_id: Payment identifier.
        """
        logger.info(f"Payment canceled: {payment_id}")
        
        async with self.session() as session:
            payment = await Payment.get_by_payment_gateway_id(
                session=session,
                gateway_payment_id=payment_id,
            )
            
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return
            
            # Update payment status
            await Payment.update_status(
                session=session,
                payment_id=payment.id,
                status=TransactionStatus.CANCELLED.value,
            )
        
        # Notify developer
        await self.services.notification.notify_developer(
            text=EVENT_PAYMENT_CANCELED_TAG + "\n\n"
            f"❌ Payment Canceled\n"
            f"Payment ID: {payment_id}\n"
            f"User ID: {payment.user_id}\n"
            f"Amount: {payment.amount} {payment.currency}"
        )
    
    async def _process_referral_reward(
        self,
        session,
        user: User,
        data: SubscriptionData,
    ) -> None:
        """
        Process referral reward for the user who invited this customer.
        
        Args:
            session: Database session.
            user: User who made the payment.
            data: Subscription data.
        """
        try:
            # Check if user was referred
            referral = user.referral
            if not referral or referral.reward_issued:
                return
            
            # Create coupon for referrer (10% discount)
            from app.db.models import Coupon
            
            coupon = await Coupon.create(
                session=session,
                user_id=referral.referrer_id,
                discount_percent=10,
                valid_days=365,
            )
            
            if coupon:
                # Mark referral reward as issued
                from app.db.models import Referral
                
                await Referral.mark_reward_issued(
                    session=session,
                    referral_id=referral.id,
                    coupon_code=coupon.code,
                )
                
                # Notify referrer
                await self.services.notification.notify_developer(
                    f"🎁 Referral Reward\n"
                    f"Referrer received coupon: {coupon.code}\n"
                    f"Discount: {coupon.discount_percent}%\n"
                    f"Valid until: {coupon.valid_until.strftime('%Y-%m-%d')}"
                )
                
                logger.info(
                    f"Referral reward issued: coupon {coupon.code} "
                    f"for referrer {referral.referrer_id}"
                )
                
        except Exception as e:
            logger.error(f"Error processing referral reward: {e}")

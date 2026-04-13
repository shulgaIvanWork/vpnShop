"""
YooKassa Payment Gateway

Integration with YooKassa payment system.
Documentation: https://yookassa.ru/developers/api
"""

import logging

from aiohttp.web import Application, Request, Response
from sqlalchemy.ext.asyncio import async_sessionmaker
from yookassa import Configuration, Payment
from yookassa.domain.common import SecurityHelper
from yookassa.domain.common.confirmation_type import ConfirmationType
from yookassa.domain.models.receipt import Receipt, ReceiptItem
from yookassa.domain.notification import (
    WebhookNotificationEventType,
    WebhookNotificationFactory,
)
from yookassa.domain.request.payment_request import PaymentRequest

from app.bot.max_api import MAXBot
from app.bot.models import ServicesContainer, SubscriptionData
from app.bot.payment_gateways import PaymentGateway
from app.bot.utils.constants import YOOKASSA_WEBHOOK, Currency
from app.config import Config
from app.db.models import Payment as PaymentModel

logger = logging.getLogger(__name__)


class Yookassa(PaymentGateway):
    """YooKassa payment gateway implementation."""
    
    name = "ЮKassa"
    currency = Currency.RUB
    callback = "pay_yookassa"
    
    def __init__(
        self,
        app: Application,
        config: Config,
        session: async_sessionmaker,
        bot: MAXBot,
        services: ServicesContainer,
    ) -> None:
        """
        Initialize YooKassa payment gateway.
        
        Args:
            app: aiohttp web application.
            config: Application configuration.
            session: SQLAlchemy session maker.
            bot: MAX Bot instance.
            services: Services container.
        """
        self.app = app
        self.config = config
        self.session = session
        self.bot = bot
        self.services = services
        
        # Configure YooKassa
        Configuration.configure(self.config.yookassa.SHOP_ID, self.config.yookassa.TOKEN)
        
        # Register webhook handler
        self.app.router.add_post(YOOKASSA_WEBHOOK, self.webhook_handler)
        
        logger.info("YooKassa payment gateway initialized.")
    
    async def create_payment(self, data: SubscriptionData) -> str:
        """
        Create YooKassa payment.
        
        Args:
            data: Subscription data with user info and plan details.
            
        Returns:
            Payment URL for user to complete payment.
        """
        # Redirect URL back to MAX bot
        redirect_url = self.config.bot.DOMAIN
        
        # Payment description
        description = f"VPN подписка: {data.duration} дней"
        
        # Calculate price with discount
        price = data.price
        if data.discount_percent > 0:
            discount_amount = price * data.discount_percent / 100
            price = price - discount_amount
            logger.info(
                f"Discount applied: {data.discount_percent}% "
                f"({discount_amount} RUB) for user {data.user_id}"
            )
        
        price_str = f"{price:.2f}"
        
        # Create receipt
        receipt = Receipt(
            customer={"email": self.config.shop.EMAIL},
            items=[
                ReceiptItem(
                    description=description,
                    quantity=1,
                    amount={"value": price_str, "currency": self.currency.code},
                    vat_code=1,
                )
            ],
        )
        
        # Create payment request
        request = PaymentRequest(
            amount={"value": price_str, "currency": self.currency.code},
            confirmation={"type": ConfirmationType.REDIRECT, "return_url": redirect_url},
            capture=True,
            save_payment_method=False,
            description=description,
            receipt=receipt,
        )
        
        # Create payment in YooKassa
        response = Payment.create(request)
        
        # Save payment to database
        async with self.session() as session:
            await PaymentModel.create(
                session=session,
                user_id=data.user_id,
                amount=price,
                currency=self.currency.code,
                status="pending",
                payment_method="yookassa",
                yookassa_payment_id=response.id,
                plan_duration=data.duration,
                discount_applied=data.discount_percent,
                coupon_code=data.coupon_code,
            )
        
        pay_url = response.confirmation["confirmation_url"]
        logger.info(f"YooKassa payment link created for user {data.user_id}: {pay_url}")
        
        return pay_url
    
    async def handle_payment_succeeded(self, payment_id: str) -> None:
        """Handle successful YooKassa payment."""
        await self._on_payment_succeeded(payment_id)
    
    async def handle_payment_canceled(self, payment_id: str) -> None:
        """Handle canceled YooKassa payment."""
        await self._on_payment_canceled(payment_id)
    
    async def webhook_handler(self, request: Request) -> Response:
        """
        Handle YooKassa webhook notifications.
        
        Verifies IP address and processes payment events.
        """
        # Verify IP address
        ip = request.headers.get("X-Forwarded-For", request.remote)
        
        if not SecurityHelper().is_ip_trusted(ip):
            logger.warning(f"Untrusted IP address: {ip}")
            return Response(status=403)
        
        try:
            # Parse webhook data
            event_json = await request.json()
            notification_object = WebhookNotificationFactory().create(event_json)
            response_object = notification_object.object
            payment_id = response_object.id
            
            # Process event
            match notification_object.event:
                case WebhookNotificationEventType.PAYMENT_SUCCEEDED:
                    await self.handle_payment_succeeded(payment_id)
                    return Response(status=200)
                
                case WebhookNotificationEventType.PAYMENT_CANCELED:
                    await self.handle_payment_canceled(payment_id)
                    return Response(status=200)
                
                case _:
                    logger.warning(f"Unknown YooKassa event: {notification_object.event}")
                    return Response(status=400)
        
        except Exception as exception:
            logger.exception(f"Error processing YooKassa webhook: {exception}")
            return Response(status=400)

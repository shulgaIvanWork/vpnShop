"""
YooMoney Payment Gateway

Integration with YooMoney payment system.
Documentation: https://yoomoney.ru/docs/wallet/payment-api/quickstart
"""

import hashlib
import logging
import uuid

import requests
from aiohttp.web import Application, Request, Response
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.max_api import MAXBot
from app.bot.models import ServicesContainer, SubscriptionData
from app.bot.payment_gateways import PaymentGateway
from app.bot.utils.constants import YOOMONEY_WEBHOOK, Currency
from app.config import Config
from app.db.models import Payment as PaymentModel

logger = logging.getLogger(__name__)


class Yoomoney(PaymentGateway):
    """YooMoney payment gateway implementation."""
    
    name = "YooMoney"
    currency = Currency.RUB
    callback = "pay_yoomoney"
    
    def __init__(
        self,
        app: Application,
        config: Config,
        session: async_sessionmaker,
        bot: MAXBot,
        services: ServicesContainer,
    ) -> None:
        """
        Initialize YooMoney payment gateway.
        
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
        
        # Register webhook handler
        self.app.router.add_post(YOOMONEY_WEBHOOK, self.webhook_handler)
        
        logger.info("YooMoney payment gateway initialized.")
    
    async def create_payment(self, data: SubscriptionData) -> str:
        """
        Create YooMoney payment.
        
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
        payment_id = str(uuid.uuid4())
        
        # Create YooMoney payment URL
        pay_url = self._create_quickpay_url(
            receiver=self.config.yoomoney.WALLET_ID,
            quickpay_form="shop",
            targets=description,
            payment_type="SB",
            sum=price,
            label=payment_id,
            success_url=redirect_url,
        )
        
        # Save payment to database
        async with self.session() as session:
            await PaymentModel.create(
                session=session,
                user_id=data.user_id,
                amount=price,
                currency=self.currency.code,
                status="pending",
                payment_method="yoomoney",
                yoomoney_payment_id=payment_id,
                plan_duration=data.duration,
                discount_applied=data.discount_percent,
                coupon_code=data.coupon_code,
            )
        
        logger.info(f"YooMoney payment link created for user {data.user_id}: {pay_url}")
        
        return pay_url
    
    async def handle_payment_succeeded(self, payment_id: str) -> None:
        """Handle successful YooMoney payment."""
        await self._on_payment_succeeded(payment_id)
    
    async def handle_payment_canceled(self, payment_id: str) -> None:
        """Handle canceled YooMoney payment."""
        await self._on_payment_canceled(payment_id)
    
    async def webhook_handler(self, request: Request) -> Response:
        """
        Handle YooMoney webhook notifications.
        
        Verifies notification signature and processes payment.
        """
        try:
            # Parse form data
            event_data = await request.post()
            logger.debug(f"YooMoney webhook data: {dict(event_data)}")
            
            # Verify notification signature
            if not self._verify_notification(event_data):
                logger.error("YooMoney signature verification failed")
                return Response(status=403)
            
            logger.debug("YooMoney signature verified successfully")
            
            # Process payment
            payment_id = event_data.get("label")
            await self.handle_payment_succeeded(payment_id)
            
            return Response(status=200)
        
        except Exception as exception:
            logger.exception(f"Error processing YooMoney webhook: {exception}")
            return Response(status=400)
    
    def _create_quickpay_url(
        self,
        receiver: str,
        quickpay_form: str,
        targets: str,
        payment_type: str,
        sum: float,
        label: str = None,
        success_url: str = None,
    ) -> str:
        """
        Create YooMoney QuickPay URL.
        
        Args:
            receiver: Wallet ID.
            quickpay_form: Form type (shop).
            targets: Payment description.
            payment_type: Payment type (SB for card).
            sum: Payment amount.
            label: Payment label (our payment_id).
            success_url: Redirect URL after payment.
            
        Returns:
            QuickPay URL.
        """
        base_url = "https://yoomoney.ru/quickpay/confirm.xml?"
        payload = {
            "receiver": receiver,
            "quickpay_form": quickpay_form,
            "targets": targets,
            "paymentType": payment_type,
            "sum": sum,
            "label": label,
            "successURL": success_url,
        }
        
        # Build query string
        query = "&".join(
            f"{key.replace('_', '-')}={str(value)}"
            for key, value in payload.items()
            if value is not None
        ).replace(" ", "%20")
        
        response = requests.post(base_url + query)
        return response.url
    
    def _verify_notification(self, data: dict) -> bool:
        """
        Verify YooMoney notification signature.
        
        Args:
            data: Notification data.
            
        Returns:
            True if signature is valid.
        """
        params = [
            data.get("notification_type", ""),
            data.get("operation_id", ""),
            data.get("amount", ""),
            data.get("currency", ""),
            data.get("datetime", ""),
            data.get("sender", ""),
            data.get("codepro", ""),
            self.config.yoomoney.NOTIFICATION_SECRET,
            data.get("label", ""),
        ]
        
        # Build signature string
        sign_str = "&".join(params)
        computed_hash = hashlib.sha1(sign_str.encode("utf-8")).hexdigest()
        
        # Verify signature
        is_valid = computed_hash == data.get("sha1_hash", "")
        
        if not is_valid:
            logger.warning(
                f"Invalid YooMoney signature. "
                f"Expected {computed_hash}, received {data.get('sha1_hash')}."
            )
        
        return is_valid

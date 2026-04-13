"""
Subscription Data Model

Pydantic model for subscription data passed between handlers and payment gateways.
"""

import json
import logging
from dataclasses import asdict, dataclass
from typing import Self

logger = logging.getLogger(__name__)


@dataclass
class SubscriptionData:
    """
    Subscription data for payment processing.
    
    Attributes:
        user_id: MAX user ID.
        duration: Subscription duration in days.
        price: Original price before discount.
        final_price: Final price after discount.
        devices: Number of allowed devices.
        discount_percent: Discount percentage (0-50).
        coupon_code: Applied coupon code (if any).
        payment_method: Selected payment method (yookassa/yoomoney).
        is_extend: True if extending existing subscription.
        is_change: True if changing subscription plan.
    """
    user_id: int
    duration: int
    price: float
    final_price: float
    devices: int = 1
    discount_percent: int = 0
    coupon_code: str | None = None
    payment_method: str = "yookassa"
    is_extend: bool = False
    is_change: bool = False
    
    def pack(self) -> str:
        """Pack subscription data to JSON string for storage."""
        return json.dumps(asdict(self))
    
    @classmethod
    def unpack(cls, user_id: int) -> Self:
        """
        Unpack subscription data from user's session/data.
        This is a placeholder - actual implementation will retrieve from FSM state.
        """
        # TODO: Retrieve from FSM state or database
        logger.warning(f"SubscriptionData.unpack called - using default data for user {user_id}")
        return cls(
            user_id=user_id,
            duration=30,
            price=299.0,
            final_price=299.0,
            devices=1,
        )
    
    @classmethod
    def create(
        cls,
        user_id: int,
        duration: int,
        price: float,
        devices: int = 1,
        discount_percent: int = 0,
        coupon_code: str | None = None,
        payment_method: str = "yookassa",
    ) -> Self:
        """
        Create subscription data with automatic price calculation.
        
        Args:
            user_id: MAX user ID.
            duration: Subscription duration in days.
            price: Original price.
            devices: Number of devices.
            discount_percent: Discount percentage.
            coupon_code: Coupon code if applied.
            payment_method: Payment gateway.
            
        Returns:
            SubscriptionData instance.
        """
        final_price = price
        if discount_percent > 0:
            discount_amount = price * discount_percent / 100
            final_price = price - discount_amount
            logger.info(
                f"Discount applied: {discount_percent}% "
                f"(-{discount_amount:.2f} RUB) for user {user_id}"
            )
        
        return cls(
            user_id=user_id,
            duration=duration,
            price=price,
            final_price=final_price,
            devices=devices,
            discount_percent=discount_percent,
            coupon_code=coupon_code,
            payment_method=payment_method,
        )

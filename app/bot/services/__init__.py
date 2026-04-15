"""
Services Container

Central container for all bot services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.config import Config
    from app.bot.max_api import MAXBot
    
    from app.bot.services.vpn import VPNService
    from app.bot.services.notification import NotificationService
    from app.bot.services.coupon import CouponService


@dataclass
class ServicesContainer:
    """
    Container for all bot services.
    
    Provides centralized access to services used across handlers.
    """
    vpn: "VPNService"
    notification: "NotificationService"
    coupon: "CouponService"
    fsm: "FSMStorage"  # FSM storage for payment flow
    sber_payment: "SberPaymentService"  # Sber QR payment service
    
    @classmethod
    def create(
        cls,
        config: "Config",
        bot: "MAXBot",
        session: "async_sessionmaker",
    ) -> "ServicesContainer":
        """
        Create ServicesContainer with all services initialized.
        
        Args:
            config: Application configuration.
            bot: MAX Bot instance.
            session: SQLAlchemy async session maker.
            
        Returns:
            Initialized ServicesContainer.
        """
        from app.bot.services.vpn import VPNService
        from app.bot.services.notification import NotificationService
        from app.bot.services.coupon import CouponService
        from app.bot.services.sber_payment import SberPaymentService
        from app.bot.fsm.storage import create_fsm_storage
        
        # Create FSM storage (use Redis if available, otherwise memory)
        fsm = create_fsm_storage(
            use_redis=False,  # Set to True when Redis is running
            redis_url=config.redis.url(),
        )
        
        return cls(
            vpn=VPNService(config=config, session=session),
            notification=NotificationService(bot=bot, config=config),
            coupon=CouponService(session=session),
            fsm=fsm,
            sber_payment=SberPaymentService(config=config),
        )

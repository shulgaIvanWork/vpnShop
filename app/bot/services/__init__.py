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
        
        return cls(
            vpn=VPNService(config=config, session=session),
            notification=NotificationService(bot=bot, config=config),
            coupon=CouponService(session=session),
        )

"""
Coupon Service

Manages discount coupons for the referral system.
"""

import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import Coupon, User

logger = logging.getLogger(__name__)


class CouponService:
    """
    Service for managing discount coupons.
    
    Handles:
    - Coupon creation
    - Coupon validation
    - Coupon application
    - User coupon management
    """
    
    def __init__(self, session: async_sessionmaker) -> None:
        """
        Initialize Coupon Service.
        
        Args:
            session: SQLAlchemy async session maker.
        """
        self.session = session
        
        logger.info("Coupon Service initialized")
    
    async def create_coupon(
        self,
        user_id: int,
        discount_percent: int = 10,
        valid_days: int = 365,
    ) -> Coupon | None:
        """
        Create a new coupon for user.
        
        Args:
            user_id: User ID to create coupon for.
            discount_percent: Discount percentage (10-50).
            valid_days: Validity period in days.
            
        Returns:
            Created coupon or None if failed.
        """
        async with self.session() as session:
            coupon = await Coupon.create(
                session=session,
                user_id=user_id,
                discount_percent=discount_percent,
                valid_days=valid_days,
            )
            
            if coupon:
                logger.info(
                    f"Coupon created: {coupon.code} for user {user_id} "
                    f"({discount_percent}%)"
                )
            
            return coupon
    
    async def validate_coupon(
        self,
        code: str,
        user_id: int,
    ) -> tuple[bool, Coupon | None, str]:
        """
        Validate coupon code.
        
        Args:
            code: Coupon code.
            user_id: User attempting to use it.
            
        Returns:
            Tuple of (is_valid, coupon_or_none, error_message).
        """
        async with self.session() as session:
            coupon = await Coupon.get(session, code)
            
            if not coupon:
                return False, None, "Купон не найден"
            
            if coupon.user_id != user_id:
                return False, None, "Купон принадлежит другому пользователю"
            
            if coupon.used:
                return False, None, "Купон уже использован"
            
            if not coupon.is_valid:
                return False, None, "Купон истёк"
            
            return True, coupon, ""
    
    async def apply_coupon(
        self,
        code: str,
        user_id: int,
        original_price: float,
    ) -> tuple[bool, float, str]:
        """
        Apply coupon to get discount.
        
        Args:
            code: Coupon code.
            user_id: User ID.
            original_price: Original price.
            
        Returns:
            Tuple of (success, final_price, error_message).
        """
        is_valid, coupon, error = await self.validate_coupon(code, user_id)
        
        if not is_valid:
            return False, original_price, error
        
        # Calculate discount
        discount_amount = original_price * coupon.discount_percent / 100
        final_price = original_price - discount_amount
        
        logger.info(
            f"Coupon {code} applied: {coupon.discount_percent}% discount "
            f"(-{discount_amount:.2f} RUB)"
        )
        
        return True, final_price, ""
    
    async def mark_coupon_used(self, code: str) -> bool:
        """
        Mark coupon as used.
        
        Args:
            code: Coupon code.
            
        Returns:
            True if marked successfully.
        """
        async with self.session() as session:
            return await Coupon.use(session, code)
    
    async def get_user_coupons(
        self,
        user_id: int,
        include_used: bool = False,
    ) -> list[Coupon]:
        """
        Get all coupons for user.
        
        Args:
            user_id: User ID.
            include_used: Include used coupons.
            
        Returns:
            List of coupons.
        """
        async with self.session() as session:
            if include_used:
                return await Coupon.get_user_coupons(session, user_id, include_used=True)
            else:
                return await Coupon.get_user_active_coupons(session, user_id)
    
    async def get_user_coupon_count(self, user_id: int) -> int:
        """
        Get count of active coupons for user.
        
        Args:
            user_id: User ID.
            
        Returns:
            Number of active coupons.
        """
        coupons = await self.get_user_coupons(user_id, include_used=False)
        return len(coupons)

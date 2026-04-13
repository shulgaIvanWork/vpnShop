import logging
import secrets
from datetime import datetime, timedelta
from typing import Self

from sqlalchemy import ForeignKey, Integer, String, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

logger = logging.getLogger(__name__)


class Coupon(Base):
    """
    Represents a discount coupon in the MAX VPN shop.

    Attributes:
        code (str): Unique coupon code (primary key).
        user_id (int): User who owns this coupon.
        discount_percent (int): Discount percentage (10-50).
        valid_until (datetime): Expiration timestamp.
        used (bool): Whether coupon has been used.
        used_at (datetime | None): Timestamp when coupon was used.
        created_at (datetime): Timestamp when coupon was created.
        user (User): User who owns the coupon.
    """

    __tablename__ = "coupons"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    discount_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(nullable=False)
    used: Mapped[bool] = mapped_column(default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="coupons")

    def __repr__(self) -> str:
        return (
            f"<Coupon(code='{self.code}', user_id={self.user_id}, "
            f"discount={self.discount_percent}%, used={self.used})>"
        )

    @property
    def is_valid(self) -> bool:
        """Check if coupon is still valid."""
        return not self.used and datetime.now() < self.valid_until

    @staticmethod
    def generate_code(length: int = 12) -> str:
        """Generate a secure random coupon code."""
        return f"VPN-{secrets.token_urlsafe(length).upper()[:length]}"

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_id: int,
        discount_percent: int,
        valid_days: int = 365,
    ) -> Self | None:
        """
        Create a new coupon.

        Args:
            session: Database session.
            user_id: User ID who will own the coupon.
            discount_percent: Discount percentage (10-50).
            valid_days: Number of days until expiration (default: 365).

        Returns:
            Coupon instance or None if failed.
        """
        if not (10 <= discount_percent <= 50):
            logger.error(f"Invalid discount percent: {discount_percent}. Must be 10-50.")
            return None

        code = cls.generate_code()
        valid_until = datetime.now() + timedelta(days=valid_days)

        coupon = cls(
            code=code,
            user_id=user_id,
            discount_percent=discount_percent,
            valid_until=valid_until,
        )
        session.add(coupon)

        try:
            await session.commit()
            logger.info(
                f"Coupon created: {code} for user {user_id} "
                f"({discount_percent}% valid for {valid_days} days)"
            )
            return coupon
        except Exception as exception:
            await session.rollback()
            logger.error(f"Error creating coupon: {exception}")
            return None

    @classmethod
    async def get(cls, session: AsyncSession, code: str) -> Self | None:
        """Get coupon by code."""
        query = await session.execute(select(Coupon).where(Coupon.code == code))
        coupon = query.scalar_one_or_none()

        if coupon:
            logger.debug(f"Coupon {code} retrieved from database.")
        else:
            logger.debug(f"Coupon {code} not found.")

        return coupon

    @classmethod
    async def validate(cls, session: AsyncSession, code: str, user_id: int) -> bool:
        """
        Validate if coupon can be used.

        Args:
            session: Database session.
            code: Coupon code.
            user_id: User attempting to use the coupon.

        Returns:
            True if coupon is valid and belongs to user.
        """
        coupon = await cls.get(session, code)

        if not coupon:
            logger.warning(f"Coupon {code} not found.")
            return False

        if coupon.user_id != user_id:
            logger.warning(f"Coupon {code} does not belong to user {user_id}.")
            return False

        if not coupon.is_valid:
            logger.warning(f"Coupon {code} is expired or already used.")
            return False

        return True

    @classmethod
    async def use(cls, session: AsyncSession, code: str) -> bool:
        """Mark coupon as used."""
        coupon = await cls.get(session, code)

        if not coupon:
            logger.warning(f"Coupon {code} not found.")
            return False

        await session.execute(
            update(Coupon)
            .where(Coupon.code == code)
            .values(used=True, used_at=func.now())
        )
        await session.commit()
        logger.info(f"Coupon {code} marked as used.")
        return True

    @classmethod
    async def get_user_coupons(
        cls, session: AsyncSession, user_id: int, include_used: bool = False
    ) -> list[Self]:
        """Get all coupons for a user."""
        query = select(Coupon).where(Coupon.user_id == user_id)

        if not include_used:
            query = query.where(Coupon.used == False)

        query = query.order_by(Coupon.valid_until.asc())
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_user_active_coupons(cls, session: AsyncSession, user_id: int) -> list[Self]:
        """Get only valid (unused and not expired) coupons for a user."""
        coupons = await cls.get_user_coupons(session, user_id, include_used=False)
        return [c for c in coupons if c.is_valid]

import logging
from datetime import datetime
from typing import Self

from sqlalchemy import ForeignKey, String, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

logger = logging.getLogger(__name__)


class Referral(Base):
    """
    Represents a referral relationship in the MAX VPN shop.

    Attributes:
        id (int): Unique primary key.
        referrer_id (int): User who made the referral.
        referred_id (int): User who was referred.
        referred_type (str): Type of referral (individual/company).
        reward_issued (bool): Whether reward has been issued.
        coupon_code (str | None): Generated coupon code for referrer.
        created_at (datetime): Timestamp when referral was created.
        referrer (User): User who referred.
        referred (User): User who was referred.
    """

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    referred_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    referred_type: Mapped[str] = mapped_column(
        String(10), default="individual", nullable=False
    )
    reward_issued: Mapped[bool] = mapped_column(default=False, nullable=False)
    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    referrer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="referrals_sent",
    )
    referred: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referred_id],
        back_populates="referral",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Referral(id={self.id}, referrer_id={self.referrer_id}, "
            f"referred_id={self.referred_id}, type='{self.referred_type}', "
            f"reward_issued={self.reward_issued})>"
        )

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        referrer_id: int,
        referred_id: int,
        referred_type: str = "individual",
    ) -> Self | None:
        """Create a new referral."""
        # Check if referral already exists
        existing = await cls.get_by_referred(session, referred_id)
        if existing:
            logger.warning(f"Referral for user {referred_id} already exists.")
            return None

        referral = cls(
            referrer_id=referrer_id,
            referred_id=referred_id,
            referred_type=referred_type,
        )
        session.add(referral)

        try:
            await session.commit()
            logger.info(
                f"Referral created: {referrer_id} -> {referred_id} ({referred_type})"
            )
            return referral
        except Exception as exception:
            await session.rollback()
            logger.error(f"Error creating referral: {exception}")
            return None

    @classmethod
    async def get(cls, session: AsyncSession, referral_id: int) -> Self | None:
        """Get referral by ID."""
        query = await session.execute(
            select(Referral).where(Referral.id == referral_id)
        )
        return query.scalar_one_or_none()

    @classmethod
    async def get_by_referred(cls, session: AsyncSession, referred_id: int) -> Self | None:
        """Get referral by referred user ID."""
        query = await session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return query.scalar_one_or_none()

    @classmethod
    async def mark_reward_issued(
        cls, session: AsyncSession, referral_id: int, coupon_code: str
    ) -> bool:
        """Mark referral reward as issued with coupon code."""
        referral = await cls.get(session, referral_id)

        if not referral:
            logger.warning(f"Referral {referral_id} not found.")
            return False

        await session.execute(
            update(Referral)
            .where(Referral.id == referral_id)
            .values(reward_issued=True, coupon_code=coupon_code)
        )
        await session.commit()
        logger.info(f"Referral {referral_id} reward issued with coupon: {coupon_code}")
        return True

    @classmethod
    async def get_referrer_stats(cls, session: AsyncSession, referrer_id: int) -> dict:
        """Get referral statistics for a user."""
        query = await session.execute(
            select(Referral).where(Referral.referrer_id == referrer_id)
        )
        referrals = query.scalars().all()

        total = len(referrals)
        rewarded = sum(1 for r in referrals if r.reward_issued)
        pending = total - rewarded

        return {
            "total_referrals": total,
            "rewarded": rewarded,
            "pending": pending,
        }

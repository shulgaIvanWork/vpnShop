"""
Manual Payment model for tracking Sber QR payments.

This model stores payment receipts that need manual admin approval.
"""

import logging
from datetime import datetime
from typing import Any, Self

from sqlalchemy import ForeignKey, Integer, String, Text, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

logger = logging.getLogger(__name__)


class ManualPayment(Base):
    """
    Represents a manual payment requiring admin approval.
    
    Used for Sber QR code payments where user sends receipt screenshot.
    
    Attributes:
        id (int): Unique primary key.
        user_id (int): Foreign key to users table.
        plan_duration (int): Subscription duration in days (30/90/180).
        original_price (int): Original price before discount.
        discount_applied (int): Discount percentage applied (0-50).
        final_price (int): Final price after discount.
        receipt_message_id (str | None): MAX message ID with receipt photo.
        receipt_text (str | None): User's comment with payment.
        status (str): Payment status (pending/approved/rejected).
        admin_id (int | None): Admin who approved/rejected.
        admin_comment (str | None): Admin's comment/reason.
        created_at (datetime): Timestamp when payment was created.
        updated_at (datetime): Timestamp when status was changed.
        user (User): User who made the payment.
    """

    __tablename__ = "manual_payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plan_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    original_price: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_applied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_price: Mapped[int] = mapped_column(Integer, nullable=False)
    
    receipt_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receipt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )
    admin_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="manual_payments")

    def __repr__(self) -> str:
        return (
            f"<ManualPayment(id={self.id}, user_id={self.user_id}, "
            f"price={self.final_price}, status='{self.status}')>"
        )

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_id: int,
        plan_duration: int,
        original_price: int,
        final_price: int,
        discount_applied: int = 0,
        receipt_message_id: str = None,
        receipt_text: str = None,
        **kwargs: Any,
    ) -> Self | None:
        """Create a new manual payment record."""
        payment = cls(
            user_id=user_id,
            plan_duration=plan_duration,
            original_price=original_price,
            discount_applied=discount_applied,
            final_price=final_price,
            receipt_message_id=receipt_message_id,
            receipt_text=receipt_text,
            **kwargs,
        )
        session.add(payment)

        try:
            await session.commit()
            logger.info(f"Manual payment created for user {user_id}: {final_price} RUB")
            return payment
        except IntegrityError as exception:
            await session.rollback()
            logger.error(f"Error creating manual payment: {exception}")
            return None

    @classmethod
    async def get(cls, session: AsyncSession, payment_id: int) -> Self | None:
        """Get manual payment by ID."""
        query = await session.execute(
            select(ManualPayment).where(ManualPayment.id == payment_id)
        )
        return query.scalar_one_or_none()

    @classmethod
    async def get_pending_payments(cls, session: AsyncSession) -> list[Self]:
        """Get all pending manual payments."""
        query = await session.execute(
            select(ManualPayment)
            .where(ManualPayment.status == "pending")
            .order_by(ManualPayment.created_at.desc())
        )
        return query.scalars().all()

    @classmethod
    async def get_user_payments(
        cls, session: AsyncSession, user_id: int
    ) -> list[Self]:
        """Get all manual payments for a user."""
        query = await session.execute(
            select(ManualPayment)
            .where(ManualPayment.user_id == user_id)
            .order_by(ManualPayment.created_at.desc())
        )
        return query.scalars().all()

    @classmethod
    async def approve(
        cls, session: AsyncSession, payment_id: int, admin_id: int
    ) -> Self | None:
        """Approve a manual payment."""
        payment = await cls.get(session, payment_id)
        
        if not payment:
            logger.warning(f"Manual payment {payment_id} not found.")
            return None
        
        await session.execute(
            update(ManualPayment)
            .where(ManualPayment.id == payment_id)
            .values(
                status="approved",
                admin_id=admin_id,
                updated_at=func.now(),
            )
        )
        await session.commit()
        
        logger.info(
            f"Manual payment {payment_id} approved by admin {admin_id}"
        )
        return payment

    @classmethod
    async def reject(
        cls,
        session: AsyncSession,
        payment_id: int,
        admin_id: int,
        reason: str = None,
    ) -> Self | None:
        """Reject a manual payment."""
        payment = await cls.get(session, payment_id)
        
        if not payment:
            logger.warning(f"Manual payment {payment_id} not found.")
            return None
        
        await session.execute(
            update(ManualPayment)
            .where(ManualPayment.id == payment_id)
            .values(
                status="rejected",
                admin_id=admin_id,
                admin_comment=reason,
                updated_at=func.now(),
            )
        )
        await session.commit()
        
        logger.info(
            f"Manual payment {payment_id} rejected by admin {admin_id}: {reason}"
        )
        return payment

import logging
from datetime import datetime
from typing import Any, Self

from sqlalchemy import ForeignKey, Numeric, String, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

logger = logging.getLogger(__name__)


class Payment(Base):
    """
    Represents a payment transaction in the MAX VPN shop.

    Attributes:
        id (int): Unique primary key.
        user_id (int): Foreign key to users table.
        amount (float): Payment amount.
        currency (str): Currency code (default: RUB).
        status (str): Payment status (pending/succeeded/cancelled).
        payment_method (str): Payment gateway (yookassa/yoomoney).
        yookassa_payment_id (str | None): YooKassa payment identifier.
        yoomoney_payment_id (str | None): YooMoney payment identifier.
        plan_duration (int): Subscription duration in days.
        discount_applied (int): Discount percentage applied (0-50).
        coupon_code (str | None): Coupon code used for discount.
        created_at (datetime): Timestamp when payment was created.
        user (User): User who made the payment.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="RUB", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    yookassa_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    yoomoney_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    plan_duration: Mapped[int] = mapped_column(nullable=False)
    discount_applied: Mapped[int] = mapped_column(default=0, nullable=False)
    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, "
            f"status='{self.status}', method='{self.payment_method}')>"
        )

    @classmethod
    async def get(cls, session: AsyncSession, payment_id: int) -> Self | None:
        """Get payment by ID."""
        query = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return query.scalar_one_or_none()

    @classmethod
    async def get_by_payment_gateway_id(
        cls, session: AsyncSession, gateway_payment_id: str
    ) -> Self | None:
        """Get payment by YooKassa or YooMoney payment ID."""
        query = await session.execute(
            select(Payment).where(
                (Payment.yookassa_payment_id == gateway_payment_id)
                | (Payment.yoomoney_payment_id == gateway_payment_id)
            )
        )
        return query.scalar_one_or_none()

    @classmethod
    async def create(cls, session: AsyncSession, user_id: int, **kwargs: Any) -> Self | None:
        """Create a new payment record."""
        payment = Payment(user_id=user_id, **kwargs)
        session.add(payment)

        try:
            await session.commit()
            logger.debug(f"Payment created for user {user_id}.")
            return payment
        except IntegrityError as exception:
            await session.rollback()
            logger.error(f"Error occurred while creating payment for user {user_id}: {exception}")
            return None

    @classmethod
    async def update_status(
        cls, session: AsyncSession, payment_id: int, status: str
    ) -> bool:
        """Update payment status."""
        payment = await cls.get(session=session, payment_id=payment_id)

        if not payment:
            logger.warning(f"Payment {payment_id} not found to update status.")
            return False

        await session.execute(
            update(Payment).where(Payment.id == payment_id).values(status=status)
        )
        await session.commit()
        logger.info(f"Payment {payment_id} status updated to: {status}")
        return True

    @classmethod
    async def get_user_payments(cls, session: AsyncSession, user_id: int) -> list[Self]:
        """Get all payments for a user."""
        query = await session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
        )
        return query.scalars().all()

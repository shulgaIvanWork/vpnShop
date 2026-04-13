import logging
from datetime import datetime
from typing import Any, Optional, Self

from sqlalchemy import ForeignKey, String, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from . import Base

logger = logging.getLogger(__name__)


class User(Base):
    """
    Represents a user in the MAX VPN shop.

    Attributes:
        id (int): Unique primary key for the user.
        max_user_id (int): Unique MAX user ID.
        username (str | None): MAX username.
        subscription_end (datetime | None): Subscription expiration timestamp.
        device_limit (int): Number of allowed devices (default: 1).
        uuid (str | None): VPN client UUID.
        assigned_server (str | None): IP of assigned 3X-UI panel.
        created_at (datetime): Timestamp when the user was created.
        payments (list[Payment]): List of payments made by the user.
        referrals_sent (list[Referral]): Referrals made by this user.
        referral (Referral | None): Referral record if invited by someone.
        coupons (list[Coupon]): Coupons owned by the user.
        corporate_server (CorporateServer | None): Corporate server if applicable.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    max_user_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(length=100), nullable=True)
    subscription_end: Mapped[datetime | None] = mapped_column(nullable=True)
    device_limit: Mapped[int] = mapped_column(default=1, nullable=False)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)
    assigned_server: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="user")
    referrals_sent: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="Referral.referrer_id",
        primaryjoin="User.id == Referral.referrer_id",
        back_populates="referrer",
        cascade="all, delete-orphan",
    )
    referral: Mapped["Referral | None"] = relationship(
        "Referral",
        foreign_keys="Referral.referred_id",
        primaryjoin="User.id == Referral.referred_id",
        back_populates="referred",
        uselist=False,
    )
    coupons: Mapped[list["Coupon"]] = relationship("Coupon", back_populates="user")
    corporate_server: Mapped["CorporateServer | None"] = relationship(
        "CorporateServer", back_populates="user", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, max_user_id={self.max_user_id}, "
            f"username='{self.username}', subscription_end={self.subscription_end}, "
            f"device_limit={self.device_limit})>"
        )

    @classmethod
    async def get(cls, session: AsyncSession, max_user_id: int) -> Self | None:
        """Get user by MAX user ID."""
        query = await session.execute(
            select(User)
            .options(
                selectinload(User.payments),
                selectinload(User.coupons),
                selectinload(User.corporate_server),
            )
            .where(User.max_user_id == max_user_id)
        )
        user = query.scalar_one_or_none()

        if user:
            logger.debug(f"User {max_user_id} retrieved from the database.")
        else:
            logger.debug(f"User {max_user_id} not found in the database.")

        return user

    @classmethod
    async def get_all(cls, session: AsyncSession) -> list[Self]:
        """Get all users."""
        query = await session.execute(select(User))
        return query.scalars().all()

    @classmethod
    async def create(cls, session: AsyncSession, max_user_id: int, **kwargs: Any) -> Self | None:
        """Create a new user."""
        user = await User.get(session=session, max_user_id=max_user_id)

        if user:
            logger.warning(f"User {max_user_id} already exists.")
            return None

        user = User(max_user_id=max_user_id, **kwargs)
        session.add(user)

        try:
            await session.commit()
            logger.debug(f"User {max_user_id} created.")
            return user
        except IntegrityError as exception:
            await session.rollback()
            logger.error(f"Error occurred while creating user {max_user_id}: {exception}")
            return None

    @classmethod
    async def update(cls, session: AsyncSession, max_user_id: int, **kwargs: Any) -> Self | None:
        """Update user fields."""
        user = await User.get(session=session, max_user_id=max_user_id)

        if user:
            filter = [User.max_user_id == max_user_id]
            await session.execute(update(User).where(*filter).values(**kwargs))
            await session.commit()
            logger.debug(f"User {max_user_id} updated.")
            return user

        logger.warning(f"User {max_user_id} not found in the database.")
        return None

    @classmethod
    async def exists(cls, session: AsyncSession, max_user_id: int) -> bool:
        """Check if user exists."""
        return await User.get(session=session, max_user_id=max_user_id) is not None

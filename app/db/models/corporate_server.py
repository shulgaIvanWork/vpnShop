import logging
from datetime import datetime
from typing import Self

from sqlalchemy import ForeignKey, Integer, String, Text, func, select, update
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

logger = logging.getLogger(__name__)


class CorporateServer(Base):
    """
    Represents a corporate VPN server in the MAX VPN shop.

    Attributes:
        id (int): Unique primary key.
        user_id (int): Corporate client who owns this server.
        server_ip (str): IP address of the 3X-UI panel.
        api_key_encrypted (str): Encrypted 3X-UI API key.
        slots_total (int): Total number of client slots (100 or 500).
        slots_used (int): Number of slots currently in use.
        status (str): Server status (active/expired/disabled).
        notes (str | None): Additional notes.
        created_at (datetime): Timestamp when server was added.
        user (User): Corporate client who owns the server.
    """

    __tablename__ = "corporate_servers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    server_ip: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    slots_total: Mapped[int] = mapped_column(Integer, nullable=False)
    slots_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="corporate_server")

    def __repr__(self) -> str:
        return (
            f"<CorporateServer(id={self.id}, user_id={self.user_id}, "
            f"ip='{self.server_ip}', slots={self.slots_used}/{self.slots_total}, "
            f"status='{self.status}')>"
        )

    @property
    def slots_available(self) -> int:
        """Get number of available slots."""
        return self.slots_total - self.slots_used

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_id: int,
        server_ip: str,
        api_key_encrypted: str,
        slots_total: int,
        notes: str | None = None,
    ) -> Self | None:
        """Create a new corporate server record."""
        if slots_total not in [100, 500]:
            logger.error(f"Invalid slots_total: {slots_total}. Must be 100 or 500.")
            return None

        server = cls(
            user_id=user_id,
            server_ip=server_ip,
            api_key_encrypted=api_key_encrypted,
            slots_total=slots_total,
            notes=notes,
        )
        session.add(server)

        try:
            await session.commit()
            logger.info(
                f"Corporate server created: {server_ip} for user {user_id} "
                f"({slots_total} slots)"
            )
            return server
        except Exception as exception:
            await session.rollback()
            logger.error(f"Error creating corporate server: {exception}")
            return None

    @classmethod
    async def get(cls, session: AsyncSession, server_id: int) -> Self | None:
        """Get corporate server by ID."""
        query = await session.execute(
            select(CorporateServer).where(CorporateServer.id == server_id)
        )
        return query.scalar_one_or_none()

    @classmethod
    async def get_by_user(cls, session: AsyncSession, user_id: int) -> Self | None:
        """Get corporate server by user ID."""
        query = await session.execute(
            select(CorporateServer).where(CorporateServer.user_id == user_id)
        )
        return query.scalar_one_or_none()

    @classmethod
    async def get_all(cls, session: AsyncSession) -> list[Self]:
        """Get all corporate servers."""
        query = await session.execute(
            select(CorporateServer).order_by(CorporateServer.created_at.desc())
        )
        return query.scalars().all()

    @classmethod
    async def update_status(
        cls, session: AsyncSession, server_id: int, status: str
    ) -> bool:
        """Update server status."""
        server = await cls.get(session, server_id)

        if not server:
            logger.warning(f"Corporate server {server_id} not found.")
            return False

        await session.execute(
            update(CorporateServer)
            .where(CorporateServer.id == server_id)
            .values(status=status)
        )
        await session.commit()
        logger.info(f"Corporate server {server_id} status updated to: {status}")
        return True

    @classmethod
    async def increment_slots_used(cls, session: AsyncSession, server_id: int) -> bool:
        """Increment slots_used counter."""
        server = await cls.get(session, server_id)

        if not server:
            logger.warning(f"Corporate server {server_id} not found.")
            return False

        if server.slots_used >= server.slots_total:
            logger.warning(f"Corporate server {server_id} has no available slots.")
            return False

        await session.execute(
            update(CorporateServer)
            .where(CorporateServer.id == server_id)
            .values(slots_used=CorporateServer.slots_used + 1)
        )
        await session.commit()
        logger.debug(f"Corporate server {server_id} slots used: {server.slots_used + 1}")
        return True

    @classmethod
    async def get_expired_servers(cls, session: AsyncSession) -> list[Self]:
        """Get all servers with expired status."""
        query = await session.execute(
            select(CorporateServer).where(CorporateServer.status == "expired")
        )
        return query.scalars().all()

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.friend_invite import FriendInvite


class FriendInviteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_invite(
            self,
            friend_id: UUID,
            token_hash: str,
            expires_at: datetime,
    ) -> FriendInvite:
        invite = FriendInvite(
            friend_id=friend_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.session.add(invite)
        await self.session.flush()
        await self.session.refresh(invite)

        return invite

    async def get_valid_invite(
            self,
            token_hash: str,
    ) -> FriendInvite | None:
        result = await self.session.execute(
            select(FriendInvite).where(
                FriendInvite.token_hash == token_hash,
                FriendInvite.used.is_(False),
                FriendInvite.expires_at > datetime.now(timezone.utc),
                )
        )

        return result.scalar_one_or_none()

    async def get_active_invite_for_friend(
            self,
            friend_id: UUID,
    ) -> FriendInvite | None:
        result = await self.session.execute(
            select(FriendInvite).where(
                FriendInvite.friend_id == friend_id,
                FriendInvite.used.is_(False),
                FriendInvite.expires_at > datetime.now(timezone.utc),
                )
        )

        return result.scalar_one_or_none()

    async def invalidate_active_invites(
            self,
            friend_id: UUID,
    ) -> None:
        await self.session.execute(
            update(FriendInvite)
            .where(
                FriendInvite.friend_id == friend_id,
                FriendInvite.used.is_(False),
                FriendInvite.expires_at > datetime.now(timezone.utc),
                )
            .values(used=True)
        )

        await self.session.flush()

    async def mark_invite_as_used(
            self,
            invite: FriendInvite,
    ) -> None:
        invite.used = True
        await self.session.flush()
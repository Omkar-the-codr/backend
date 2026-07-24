import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import FRIEND_INVITE_EXPIRE_MINUTES
from repository.friend_invite_repository import FriendInviteRepository
from repository.friend_repository import FriendRepository
from repository.user_repository import UserRepository
from services.friend_service import claim_friend_internal


async def create_friend_invite(
        friend_id: UUID,
        db: AsyncSession,
):
    friend_repo = FriendRepository(db)
    invite_repo = FriendInviteRepository(db)

    friend = await friend_repo.get_by_id(friend_id)

    if not friend:
        raise HTTPException(
            status_code=404,
            detail="Friend not found",
        )

    if friend.claimed_by_user_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Friend has already been claimed",
        )

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=FRIEND_INVITE_EXPIRE_MINUTES
    )
    await invite_repo.invalidate_active_invites(friend.id)
    await invite_repo.save_invite(
        friend.id,
        token_hash,
        expires_at,
    )
    await db.commit()
    return {
        "token": raw_token,
    }



async def redeem_friend_invite(
        raw_token: str,
        current_user_id: UUID,
        db: AsyncSession,
):
    invite_repo = FriendInviteRepository(db)
    friend_repo = FriendRepository(db)
    user_repo = UserRepository(db)

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    invite = await invite_repo.get_valid_invite(token_hash)

    if not invite:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired invite",
        )

    friend = await friend_repo.get_by_id(invite.friend_id)

    if not friend:
        raise HTTPException(
            status_code=404,
            detail="Friend not found",
        )

    user = await user_repo.get_user_by_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )


    if friend.claimed_by_user_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Friend has already been claimed",
        )

    await invite_repo.mark_invite_as_used(invite)

    if current_user_id == friend.owner_id:
        raise HTTPException(
            status_code=400,
            detail="Owner cannot claim their own friend",
        )

    claimed_friend = await claim_friend_internal(
        friend_repo,
        friend,
        current_user_id,
    )

    await db.commit()
    await db.refresh(claimed_friend)
    return SuccessResponse(
        message="Friend claimed successfully",
        data=FriendResponse.model_validate(claimed_friend),
    )
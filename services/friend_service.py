from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.expense_splits import ExpenseSplit
from models.friend import Friend
from models.group_members import GroupMember, Role
from models.groups import Group
from repository.friend_repository import FriendRepository
from repository.group_member_repository import GroupMemberRepository
from repository.group_repository import GroupRepository
from schemas.common import SuccessResponse
from schemas.friend import FriendResponse
from models.friend import Friend


async def create_friend(
    owner_id: UUID, name: str, db: AsyncSession
) -> SuccessResponse[FriendResponse]:
    friend_repo = FriendRepository(db)
    group_repo = GroupRepository(db)
    member_repo = GroupMemberRepository(db)

    friend = Friend(owner_id=owner_id, name=name)
    created_friend = await friend_repo.create_friend(friend)

    shadow_group = Group(
        name=name,
        created_by=owner_id,
        is_shadow=True,
    )
    created_group = await group_repo.create(shadow_group)

    created_friend.shadow_group_id = created_group.id
    await db.flush()

    await member_repo.add_group_member(user_id=owner_id, group_id=created_group.id)

    await db.execute(
        GroupMember.__table__.insert().values(
            group_id=created_group.id,
            friend_id=created_friend.id,
            role=Role.MEMBER,
        )
    )

    await db.commit()
    await db.refresh(created_friend)

    return SuccessResponse(
        message="Friend created successfully",
        data=FriendResponse.model_validate(created_friend),
    )


async def get_friend(
    friend_id: UUID, owner_id: UUID, db: AsyncSession
) -> SuccessResponse[FriendResponse]:
    friend_repo = FriendRepository(db)

    friend = await friend_repo.get_by_id(friend_id)
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")

    if friend.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not authorised")

    return SuccessResponse(
        message="Friend fetched successfully",
        data=FriendResponse.model_validate(friend),
    )


async def delete_friend(
    friend_id: UUID, owner_id: UUID, db: AsyncSession
) -> SuccessResponse[None]:
    friend_repo = FriendRepository(db)

    friend = await friend_repo.get_by_id(friend_id)
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")

    if friend.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not authorised")

    if friend.claimed_by_user_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Friend has already been claimed and cannot be deleted",
        )

    result = await db.execute(
        select(ExpenseSplit).where(
            ExpenseSplit.friend_id == friend_id, ExpenseSplit.amount != 0
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=400,
            detail="Friend has a pending balance and cannot be deleted",
        )

    await friend_repo.delete_friend(friend)

    return SuccessResponse(message="Friend deleted successfully", data=None)



async def _claim_friend_internal(
        friend_repo: FriendRepository,
        friend: Friend,
        new_user_id: UUID,
) -> Friend:
    await friend_repo.rewrite_group_members(friend.id, new_user_id)
    await friend_repo.rewrite_expense_splits(friend.id, new_user_id)
    await friend_repo.rewrite_settlements(friend.id, new_user_id)

    return await friend_repo.mark_claimed(friend, new_user_id)


async def claim_friend(
        friend_id: UUID,
        new_user_id: UUID,
        db: AsyncSession,
) -> SuccessResponse[FriendResponse]:
    friend_repo = FriendRepository(db)

    friend = await friend_repo.get_by_id(friend_id)
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")

    if friend.claimed_by_user_id is not None:
        raise HTTPException(status_code=400, detail="Friend has already been claimed")

    if new_user_id == friend.owner_id:
        raise HTTPException(
            status_code=400,
            detail="Owner cannot claim their own friend",
        )

    claimed_friend = await _claim_friend_internal(
        friend_repo,
        friend,
        new_user_id,
    )

    await db.commit()
    await db.refresh(claimed_friend)

    return SuccessResponse(
        message="Friend claimed successfully",
        data=FriendResponse.model_validate(claimed_friend),
    )

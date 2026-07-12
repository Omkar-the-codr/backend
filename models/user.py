import uuid
from enum import Enum

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, String  # type: ignore
from sqlalchemy import Enum as SQLEnum  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore
from sqlalchemy.orm import backref, relationship  # type: ignore
from sqlalchemy.sql import func  # type: ignore

from core.database import Base


class AuthProvider(Enum):
    LOCAL = "local"
    GOOGLE = "google"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    # ghost users don't have email
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    auth_provider = Column(
        SQLEnum(AuthProvider), nullable=False, default=AuthProvider.LOCAL
    )
    profile_picture = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Ghost User Metadata
    is_ghost = Column(Boolean, nullable=False, default=False)
    ghost_owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    shadow_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "groups.id",
            use_alter=True,
            name="fk_users_shadow_group_id_groups",
        ),
        nullable=True,
    )

    # relationships

    personal_expenses = relationship("PersonalExpense", back_populates="user")
    groups = relationship(
        "Group", foreign_keys="Group.created_by", back_populates="creator"
    )
    group_memberships = relationship("GroupMember", back_populates="user")
    expenses_paid = relationship(
        "GroupExpense", foreign_keys="GroupExpense.paid_by", back_populates="payer"
    )
    expense_splits = relationship("ExpenseSplit", back_populates="user")
    payments_made = relationship(
        "Settlement", foreign_keys="Settlement.payer_id", back_populates="payer"
    )
    payments_received = relationship(
        "Settlement", foreign_keys="Settlement.receiver_id", back_populates="receiver"
    )

    # relationship b/w Ghost and user

    ghosts = relationship(
        "User",
        foreign_keys=[ghost_owner_id],
        backref=backref("ghost_owner", remote_side=[id]),
        lazy="selectin",
    )
    shadow_group = relationship("Group", foreign_keys=[shadow_group_id])

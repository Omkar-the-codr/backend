import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import false

from core.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_ghost_group = Column(Boolean, nullable=False, default=False, server_default=false())

    # relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="groups")
    members = relationship("GroupMember", back_populates="group")
    expenses = relationship("GroupExpense", back_populates="group")

    personal_expenses = relationship("PersonalExpense", back_populates="group")
    settlements = relationship("Settlement", back_populates="group")

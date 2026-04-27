from typing import Optional, List

from sqlalchemy import DateTime, Column, func
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


class AgentModel(SQLModel, table=True):
    __tablename__ = "agent"
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_name: str = Field(default="")
    agent_email: str = Field(nullable=False,)
    agent_phone: str = Field(nullable=False, index=True,unique=True)
    agent_code: str = Field(nullable=False, index=True)
    referrals: List["AgentReferrals"] = Relationship(back_populates="agent")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class AgentReferrals(SQLModel, table=True):
    __tablename__ = "agent_referrals"
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: Optional[int] = Field(foreign_key="agent.id", nullable=False)
    user_id: Optional[int] = Field(foreign_key="user.id", nullable=False)
    agent: Optional["AgentModel"] = Relationship(back_populates="referrals")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

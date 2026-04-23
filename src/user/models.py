from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func, JSON
from sqlmodel import Field, SQLModel, Relationship

from enum import Enum

from src.user.enums import Gender, AccountType


class UserBaseModel(SQLModel):
    first_name: str = Field(default="")
    last_name: str = Field(default="")
    email: str = Field(default="")
    phone_number: str = Field(default="")
    profile_picture: str = Field(default="")
    video_picture: str = Field(default="")
    dob: str = Field(default="")
    gender: Gender = Field(default=Gender.MALE)
    hobby: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False)
    )
    state: str = Field(default="")
    city: str = Field(default="")


class UserModel(UserBaseModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    step_1_error: Optional[str] = Field(default="PENDING")
    step_2_error: Optional[str] = Field(default="PENDING")
    step_3_error: Optional[str] = Field(default="PENDING")
    lvl: Optional[int] = Field(default=1)
    score: Optional[int] = Field(default=0)
    account_type: AccountType = Field(default=AccountType.USER)
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    is_active: bool = Field(default=False)
    addition_images: List["UserAdditionPicture"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    call_made: List["CallHistoryTable"] = Relationship(
        back_populates="caller",
        sa_relationship_kwargs={"foreign_keys": "[CallHistoryTable.caller_id]"}
    )
    call_received: List["CallHistoryTable"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={"foreign_keys": "[CallHistoryTable.receiver_id]"}
    )


class UserAdditionPicture(SQLModel, table=True):
    __tablename__ = "addition_image"
    id: Optional[int] = Field(default=None, primary_key=True)
    image_path: str = Field(nullable=False)
    user_id: Optional[int] = Field(foreign_key="user.id", nullable=False)
    user: Optional["UserModel"] = Relationship(back_populates="addition_images")

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class ConversationTable(SQLModel, table=True):
    __tablename__ = "conversation"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_a_id: int = Field(foreign_key="user.id", nullable=False)
    user_b_id: int = Field(foreign_key="user.id", nullable=False)
    unread_count_a: int = Field(default=0)
    unread_count_b: int = Field(default=0)
    last_message: str = Field(default=None)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    user_a: Optional["UserModel"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "ConversationTable.user_a_id"}
    )
    user_b: Optional["UserModel"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "ConversationTable.user_b_id"}
    )


class FriendTable(SQLModel, table=True):
    __tablename__ = "friend"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    friend_id: int = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class FriendRequestTable(SQLModel, table=True):
    __tablename__ = "friend_request"
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    receiver_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class CallHistoryTable(SQLModel, table=True):
    __tablename__ = "call_history"
    id: Optional[int] = Field(default=None, primary_key=True)
    caller_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    receiver_id: int = Field(foreign_key="user.id", index=True, nullable=False)

    receiver: Optional["UserModel"] = Relationship(
        back_populates="call_received",
        sa_relationship_kwargs={"foreign_keys": "[CallHistoryTable.receiver_id]"}
    )
    caller : Optional["UserModel"] = Relationship(
        back_populates="call_made",
        sa_relationship_kwargs={"foreign_keys": "[CallHistoryTable.caller_id]"}
    )

    duration: int = Field(default=0)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

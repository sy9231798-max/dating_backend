from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func, JSON, UniqueConstraint, ForeignKey
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Enum as SAEnum
from enum import Enum

from src.user.enums import Gender, AccountType, CallStatus, PaymentStatus


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
    coins: int = Field(default=100)
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

    call_made: List["CallHistory"] = Relationship(
        back_populates="caller",
        sa_relationship_kwargs={"foreign_keys": "[CallHistory.caller_id]"}
    )
    call_received: List["CallHistory"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={"foreign_keys": "[CallHistory.receiver_id]"}
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


class CallHistory(SQLModel, table=True):
    __tablename__ = "call_history"
    id: Optional[int] = Field(default=None, primary_key=True)
    caller_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    receiver_id: int = Field(foreign_key="user.id", index=True, nullable=False)

    receiver: Optional["UserModel"] = Relationship(
        back_populates="call_received",
        sa_relationship_kwargs={"foreign_keys": "[CallHistory.receiver_id]"}
    )
    caller: Optional["UserModel"] = Relationship(
        back_populates="call_made",
        sa_relationship_kwargs={"foreign_keys": "[CallHistory.caller_id]"}
    )
    room_id: str = Field(nullable=True)
    call_status: CallStatus = Field(default=CallStatus.NONE)
    call_duration: int = Field(default=0)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class BlockedUser(SQLModel, table=True):
    __tablename__ = "blocked_users"

    id: int = Field(primary_key=True, default=None)
    blocker_id: int = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    blocked_id: int = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    reason: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="unique_block"),
    )


class ReportUser(SQLModel, table=True):
    __tablename__ = "report_user"

    id: int = Field(primary_key=True, default=None)
    reporter_id: int = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    reported_id: int = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    reason: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class UserPaymentDetail(SQLModel, table=True):
    __tablename__ = "user_payment_detail"
    id: int = Field(primary_key=True, default=None)
    user_id: int = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    account_number: str = Field(nullable=False, default="")
    bank_name: str = Field(nullable=False, default="")
    holder_name: str = Field(nullable=False, default="")
    ifsc_code: str = Field(nullable=False, default="")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class UserPaymentHistory(SQLModel, table=True):
    __tablename__ = "payment_history"
    id: int = Field(primary_key=True, default=None)
    user_id: int = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    )
    account_number: str = Field(nullable=False, default="")
    bank_name: str = Field(nullable=False, default="")
    amount: int = Field(nullable=False, default=0)
    payment_status: PaymentStatus = Field(
        sa_column=Column(
            SAEnum(
                PaymentStatus,
                name="paymentstatus",
                create_type=False
            ),
            nullable=False,
            default=PaymentStatus.PENDING
        )
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

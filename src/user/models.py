from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func, JSON
from sqlmodel import Field, SQLModel, Relationship

from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


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
    addition_images: List["UserAdditionPicture"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    step_1_error: Optional[str] = Field(default="PENDING")
    step_2_error: Optional[str] = Field(default="PENDING")
    step_3_error: Optional[str] = Field(default="PENDING")
    account_type: int = Field(default=2, description="1 For Client And 2 For User")
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    is_active: bool = Field(default=False)


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

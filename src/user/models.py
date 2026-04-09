from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func, JSON
from sqlmodel import Field, SQLModel

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


class UserModel(UserBaseModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

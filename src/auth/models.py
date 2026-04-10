from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel, Relationship


class OtpModel(SQLModel, table=True):
    __tablename__ = "otp"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    phone_number: str = Field(nullable=False)
    attempts: int = Field(default=0)
    is_used: bool = Field(default=False)
    hashed_otp: str = Field(nullable=False)
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

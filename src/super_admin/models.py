from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel, Relationship


class AdminModel(SQLModel, table=True):
    __tablename__ = "admin"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password: str
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class GiftModel(SQLModel, table=True):
    __tablename__ = "gift"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default="")
    price: int = Field(default=0)
    image_path: str = Field(nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

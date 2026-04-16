from datetime import datetime
from typing import List, Optional, Mapping, Any

from pydantic import BaseModel, Field
from sqlalchemy.sql.functions import user

from src.user.models import Gender, ConversationTable, UserModel


class UserDataResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    profile_picture: str
    video_picture: str
    dob: str
    gender: Gender
    hobby: List[str]
    state: str
    city: str
    created_at: datetime
    is_active: bool


class ConversationUserData(BaseModel):
    id: int
    first_name: str
    last_name: str
    profile_picture: str

    @classmethod
    def get_user(cls, user: UserModel) -> ConversationUserData:
        return cls(**user.dict())


class ConversationDataResponse(BaseModel):
    id: int
    last_message: str
    user_id: int
    user: ConversationUserData
    unread_count: int
    updated_at: datetime

    @classmethod
    def conversation(cls, user_id: int, conversation: ConversationTable) -> ConversationDataResponse:
        is_a = conversation.user_a.id == user_id
        return cls(
            **conversation.model_dump(),
            user_id=conversation.user_b.id if is_a else conversation.user_a.id,
            user=ConversationUserData.get_user(conversation.user_b if is_a else conversation.user_a),
            unread_count=conversation.unread_count_a if is_a else conversation.unread_count_b
        )


class MessageResponse(BaseModel):
    id: str
    receiver: int
    sender: int
    type: str
    message_type: str
    message: str

    class Config:
        populate_by_name = True


    @classmethod
    def from_mongodb(cls, message: Mapping[str, Any]) -> MessageResponse:
        return MessageResponse(
            id=str(message.get('_id')),
            receiver=message.get("to"),
            sender=message.get("from"),
            type=message.get("type"),
            message_type=message.get("message_type"),
            message=message.get("message")
        )
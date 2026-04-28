from datetime import datetime
from typing import List, Optional, Mapping, Any

from pydantic import BaseModel, Field
from sqlalchemy.sql.functions import user

from src.user.models import Gender, ConversationTable, UserModel, UserAdditionPicture, CallHistoryTable


class UserDataResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone_number: str
    email: str
    profile_picture: str
    video_picture: str
    dob: str
    gender: Gender
    hobby: List[str]
    state: str
    city: str
    lvl: int
    is_pending: Optional[bool] = False
    score: int
    created_at: datetime
    addition_images: List[UserAdditionPicture]
    is_active: bool

    @classmethod
    def with_is_pending_status(cls, user: UserModel) -> UserDataResponse:
        is_pending = user.step_1_error == "COMPLETED" and user.step_2_error == "COMPLETED" and user.step_3_error == "COMPLETED"
        return cls(**user.dict(),
                   addition_images=user.addition_images,
                   is_pending=is_pending
                   )


class UserDetailResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone_number: str
    email: str
    profile_picture: str
    video_picture: str
    dob: str
    gender: Gender
    hobby: List[str]
    state: str
    city: str
    lvl: int
    is_pending: Optional[bool]
    score: int
    created_at: datetime
    addition_images: List[UserAdditionPicture]
    is_active: bool
    step_1_error: Optional[str]
    step_2_error: Optional[str]
    step_3_error: Optional[str]

    @classmethod
    def with_is_pending_status(cls, user: UserModel) -> UserDetailResponse:

        is_completed = user.step_1_error == "COMPLETED" and user.step_2_error == "COMPLETED" and user.step_3_error == "COMPLETED"


        return cls(**user.dict(),
                   addition_images=user.addition_images,
                   is_pending=not is_completed
                   )


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


class CallDataResponse(BaseModel):
    id: int
    caller_id: int
    user: ConversationUserData
    duration: int
    created_at: datetime

    @classmethod
    def call_history(cls, user_id: int, call_history: CallHistoryTable) -> CallDataResponse:
        is_me = call_history.caller == user_id
        return cls(
            **call_history.model_dump(),
            user=ConversationUserData.get_user(call_history.receiver if is_me else call_history.caller),
        )


class MessageResponse(BaseModel):
    id: Optional[str] = None
    conversation_id: int
    receiver: int
    sender: int
    message_type: str
    message: Optional[str] = None
    image: Optional[str] = None
    send_at: datetime

    class Config:
        populate_by_name = True

    @classmethod
    def from_mongodb(cls, message: Mapping[str, Any]) -> MessageResponse:
        return MessageResponse(
            id=str(message.get('_id')),
            conversation_id=message.get('conversation_id'),
            receiver=message.get("receiver"),
            sender=message.get("sender"),
            message_type=message.get("message_type"),
            message=message.get("message"),
            image=message.get("image"),
            send_at=message.get("send_at"),
        )

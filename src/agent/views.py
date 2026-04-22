from typing import List

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from src.auth.model_wrapper import LoginResponseWrapper
from src.database import get_session
from src.mongo_helper import message_collection
from src.user.model_wrapper import UserDataResponse, ConversationDataResponse, MessageResponse
from src.user.models import FriendTable, UserModel
from src.user.service import (get_my_information, fetch_explore, fetch_profile_status, fetch_conversation,
                              fetch_all_message, sent_request, friend_request_action)

router = APIRouter()


@router.get("/me", response_model=UserDataResponse)
async def get_me_information(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return get_my_information(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed get my information: {str(e)}"
        )

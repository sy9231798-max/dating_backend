from typing import List

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlmodel import Session
from starlette import status

from src.auth.model_wrapper import LoginResponseWrapper
from src.database import get_session
from src.mongo_helper import message_collection
from src.user.model_wrapper import UserDataResponse, ConversationDataResponse, MessageResponse
from src.user.service import (get_my_information, fetch_explore, fetch_profile_status, fetch_conversation,
                              fetch_all_message)

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
            detail=f"Failed to Login: {str(e)}"
        )


@router.get("/profile-status", response_model=LoginResponseWrapper)
async def get_profile_status(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_profile_status(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.get("/explore", response_model=List[UserDataResponse])
async def get_explore_data(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_explore(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.get("/conversation", response_model=List[ConversationDataResponse])
async def get_conversation_data(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_conversation(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.get("/messages/{conversation_id}",response_model=List[MessageResponse])
async def get_conversation_data(
        conversation_id: int,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return await fetch_all_message(token=user_token, conversation_id=conversation_id,
                                       message_collection=message_collection, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )

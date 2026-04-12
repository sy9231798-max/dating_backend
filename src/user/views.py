from typing import List

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlmodel import Session
from starlette import status

from src.auth.model_wrapper import LoginResponseWrapper
from src.database import get_session
from src.user.model_wrapper import UserDataResponse
from src.user.models import UserModel
from src.user.service import (get_my_information, fetch_explore, fetch_profile_status)

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

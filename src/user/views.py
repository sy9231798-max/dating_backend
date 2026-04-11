from typing import List

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlmodel import Session
from starlette import status

from src.database import get_session
from src.user.model_wrapper import UserDataResponse
from src.user.models import UserModel
from src.user.service import (get_my_information, fetch_explore)

router = APIRouter()


@router.get("/me", response_model=UserDataResponse)
async def get_me(
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


@router.get("/explore",response_model=List[UserDataResponse])
async def get_explore(
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

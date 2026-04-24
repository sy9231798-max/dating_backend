from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Header, Query
from sqlmodel import Session
from starlette import status

from src.database import get_session
from src.pagination_model import PaginatedResponse
from src.super_admin.model_wrapper import AdminDashboardResponse
from src.super_admin.service import login_user, fetch_dashboard, fetch_all_user
from src.user.enums import AccountType
from src.user.model_wrapper import UserDataResponse

router = APIRouter()


@router.post("/login")
async def login(
        email: str = Body(...),
        password: str = Body(...),
        db: Session = Depends(get_session)
):
    try:
        return login_user(email=email, password=password, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_dashboard(
        db: Session = Depends(get_session),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return fetch_dashboard(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


@router.get("/users",response_model=PaginatedResponse[UserDataResponse])
async def get_all_users(
        db: Session = Depends(get_session),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        account_type: Optional[AccountType] = Query(None),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return fetch_all_user(db=db, token=user_token,
                              page_item=page_size,
                              page=page,
                              account_type=account_type
                              )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )

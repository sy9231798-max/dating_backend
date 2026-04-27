from typing import Optional, List

from fastapi import APIRouter, Body, Depends, HTTPException, Header, Query, UploadFile, File
from sqlmodel import Session
from starlette import status

from src.database import get_session
from src.pagination_model import PaginatedResponse
from src.super_admin.model_wrapper import AdminDashboardResponse
from src.super_admin.models import GiftModel
from src.super_admin.service import login_user, fetch_dashboard, fetch_all_user, insert_gift, fetch_all_gifts, \
    update_gift, remove_gift, approve_agent_profile, not_approve_agent_profile, insert_agency
from src.user.enums import AccountType
from src.user.model_wrapper import UserDataResponse, UserDetailResponse

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

        print(str(e))
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


@router.get("/users", response_model=PaginatedResponse[UserDetailResponse])
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


@router.post("/approve-agent")
async def approve_agent(
        db: Session = Depends(get_session),
        user_id: int = Body(...),
        step_no: int = Body(...),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return approve_agent_profile(db=db, token=user_token, user_id=user_id, step_no=step_no)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve user: {str(e)}"
        )


@router.post("/not-approve-agent")
async def not_approve_agent(
        db: Session = Depends(get_session),
        user_id: int = Body(...),
        step_no: int = Body(...),
        reason: str = Body(),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return not_approve_agent_profile(db=db, token=user_token, user_id=user_id, step_no=step_no, reason=reason)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to not approve user: {str(e)}"
        )

@router.post("/add-agency")
async def add_agency(
        db: Session = Depends(get_session),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        email: str = Body(...),
        phone: str = Body(...),
        name: str = Body(...),
):
    try:
        return insert_agency(db=db, token=user_token,phone=phone,name=name,email=email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add agency: {str(e)}"
        )


@router.get("/get-all-gift", response_model=List[GiftModel])
async def get_all_gifts(
        db: Session = Depends(get_session),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return fetch_all_gifts(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add gift: {str(e)}"
        )


@router.post("/add-gift", response_model=GiftModel)
async def add_gift(
        db: Session = Depends(get_session),
        price: int = Body(...),
        name: str = Body(...),
        image: UploadFile = File(...),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return await insert_gift(db=db, token=user_token, image=image, name=name, price=price)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add gift: {str(e)}"
        )


@router.post("/edit-gift/{gift_id}", response_model=GiftModel)
async def edit_gift(
        gift_id: int,
        db: Session = Depends(get_session),
        price: int = Body(...),
        name: str = Body(...),
        image: Optional[UploadFile] = File(None),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return await update_gift(db=db, token=user_token, image=image, name=name, price=price, gift_id=gift_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit gift: {str(e)}"
        )


@router.delete("/delete-gift/{gift_id}")
async def delete_gift(
        gift_id: int,
        db: Session = Depends(get_session),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken")
):
    try:
        return await remove_gift(db=db, token=user_token, gift_id=gift_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove gift: {str(e)}"
        )

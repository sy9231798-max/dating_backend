from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body, Header
from fastapi import APIRouter, UploadFile, File
from typing import List, Annotated
from sqlmodel import Session
from starlette import status

from src.auth.model_wrapper import LoginRequestBody, LoginResponseWrapper, ClientProfileRequestBody
from src.auth.service import login_user, store_client_profile_image, otp_verification, otp_resent, \
    store_client_profile_video, store_client_profile_detail
from src.database import get_session

router = APIRouter()



@router.post("/login")
async def login(login_model: LoginRequestBody,
                db: Session = Depends(get_session)
                ):
    try:
        return login_user(login_model=login_model, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.post("/verify_otp")
async def verify_otp(
        phone_number: str = Body(...),
        otp: str = Body(...),
        db: Session = Depends(get_session)
):
    try:
        return otp_verification(db=db, phone_number=phone_number, otp=otp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.post("/resent_otp")
async def resent_otp(
        phone_number: str = Body(...),
        db: Session = Depends(get_session)
):
    try:
        return otp_resent(db=db, phone_number=phone_number)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.post("/client-profile-image")
async def upload_client_profile_image(
        profile_picture: UploadFile = File(...),
        other_picture: List[UploadFile] = File(description="Upload multiple images"),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session)
):
    try:
        return await store_client_profile_image(profile_picture, other_picture, db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.post("/client-profile-video")
async def upload_client_profile_video(
        profile_video: UploadFile = File(...),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session)
):
    try:
        return await store_client_profile_video(profile_video, db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


@router.post("/client-profile-detail")
async def upload_client_profile_detail(
        user_data: ClientProfileRequestBody,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session)
):
    try:
        return store_client_profile_detail(
            user_data=user_data,
            token=user_token,
            db=db
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi import APIRouter, UploadFile, File
from typing import List, Annotated
from sqlmodel import Session
from starlette import status

from src.auth.model_wrapper import LoginRequestBody
from src.auth.service import login_user, store_client_profile_image
from src.database import get_session

router = APIRouter()


#
# @router.post("/login")
# async def login(login_model: LoginRequestBody,
#                 db: Session = Depends(get_session)
#                 ):
#     try:
#         return login_user(login_model=login_model, db=db)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to Login: {str(e)}"
#         )


@router.post("/client-profile-image")
async def upload_client_profile_image(
        profile_picture: UploadFile = File(...),
        other_picture: List[UploadFile] = File(description="Upload multiple images"),
        db: Session = Depends(get_session)
):
    try:
        return store_client_profile_image(profile_picture, other_picture, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )

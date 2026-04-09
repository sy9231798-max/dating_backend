from typing import Optional, List

from fastapi import HTTPException
from sqlmodel import Session, select
from starlette import status
from starlette.datastructures import UploadFile

from src.auth.model_wrapper import LoginRequestBody
from src.user.models import UserModel
from src.validator_helper import validate_phone_number
import os

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def login_user(login_model: LoginRequestBody, db: Session):
    try:

        db_user: Optional[UserModel] = db.exec(
            select(UserModel).where(UserModel.phone_number == login_model.phone_number)).first()
        validate_phone_number(login_model.phone_number)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phone Number {login_model.phone_number} does not exist"
            )

        return db_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


async def store_client_profile_image(
        profile_picture: UploadFile,
        other_picture: List[UploadFile],
        db: Session):
    try:
        contents = await profile_picture.read()

        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = generate_filename(ext)

        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(contents)

        return {}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )

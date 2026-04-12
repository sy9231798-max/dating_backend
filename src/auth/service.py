from datetime import datetime, timedelta, timezone
from typing import Optional, List
import secrets
from fastapi import HTTPException
from sqlmodel import Session, select
from starlette import status
from starlette.datastructures import UploadFile

from src.auth.model_wrapper import LoginRequestBody, LoginResponseWrapper, ClientProfileRequestBody
from src.auth.models import OtpModel
from src.image_upload_helper import upload_image, upload_video
from src.password_handler import pwd_context
from src.token_helper import create_token, verify_token
from src.user.models import UserModel, UserAdditionPicture
from src.validator_helper import validate_phone_number

OTP_EXPIRY = 300


def login_user(login_model: LoginRequestBody, db: Session):
    try:

        db_user: Optional[UserModel] = db.exec(
            select(UserModel).where(UserModel.phone_number == login_model.phone_number)).first()
        validate_phone_number(login_model.phone_number)
        if db_user is None:
            user = UserModel(**login_model.dict())
            db.add(user)
            db.commit()
            db.refresh(user)

            db_user = user

        otp = str(secrets.randbelow(1000000)).zfill(6)

        otp_record = OtpModel(
            phone_number=db_user.phone_number,
            hashed_otp=pwd_context.hash(otp),
            expires_at=datetime.now() + timedelta(seconds=OTP_EXPIRY)
        )

        db.add(otp_record)
        db.commit()
        return {
            "status": True,
            "message": f"OTP sent to {db_user.phone_number}",
            "otp": otp
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def otp_resent(db: Session, phone_number: str):
    otp = str(secrets.randbelow(1000000)).zfill(6)

    otp_record = OtpModel(
        phone_number=phone_number,
        hashed_otp=pwd_context.hash(otp),
        expires_at=datetime.now() + timedelta(seconds=OTP_EXPIRY)
    )

    db.add(otp_record)
    db.commit()
    return {
        "status": True,
        "message": f"OTP sent again to {phone_number}",
        "otp": otp
    }


MAX_ATTEMPTS = 5


def otp_verification(phone_number: str, otp: str, db: Session):
    record = db.exec(
        select(OtpModel)
        .where(
            OtpModel.phone_number == phone_number,
            OtpModel.is_used == False,
        )
        .order_by(OtpModel.created_at.desc())
    ).first()

    if not record:
        raise HTTPException(400, "OTP not found")

    if record.is_used:
        raise HTTPException(400, "OTP already used")

    if datetime.now().astimezone() > record.expires_at:
        raise HTTPException(400, "OTP expired")

    if record.attempts >= MAX_ATTEMPTS:
        raise HTTPException(400, "Too many attempts")

    if not pwd_context.verify(otp, record.hashed_otp):
        record.attempts += 1
        db.commit()
        raise HTTPException(400, "Invalid OTP")

    record.is_used = True
    db.commit()

    db_user: Optional[UserModel] = db.exec(select(UserModel).where(UserModel.phone_number == phone_number)).first()
    any_error = (
            db_user.step_1_error not in ["PENDING", "COMPLETED"]
            or db_user.step_2_error not in ["PENDING", "COMPLETED"]
            or db_user.step_3_error not in ["PENDING", "COMPLETED"]
    )
    all_pending = (
            db_user.step_1_error in ["PENDING"]
            and db_user.step_2_error in ["PENDING"]
            and db_user.step_3_error in ["PENDING"]
    )
    if all_pending:
        error_code = status.HTTP_404_NOT_FOUND
    elif any_error:
        error_code = status.HTTP_400_BAD_REQUEST
    else:
        error_code = status.HTTP_200_OK
    return LoginResponseWrapper(
        user_data=db_user,
        token=create_token(db_user, isClient=True),
        error_code=error_code,
        step2_error_message=db_user.step_2_error,
        step3_error_message=db_user.step_3_error,
        step1_error_message=str(db_user.step_1_error)
    )

    return {"message": "Login successful"}


async def store_client_profile_image(
        profile_picture: UploadFile,
        other_picture: List[UploadFile],
        token: str,
        db: Session):
    try:
        token_data = verify_token(token)
        user_id = token_data.get("user_id")

        db_user: Optional[UserModel] = db.exec(select(UserModel).where(UserModel.id == user_id)).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        picture_path = await upload_image(profile_picture)
        db_user.profile_picture = picture_path

        addition_records = [
            UserAdditionPicture(
                image_path=await upload_image(i),
                user_id=user_id
            )
            for i in other_picture
        ]

        db.add_all(addition_records)
        db.commit()
        return {
            "status": True,
            "message": "Picture Uploaded"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


async def store_client_profile_video(
        profile_video: UploadFile,
        token: str,
        db: Session):
    try:
        token_data = verify_token(token)
        user_id = token_data.get("user_id")

        db_user: Optional[UserModel] = db.exec(select(UserModel).where(UserModel.id == user_id)).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        video_path = await upload_video(profile_video)
        db_user.video_picture = video_path
        db.commit()
        return {
            "status": True,
            "message": "Video Uploaded"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def store_client_profile_detail(
        user_data: ClientProfileRequestBody,
        token: str,
        db: Session):
    try:
        token_data = verify_token(token)
        user_id = token_data.get("user_id")

        db_user: Optional[UserModel] = db.exec(select(UserModel).where(UserModel.id == user_id)).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db_user.hobby = user_data.hobby
        db_user.first_name = user_data.first_name
        db_user.last_name = user_data.last_name
        db_user.dob = user_data.dob
        db_user.gender = user_data.gender

        db_user.state = user_data.state
        db_user.city = user_data.city
        db.commit()
        db.refresh(db_user)
        return {
            "status": True,
            "message": "Profile Detail Uploaded"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )

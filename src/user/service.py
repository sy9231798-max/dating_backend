from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select
from starlette import status

from src.auth.model_wrapper import LoginResponseWrapper
from src.token_helper import verify_token, create_token
from src.user.models import UserModel, AccountType


def get_my_information(
        token: str,
        db: Session
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]
        db_user = db.get(UserModel, user_id)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def fetch_profile_status(
        token: str,
        db: Session
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]
        db_user: Optional[UserModel] = db.get(UserModel, user_id)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
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
            addition_image=db_user.addition_images,
            step2_error_message=db_user.step_2_error,
            step3_error_message=db_user.step_3_error,
            step1_error_message=str(db_user.step_1_error)
        )

        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )



def fetch_explore(
        token: str,
        db: Session
):
    try:
        payload = verify_token(token)


        statement = select(UserModel).where(UserModel.account_type == AccountType.AGENT)
        users = db.exec(statement).all()
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )

from fastapi import HTTPException
from sqlmodel import Session, select
from starlette import status

from src.token_helper import verify_token
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

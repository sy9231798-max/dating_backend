import secrets
import string
from typing import Optional

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from sqlalchemy import asc
from sqlmodel import Session, select, or_, desc
from starlette import status

from src.auth.model_wrapper import LoginResponseWrapper
from src.token_helper import verify_token, create_token
from src.user.model_wrapper import ConversationDataResponse, MessageResponse
from src.user.models import UserModel, AccountType, ConversationTable, FriendTable, FriendRequestTable

def generate_code(length=6):
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(secrets.choice(characters) for _ in range(length))

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


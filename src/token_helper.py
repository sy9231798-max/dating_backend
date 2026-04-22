from datetime import datetime, timedelta
from typing import Dict

import jwt
from fastapi import HTTPException
from starlette import status

from parameter import SECRET_KEY, ALGORITHM
from src.super_admin.models import AdminModel
from src.user.models import UserModel


def create_token(user: UserModel, isClient: bool) -> str:
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": "client" if isClient else "user",
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token

def create_admin_token(user: AdminModel) -> str:
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> Dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided"
        )

    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

from fastapi import APIRouter, Header, Depends, HTTPException
from sqlmodel import Session
from starlette import status

from src.database import get_session
from src.user.model_wrapper import MeInformationResponse
from src.user.models import UserModel
from src.user.service import get_my_information

router = APIRouter()


@router.get("/me",response_model=MeInformationResponse)
async def get_me(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return get_my_information(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )

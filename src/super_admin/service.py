from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy import func, asc
from sqlmodel import Session, select
from starlette import status

from src.agent.models import AgentModel
from src.pagination_model import PaginatedResponse, PaginationMeta
from src.password_handler import pwd_context
from src.super_admin.model_wrapper import AdminDashboardResponse
from src.super_admin.models import AdminModel
from src.token_helper import create_token, create_admin_token, verify_token
from src.user.enums import AccountType
from src.user.model_wrapper import UserDataResponse
from src.user.models import UserModel


def login_user(email: str, password: str, db: Session):
    try:
        user = db.exec(select(AdminModel).where(AdminModel.email == email)).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Email {email} does not exist")

        if not pwd_context.verify(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        return {
            "user": user,
            "token": create_admin_token(user)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def fetch_dashboard(token: str, db: Session):
    try:
        # payload = verify_token(token)
        # role = payload["role"]
        role = "admin"
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        total_count = db.exec(
            select(func.count(UserModel.id))
        ).one()
        total_agent = db.exec(select(func.count(UserModel.id)).where(UserModel.account_type == AccountType.AGENT)).one()
        total_user = total_count - total_agent

        total_agency = db.exec(
            select(func.count(AgentModel.id))
        ).one()

        return AdminDashboardResponse(
            total_users=total_user,
            total_agent=total_agent,
            total_agency=total_agency
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


def fetch_all_user(token: str,
                   account_type: Optional[AccountType],
                   page_item: Optional[int],
                   db: Session,
                   page: Optional[int] = 1,
                   ):
    try:
        # payload = verify_token(token)
        # role = payload["role"]
        role = "admin"
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        statement = select(UserModel)
        if account_type is not None:
            statement = statement.where(UserModel.account_type == account_type)

        count_statement = select(func.count()).select_from(statement.subquery())
        total = db.exec(count_statement).one()

        offset = (page - 1) * page_item
        statement = statement.order_by(asc(UserModel.id)).offset(offset).limit(page_item)
        user: Optional[List[UserModel]] = db.exec(statement).all()
        total_pages = (total + page_item - 1) // page_item

        return PaginatedResponse[UserDataResponse](
            data=[UserDataResponse.with_is_pending_status(i) for i in user],
            pagination=PaginationMeta(
                page=page,
                page_item=page_item,
                total=total,
                has_next=page < total_pages,
                has_previous=page > 1,
            )
        )

        return {}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )

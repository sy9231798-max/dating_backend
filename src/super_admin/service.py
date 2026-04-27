from typing import Optional, List

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, asc
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from starlette import status

from src.agent.models import AgentModel
from src.image_upload_helper import upload_image
from src.pagination_model import PaginatedResponse, PaginationMeta
from src.password_handler import pwd_context, generate_code
from src.super_admin.model_wrapper import AdminDashboardResponse
from src.super_admin.models import AdminModel, GiftModel
from src.token_helper import create_token, create_admin_token, verify_token
from src.user.enums import AccountType
from src.user.model_wrapper import UserDataResponse, UserDetailResponse
from src.user.models import UserModel


def login_user(email: str, password: str, db: Session):
    try:
        user = db.exec(select(AdminModel).where(AdminModel.email == email)).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Email {email} does not exist")

        print(
            pwd_context.verify(password, user.password)
        )
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
        statement = statement.options(selectinload(UserModel.addition_images)).order_by(asc(UserModel.id)).offset(
            offset).limit(page_item)
        user: Optional[List[UserModel]] = db.exec(statement).all()
        total_pages = (total + page_item - 1) // page_item

        return PaginatedResponse[UserDetailResponse](
            data=[UserDetailResponse.with_is_pending_status(i) for i in user],
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


def approve_agent_profile(
        user_id: int,
        step_no: int,
        token: str,
        db: Session,
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
        db_user = db.get(UserModel, user_id)
        match step_no:
            case 1:
                db_user.step_1_error = "COMPLETED"
            case 2:
                db_user.step_2_error = "COMPLETED"
            case 3:
                db_user.step_3_error = "COMPLETED"
            case _:
                print()
                return {}

        db.commit()
        return {
            "status": True
        }


    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve user: {str(e)}"
        )


def not_approve_agent_profile(
        user_id: int,
        step_no: int,
        reason: str,
        token: str,
        db: Session,
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
        db_user = db.get(UserModel, user_id)
        match step_no:
            case 1:
                db_user.step_1_error = reason
            case 2:
                db_user.step_2_error = reason
            case 3:
                db_user.step_3_error = reason
            case _:
                print()
                return {}
        db.commit()
        return {
            "status": True
        }


    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to not approve user: {str(e)}"
        )


def insert_agency(
        email: str,
        name: str,
        phone: str,
        token: str,
        db: Session,
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

        is_exist = db.exec(select(AgentModel).where(AgentModel.agent_phone == phone)).first()
        if is_exist:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Phone number {phone} already exists"
            )

        db_agency = AgentModel()

        db_agency.agent_email = email
        db_agency.agent_phone = phone
        db_agency.agent_name = name

        while True:
            agent_code = generate_code()
            is_exist = db.exec(select(AgentModel).where(AgentModel.agent_code == agent_code)).all()
            if is_exist:
                continue
            else:
                break

        db_agency.agent_code = agent_code
        db.add(db_agency)
        db.commit()
        db.refresh(db_agency)
        return db_agency


    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add agency: {str(e)}"
        )


async def insert_gift(token: str,
                      price: int,
                      name: str,
                      image: UploadFile,
                      db: Session,
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

        image_path = await upload_image(image)
        gift = GiftModel(
            name=name,
            price=price,
            image_path=image_path,
        )

        db.add(gift)
        db.commit()
        db.refresh(gift)

        return gift

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add gift: {str(e)}"
        )


async def update_gift(token: str,
                      gift_id: int,
                      price: int,
                      name: str,
                      image: Optional[UploadFile],
                      db: Session,
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
        db_gift = db.get(GiftModel, gift_id)
        if db_gift is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gift not found"
            )

        if image is not None:
            image_path = await upload_image(image)
            db_gift.image_path = image_path

        db_gift.name = name
        db_gift.price = price
        db.commit()
        db.refresh(db_gift)

        return db_gift

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit gift: {str(e)}"
        )


async def remove_gift(token: str,
                      gift_id: int,
                      db: Session,
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
        db_gift = db.get(GiftModel, gift_id)
        if db_gift is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gift not found"
            )

        db.delete(db_gift)

        return {
            "message": "Gift removed",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove gift: {str(e)}"
        )


def fetch_all_gifts(token: str,
                    db: Session,
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

        all_gifts = db.exec(select(GiftModel).order_by(asc(GiftModel.price))).all()
        return all_gifts

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add gift: {str(e)}"
        )

from typing import List, Optional, Type, Dict, Any
import strawberry
from boto3.compat import is_append_mode
from fastapi import Depends, HTTPException
from graphql import GraphQLError
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload
from starlette.requests import Request
from strawberry import Info
from strawberry.extensions import SchemaExtension
from strawberry.fastapi import GraphQLRouter

from src.graphql.models import (
    PublicUserDataType,
    ExploreDataType, PageInfo
)
from src.database import get_session
from src.graphql.models import UserDataType, AdditionImageType
from src.user.models import UserModel
from src.token_helper import verify_token


def get_current_user_payload(info: Info) -> Dict:
    """Extracts and verifies token, returns payload. Raises GraphQLError on failure."""
    token = info.context.get("token", "")
    try:
        payload = verify_token(token)  # your existing function
        return payload
    except HTTPException as e:
        raise GraphQLError(e.detail)


def require_role(info: Info, *allowed_roles: str) -> Dict:
    """Verifies token and checks role. Raises GraphQLError if unauthorized."""
    payload = get_current_user_payload(info)
    role = payload.get("role")
    if role not in allowed_roles:
        raise GraphQLError(f"Access denied. Required role(s): {', '.join(allowed_roles)}")
    return payload


async def get_context(request: Request, db: Session = Depends(get_session)):
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token[7:]

    return {
        "db": db,
        "token": token,
        "request": request
    }


def get_user_data_type(user: UserModel, is_admin: bool = False):
    model = UserDataType(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        is_active=user.is_active,
        created_at=user.created_at,
        is_pending=True,
        video_picture=user.video_picture,
        dob=user.dob,
        lvl=user.lvl,
        hobby=user.hobby,
        profile_picture=user.profile_picture,
        addition_images=[AdditionImageType(
            created_at=images.created_at,
            image_path=images.image_path,
            updated_at=images.updated_at,
            user_id=images.user_id,
            id=images.id
        ) for images in user.addition_images],
        city=user.city,
        score=user.score,
        state=user.state,
        gender=user.gender
    )

    return model if is_admin else model.to_public()


@strawberry.type
class HelloResponse:
    message: str
    user: str


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self, info: Info) -> HelloResponse:
        return HelloResponse(
            message="Hello World!",
            user="asdasd"
        )

    @strawberry.field
    async def explore(self,
                      info: Info,
                      page: int = 1,
                      page_size: int = 10) -> ExploreDataType:
        payload = require_role(info, "user", "admin")
        is_admin = payload.get("role") == "admin"
        db: Session = info.context["db"]

        total_count = db.query(UserModel).count()
        total_pages = (total_count + page_size - 1) // page_size  # ceiling division
        offset = (page - 1) * page_size
        users: Optional[List[Type[UserModel]]] = (
            db.query(UserModel)
            .options(selectinload(UserModel.addition_images))
            .order_by(desc(UserModel.score))
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return ExploreDataType(
            items=[
                get_user_data_type(user, is_admin=is_admin)
                for user in users
            ],
            page_info=PageInfo(
                has_next_page=page < total_pages,
                has_previous_page=page > 1,
                total_count=total_count,
                total_pages=total_pages,
                current_page=page,
            )
        )

    @strawberry.field
    async def user_detail(self, info: Info, id: int) -> UserDataType:
        db: Session = info.context["db"]

        user: Optional[Type[UserModel]] = (
            db.query(UserModel)
            .options(selectinload(UserModel.addition_images))
            .where(UserModel.id == id)
            .first()
        )

        if user is None:
            raise GraphQLError(f"User with id {id} not found")
        return UserDataType(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            is_active=user.is_active,
            created_at=user.created_at,
            is_pending=True,
            video_picture=user.video_picture,
            dob=user.dob,
            lvl=user.lvl,
            hobby=user.hobby,
            profile_picture=user.profile_picture,
            addition_images=[AdditionImageType(
                created_at=images.created_at,
                image_path=images.image_path,
                updated_at=images.updated_at,
                user_id=images.user_id,
                id=images.id
            ) for images in user.addition_images],
            city=user.city,
            score=user.score,
            state=user.state,
            gender=user.gender
        )


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(schema, context_getter=get_context)

from datetime import datetime
from typing import List, Optional, Type

import strawberry
from fastapi import Depends
from graphql import GraphQLError
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload
from strawberry import Info

from src.database import get_session
from src.graphql.models import UserDataType, AdditionImageType
from src.user.models import UserModel


async def get_context(db: Session = Depends(get_session)):
    return {"db": db}


def get_user_data_type(user: UserModel) -> UserDataType:
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


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self) -> str:
        return "Hello"

    @strawberry.field
    async def explore(self, info: Info) -> List[UserDataType]:
        db: Session = info.context["db"]
        users: Optional[List[Type[UserModel]]] = (((db.query(UserModel)
                                                    .options(selectinload(UserModel.addition_images)))
                                                   .order_by(desc(UserModel.score)))
                                                  .all())
        return [
            get_user_data_type(user)
            for user in users
        ]

    @strawberry.field
    async def user_detail(self, info: Info, id: int) -> UserDataType:
        db: Session = info.context["db"]

        user: Optional[Type[UserModel]] = db.query(UserModel).where(UserModel.id == id).first()

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

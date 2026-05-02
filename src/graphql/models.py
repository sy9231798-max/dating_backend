from datetime import datetime
from typing import List, Optional, Annotated, Union
import strawberry

from src.user.enums import Gender


@strawberry.type
class AdditionImageType:
    image_path: str
    created_at: datetime
    updated_at: datetime
    id: int
    user_id: int


@strawberry.type
class PublicUserDataType:
    id: int
    first_name: str
    last_name: str
    profile_picture: str
    video_picture: str
    dob: str
    gender: Gender
    hobby: List[str]
    state: str
    city: str
    lvl: int
    score: int
    created_at: datetime
    addition_images: List[AdditionImageType]
    is_active: bool


@strawberry.type
class UserDataType(PublicUserDataType):
    phone_number: str
    email: str
    is_pending: bool

    def to_public(self) -> PublicUserDataType:
        return PublicUserDataType(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            profile_picture=self.profile_picture,
            video_picture=self.video_picture,
            dob=self.dob,
            gender=self.gender,
            hobby=self.hobby,
            state=self.state,
            city=self.city,
            lvl=self.lvl,
            score=self.score,
            created_at=self.created_at,
            addition_images=self.addition_images,
            is_active=self.is_active,
        )





@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    total_count: int
    total_pages: int
    current_page: int


@strawberry.type
class ExploreDataType:
    items: List[UserDataType]
    page_info: PageInfo
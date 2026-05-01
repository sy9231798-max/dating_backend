from datetime import datetime
from typing import List, Optional

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
class UserDataType:
    id: int
    first_name: str
    last_name: str
    phone_number: str
    email: str
    profile_picture: str
    video_picture: str
    dob: str
    gender: Gender
    hobby: List[str]
    state: str
    city: str
    lvl: int
    is_pending: Optional[bool]
    score: int
    created_at: datetime
    addition_images: List[AdditionImageType]
    is_active: bool

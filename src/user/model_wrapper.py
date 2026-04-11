from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.user.models import Gender


class UserDataResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    profile_picture: str
    video_picture: str
    dob: str
    gender: Gender
    hobby: List[str]
    state: str
    city: str
    created_at: datetime
    is_active: bool

from typing import List

from pydantic import BaseModel

from src.user.models import (
    UserModel, Gender, UserAdditionPicture
)


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_agent: int
    total_agency: int

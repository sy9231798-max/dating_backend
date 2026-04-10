from datetime import datetime
from typing import List, Optional

from src.user.models import UserModel, UserAdditionPicture, UserBaseModel



class MeInformationResponse(UserBaseModel):  # ✅ non-table model
    id: int
    addition_images: List[UserAdditionPicture]
    is_active: bool
    account_type: int
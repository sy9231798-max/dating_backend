from typing import List

from pydantic import BaseModel

from src.user.models import (
    UserModel, Gender
)


class LoginRequestBody(BaseModel):
    phone_number: str
    email: str


class LoginResponseWrapper(BaseModel):
    user_data: UserModel
    token: str
    error_code: int
    step1_error_message: str
    step2_error_message: str
    step3_error_message: str


class ClientProfileRequestBody(BaseModel):
    first_name: str
    last_name: str
    hobby: List[str]
    dob:str
    gender: Gender
    state: str
    city: str
# {
#   "phone_number": "8758865947",
#   "first_name": "Karan",
#   "video_picture": "uploads/20260410_123626_880724.mp4",
#   "dob": "26/10/2001",
#   "hobby": [
#     "Cricket",
#     "Dance"
#   ],
#   "created_at": "2026-04-10T11:44:08.353946+05:30",
#   "step_2_error": "",
#   "updated_at": "2026-04-10T12:47:42.398448+05:30",
#   "last_name": "Giri",
#   "email": "karangiri121@gmail.com",
#   "profile_picture": "uploads/20260410_123122_934512.png",
#   "gender": "female",
#   "id": 1,
#   "step_1_error": "",
#   "step_3_error": "",
#   "addition_images": [
#     {
#       "id": 1,
#       "created_at": "2026-04-10T12:31:22.932723+05:30",
#       "image_path": "uploads/20260410_123122_935700.png",
#       "user_id": 1,
#       "updated_at": "2026-04-10T12:31:22.932723+05:30"
#     },
#     {
#       "id": 2,
#       "created_at": "2026-04-10T12:31:22.932723+05:30",
#       "image_path": "uploads/20260410_123122_937257.png",
#       "user_id": 1,
#       "updated_at": "2026-04-10T12:31:22.932723+05:30"
#     },
#     {
#       "id": 3,
#       "created_at": "2026-04-10T12:31:22.932723+05:30",
#       "image_path": "uploads/20260410_123122_937915.png",
#       "user_id": 1,
#       "updated_at": "2026-04-10T12:31:22.932723+05:30"
#     }
#   ]
# }
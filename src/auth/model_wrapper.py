from pydantic import BaseModel


class LoginRequestBody(BaseModel):
    phone_number: str
    email: str
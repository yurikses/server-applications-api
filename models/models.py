from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class UserModel(BaseModel):
    name: Annotated[str, Field(min_length=3)]
    email: EmailStr
    password: Annotated[str, Field(min_length=6)]
    is_subscribed: bool
    age: int


class UserModelWithToken(UserModel):
    session_token: str

class LoginRequest(BaseModel):
    username: str
    password: str

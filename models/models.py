from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class ErrorResponse(BaseModel):
    message: str


class UserRequest(BaseModel):
    name: Annotated[str, Field(min_length=3)]
    email: EmailStr
    password: Annotated[str, Field(min_length=6)]
    is_subscribed: bool
    age: int


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    is_subscribed: bool
    age: int


class UserModel(UserRequest):
    session_token: str
    id: str


class LoginRequest(BaseModel):
    username: str
    password: str

from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CommonHeaders(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    user_agent: str | None = Field(default=None, alias="User-Agent")
    accept_language: str | None= Field(default=None, alias="Accept-Language")


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

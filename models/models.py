from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: Annotated[str, Field(description="The user's email address")]

class User(UserBase):
    password: Annotated[str, Field(description="The user's password")]
    
class UserInDB(UserBase):
    hashed_password: Annotated[str, Field(description="The user's hashed password")]
    

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TodoUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool

class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    


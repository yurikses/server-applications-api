from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: Annotated[str, Field(description="The user's email address")]

class User(UserBase):
    password: Annotated[str, Field(description="The user's password")]
    
class UserInDB(UserBase):
    hashed_password: Annotated[str, Field(description="The user's hashed password")]
    


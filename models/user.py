from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    username: str
    age: Annotated[int, Field( gt=18)] ## conint убран в пользу Annotated
    email: EmailStr    
    password:Annotated[str, Field( min_length=8, max_length=16)] ## constr убран в пользу Annotated
    phone: Optional[str] = 'Unknown'

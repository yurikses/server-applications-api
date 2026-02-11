from re import IGNORECASE, search
from pydantic import BaseModel,Field, field_validator


class User(BaseModel):
    name: str
    age: int
    id: int | None = None
    
class Feedback(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    message: str = Field(min_length=10, max_length=500)
    
    @field_validator("message", mode="after")
    @classmethod
    def check_words(cls, value: str) -> str:
        regex = r"\b(кринж\w*|рофл\w*|вайб\w*)\b"
        if(search(regex, value, IGNORECASE)):
            raise ValueError("Использование недопустимых слов")
            
        return value
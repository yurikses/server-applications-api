from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr

app = FastAPI()

fake_users_db = {}


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    age: int


@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    fake_users_db[user.username] = user.model_dump()
    return {"message": "User created", "user": fake_users_db[user.username]}


@app.get("/users/{username}", status_code=status.HTTP_200_OK)
async def get_user(username: str):
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return fake_users_db[username]


@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str):
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    del fake_users_db[username]


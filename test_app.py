# crud_app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


fake_users_db = {}

class UserCreate(BaseModel):
    username: str
    email: str


@app.post("/users", status_code=201)
def create_user(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    fake_users_db[user.username] = user.model_dump()
    return {"message": "User created", "user": fake_users_db[user.username]}


@app.get("/users/{username}")
def get_user(username: str):
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return fake_users_db[username]


@app.delete("/users/{username}")
def delete_user(username: str):
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    del fake_users_db[username]
    return {"message": "User deleted successfully"}

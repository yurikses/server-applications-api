from typing import Literal
import uuid
from enum import Enum

from fastapi import Cookie, FastAPI, Response
from fastapi.responses import FileResponse

from lib.utils import generate_token
from models.models import ErrorResponse, LoginRequest, UserModel, UserRequest, UserResponse

SECRET_KEY = "your_secret_key"

app = FastAPI()
users: list[UserModel] = []
sample_product_1 = {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99,
}

sample_product_2 = {
    "product_id": 456,
    "name": "Phone Case",
    "category": "Accessories",
    "price": 19.99,
}

sample_product_3 = {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99,
}

sample_product_4 = {
    "product_id": 101,
    "name": "Headphones",
    "category": "Accessories",
    "price": 99.99,
}

sample_product_5 = {
    "product_id": 202,
    "name": "Smartwatch",
    "category": "Electronics",
    "price": 299.99,
}

sample_products = [
    sample_product_1,
    sample_product_2,
    sample_product_3,
    sample_product_4,
    sample_product_5,
]


@app.post("/create_user")
def create_user(user: UserRequest) -> UserResponse:
    new_user = UserModel(**user.model_dump(), session_token="", id=str(uuid.uuid4()))
    users.append(new_user)
    return UserResponse(**new_user.model_dump())


@app.get("/product/{product_id}")
def get_product(product_id: int) -> dict | None:
    for product in sample_products:
        if product["product_id"] == product_id:
            return product
    return None


@app.get("/products/search")
def search_product(keyword: str, category: str, limit: int) -> list[dict] | None:
    results = []
    for product in sample_products:
        if keyword in product["name"] and category == product["category"]:
            if results.__len__() < limit:
                results.append(product)

    return results if results.__len__() > 0 else None


@app.post("/login")
def login(response: Response, request: LoginRequest) -> str | ErrorResponse:
    for user in users:
        if user.name == request.username and user.password == request.password:
            user.session_token = (
                user.id + "." + generate_token({"user_id": user.name}, SECRET_KEY)
            )
            response.set_cookie(
                key="session_token", value=user.session_token, httponly=True
            )
            return "Login successful"
    return ErrorResponse(message="Invalid username or password")


# return code 401 and message "Unauthorized" if the user is not authenticated
@app.get("/user")
def get_user(response: Response, session_token: str = Cookie()) -> UserResponse |  ErrorResponse:
    for user in users:
        if user.session_token == session_token:
            return UserResponse(**user.model_dump())
    
    response.status_code = 401
    return ErrorResponse(message="Unauthorized") 

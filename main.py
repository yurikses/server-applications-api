import uuid
from fastapi import FastAPI, Response, Cookie
from fastapi.responses import FileResponse
from models.models import UserModel, UserModelWithToken, LoginRequest
from enum import Enum


app = FastAPI()
users: list[UserModelWithToken] = []
sample_product_1 = {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99
}

sample_product_2 = {
    "product_id": 456,
    "name": "Phone Case",
    "category": "Accessories",
    "price": 19.99
}

sample_product_3 = {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99
}

sample_product_4 = {
    "product_id": 101,
    "name": "Headphones",
    "category": "Accessories",
    "price": 99.99
}

sample_product_5 = {
    "product_id": 202,
    "name": "Smartwatch",
    "category": "Electronics",
    "price": 299.99
}

sample_products = [sample_product_1, sample_product_2, sample_product_3, sample_product_4, sample_product_5]




    
@app.post('/create_user')
def create_user(user: UserModel) -> UserModel:
    user_with_token = UserModelWithToken(**user.model_dump(), session_token="")
    users.append(user_with_token)
    return user
    
    
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
            if(results.__len__() < limit):
                results.append(product)
    
    return results if results.__len__() > 0 else None
    
@app.post("/login")
def login(response: Response, request: LoginRequest ) -> str:
    print(request.username, request.password)
    for user in users:
        if user.name == request.username and user.password == request.password:
            user.session_token = str(uuid.uuid4())
            response.set_cookie(key="session_token", value=user.session_token, httponly=True)
            return "Login successful"
    return "Invalid username or password"
    
@app.get("/user")
def get_user(session_token: str = Cookie()) -> UserModel | None:
    for user in users:
        if user.session_token == session_token:
            return user
    return None
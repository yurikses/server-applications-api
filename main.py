import uuid
from enum import Enum
from typing import Annotated, Literal

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic_core.core_schema import NoInfoWrapValidatorFunction

from lib.utils import generate_token, get_timestamp
from models.models import (
    CommonHeaders,
    ErrorResponse,
    LoginRequest,
    UserModel,
    UserRequest,
    UserResponse,
)

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


def get_user_by_token(session_token: str) -> UserModel | None:
    for user in users:
        if user.session_token == session_token:
            return user
    return None


def get_user_by_id(user_id: str) -> UserModel | None:
    for user in users:
        if user.id == user_id:
            return user
    return None


def validate_token(session_token: str) -> Literal[True] | ErrorResponse:
    user = get_user_by_token(session_token)
    if user is None:
        return ErrorResponse(message="Invalid session token")
    user_id, timestamp, tokenData, tokenSalt = user.session_token.split(".")

    if user_id is None or timestamp is None or tokenData is None or tokenSalt is None:
        return ErrorResponse(message="Invalid session token")

    if get_timestamp() - int(timestamp) > 300:
        return ErrorResponse(message="Session expired")

    if ".".join([tokenData, tokenSalt]) != generate_token(
        {"user_id": user_id}, SECRET_KEY
    ):
        return ErrorResponse(message="Invalid session token")

    return True


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
                user.id
                + "."
                + str(get_timestamp())
                + "."
                + generate_token({"user_id": user.id}, SECRET_KEY)
            )
            response.set_cookie(
                key="session_token",
                value=user.session_token,
                httponly=True,
                max_age=300,
            )
            return "Login successful"
    return ErrorResponse(message="Invalid username or password")

@app.get("/profile")
def get_user(
    response: Response, session_token: str = Cookie()
) -> UserResponse | ErrorResponse:

    result = validate_token(session_token)
    if isinstance(result, ErrorResponse):
        response.delete_cookie(key="session_token")
        response.status_code = 401
        return result
    user = get_user_by_token(session_token)
    if user is None:
        response.delete_cookie(key="session_token")
        response.status_code = 401
        return ErrorResponse(message="Unauthorized")

    data = session_token.split(".")
    timestamp = data[1]
    delta_time = get_timestamp() - int(timestamp)
    if 180 <= delta_time < 300:
        user.session_token = (
            user.id
            + "."
            + str(get_timestamp())
            + "."
            + generate_token({"user_id": user.id}, SECRET_KEY)
        )
        response.set_cookie(
            key="session_token",
            value=user.session_token,
            httponly=True,
            max_age=300,
        )

    return UserResponse(**user.model_dump())


def get_common_headers(
    user_agent: Annotated[str | None, Header(alias="User-Agent")] = None,
    accept_language: Annotated[str | None, Header(alias="Accept-Language")] = None,
) -> CommonHeaders:
    return CommonHeaders(user_agent=user_agent, accept_language=accept_language)


@app.get("/headers")
def get_headers(response: Response, headers: Annotated[CommonHeaders, Depends(get_common_headers)]) -> dict:
    user_agent = headers.user_agent
    accept_language = headers.accept_language
    if user_agent is None or accept_language is None:
        raise HTTPException(status_code=400, detail="Missing required headers")
        
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language,
    }
    
@app.get("/info")
def get_info(response: Response, headers: Annotated[CommonHeaders, Depends(get_common_headers)]):
    user_agent = headers.user_agent
    accept_language = headers.accept_language
    if user_agent is None or accept_language is None:
        raise HTTPException(status_code=400, detail="Missing required headers")
    
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны!",
        "headers": {
            "User-Agent": user_agent,
            "Accept-Language": accept_language,
        },
    }

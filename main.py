import datetime
import logging
import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from lib.jwt import create_jwt_token, decode_jwt_token
from lib.utils import get_timestamp, hash_password, verify_password
from models.models import User, UserInDB

FAKE_DB = [
    {
        "username": "admin",
        "password": hash_password("admin"),
    }
]

load_dotenv()
mode = os.getenv("MODE", "DEV")
if mode not in ("DEV", "PROD"):
    mode = "DEV"

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.state.limiter = limiter

async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    
    return JSONResponse(
        status_code=429, 
        content={"detail": f"Слишком много запросов. Лимит: {exc.detail}"},
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)  # type: ignore
app.add_middleware(SlowAPIMiddleware)

security = HTTPBasic()
security_bearer = HTTPBearer()
logger = logging.getLogger("uvicorn.error")


def find_user(username: str) -> dict[str, str] | None:
    for user in FAKE_DB:
        if secrets.compare_digest(user.get("username", ""), username):
            return user
    return None


# Функция для проверки пользователя в базе данных
def verify_user(user: User):
    logger.info(f"Попытка авторизации пользователя: {user.username}")
    founded_user = find_user(user.username)

    if founded_user is None:
        logger.warning(f"Пользователь не найден: {user.username}")
        raise HTTPException(
            status_code=404,
            detail="User not found",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not verify_password(user.password, founded_user.get("password", "")):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info(f"Пользователь в базе данных: {founded_user.get('username', '')}")

    return user


# Функция для аутентификации пользователя
def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    logger.info(f"Получены учетные данные: {credentials.username}")
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=401,
            detail="Username and password are required",
            headers={"WWW-Authenticate": "Basic"},
        )
    user = User(username=credentials.username, password=credentials.password)
    valid_user = verify_user(user)
    return valid_user


@app.get("/login")
def login(valid_user: User = Depends(auth_user)):

    return {"message": f"Welcom, {valid_user.username}!"}



@app.post("/register")
@limiter.limit("1/minute")
def register(request: Request, user: User):

    logger.info(f"Получены учетные данные: {user.username}, {user.password}")

    if find_user(user.username) is not None:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    logger.info(f"Регистрация нового пользователя: {user.username}, {user.password}")

    hashed_password = hash_password(user.password)
    user_in_db = UserInDB(username=user.username, hashed_password=hashed_password)

    FAKE_DB.append(
        {
            "username": user_in_db.username,
            "password": user_in_db.hashed_password,
        }
    )

    print(FAKE_DB)
    return {"message": "Successfully registered!"}



@app.post("/login")
@limiter.limit("5/minute")
def login_jwt(request: Request, user: User):

    logger.info(f"Получены учетные данные: {user.username}, {user.password}")
    user = verify_user(user)

    jwt = create_jwt_token(
        data={
            "sub": user.username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(minutes=15),
        },
        secret_key=os.getenv("JWT_SECRET_KEY", "default_secret"),
    )

    return {"access_token": jwt}


@app.get("/protected_resource")
def protected_resource(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
):
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_jwt_token(
            token,
            secret_key=os.getenv("JWT_SECRET_KEY", "default_secret"),
        )
        username = payload.get("username")
        return {"message": f"Hello, {username}! This is a protected resource."}
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


if mode == "DEV":

    @app.get("/docs", include_in_schema=False)
    def custom_swagger_ui_html(valid_user: User = Depends(auth_user)):
        logger.info(
            f"Проверка доступа к документации для пользователя: {valid_user.username}, {valid_user.password}"
        )
        logger.info(
            f"Ожидаемые учетные данные: {os.getenv('DOCS_USER', '')}, {os.getenv('DOCS_PASSWORD', '')}"
        )

        if not secrets.compare_digest(
            valid_user.username, os.getenv("DOCS_USER", "")
        ) or not secrets.compare_digest(
            valid_user.password, os.getenv("DOCS_PASSWORD", "")
        ):
            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Basic"},
            )

        return get_swagger_ui_html(
            openapi_url="/openapi.json", title="API Documentation"
        )

    @app.get("/openapi.json", include_in_schema=False)
    def get_openapi_endpoint(valid_user: User = Depends(auth_user)):

        if not secrets.compare_digest(
            valid_user.username, os.getenv("DOCS_USER", "")
        ) or not secrets.compare_digest(
            valid_user.password, os.getenv("DOCS_PASSWORD", "")
        ):
            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Basic"},
            )

        return get_openapi(title="My API", version="1.0.0", routes=app.routes)

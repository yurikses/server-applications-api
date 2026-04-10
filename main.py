import logging
import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from lib.utils import hash_password, verify_password
from models.models import User, UserInDB

load_dotenv()
mode = os.getenv("MODE", "DEV")

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
security = HTTPBasic()


logger = logging.getLogger("uvicorn.error")

FAKE_DB = [
    {
        "username": "admin",
        "password": hash_password("admin"),
    }
]


def find_user(username: str) -> dict[str, str] | None:
    for user in FAKE_DB:
        if secrets.compare_digest(user.get("username", ""), username):
            return user
    return None


# Функция для проверки пользователя в базе данных
def verify_user(user: User):
    logger.info(f"Попытка авторизации пользователя: {user.username}")
    founded_user = find_user(user.username)

    if founded_user is None or not verify_password(
        user.password, founded_user.get("password", "")
    ):
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
def register(user: User):

    logger.info(f"Получены учетные данные: {user.username}, {user.password}")

    if user.username in FAKE_DB:
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
    return {"message": "Successfully registered"}


if mode == "DEV":

    @app.get("/docs", include_in_schema=False)
    def custom_swagger_ui_html(valid_user: User = Depends(auth_user)):
        logger.info(
            f"Проверка доступа к документации для пользователя: {valid_user.username}, {valid_user.password}"
        )
        logger.info(f"Ожидаемые учетные данные: {os.getenv('DOCS_USER', '')}, {os.getenv('DOCS_PASSWORD', '')}")
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

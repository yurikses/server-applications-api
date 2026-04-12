import datetime
import logging
import os
import secrets
import sqlite3
from lib.database import get_db_connection, init_db
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from lib.jwt import create_jwt_token, decode_jwt_token
from lib.utils import hash_password, verify_password
from models.models import TodoCreate, TodoResponse, TodoUpdate, User, UserInDB

FAKE_DB = [
    {"username": "admin", "password": hash_password("admin"), "role": "admin"},
    {"username": "user1", "password": hash_password("123"), "role": "user"},
]


ROLE_PERMISSIONS = {
    "admin": ["create", "read", "update", "delete"],
    "user": ["read", "update"],
    "guest": ["read"],
}

init_db()
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

class RoleChecker:
    """
    Класс для проверки ролей пользователя на основе JWT токена. \n
    Принимает список разрешенных ролей и проверяет, соответствует ли роль пользователя одной из них.\n
    Если роль не соответствует, выбрасывает HTTPException с кодом 403. \n
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
        token = credentials.credentials
        
        if not token:
            raise HTTPException(status_code=401, detail="Token is missing")

        try:
            payload = decode_jwt_token(
                token,
                secret_key=os.getenv("JWT_SECRET_KEY", "default_secret"),
            )
            
            user_role = payload.get("role")
        
            if user_role not in self.allowed_roles:
                logger.warning(f"Отказ в доступе. Пользователь: {payload.get('sub')}, Роль: {user_role}")
                raise HTTPException(
                    status_code=403, 
                    detail=f"Operation not permitted. Required roles: {self.allowed_roles}"
                )
                
            return payload 
            
        except ValueError as e:
            logger.warning(f"Ошибка при декодировании JWT токена: {str(e)}")
            raise HTTPException(status_code=401, detail=str(e))

allow_admin = RoleChecker(["admin"])
allow_user = RoleChecker(["admin", "user"])
allow_guest = RoleChecker(["admin", "user", "guest"])
allow_admin_user = RoleChecker(["admin", "user"])

def find_user(username: str) -> dict[str, str] | None:
    
    """Ищет пользователя в базе данных по имени пользователя. Если пользователь найден, возвращает словарь с данными пользователя, иначе возвращает None."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    return {
        "username": row["username"],
        "password": row["password"],
        "role": row["role"] if "role" in row.keys() else "user"
    }

def verify_user(user: User):
    """Проверяет, существует ли пользователь в базе данных и совпадает ли пароль. Если пользователь не найден или пароль неверный, выбрасывает HTTPException. Если все проверки проходят успешно, возвращает объект User."""
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=400, detail="Username already exists")
        

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user.username, hash_password(user.password))
        )
        
        conn.commit()
        
    finally:
        conn.close()
    return {"message": "User registered successfully!"}

@app.post("/login")
@limiter.limit("5/minute")
def login_jwt(request: Request, user: User):

    logger.info(f"Получены учетные данные: {user.username}, {user.password}")
    verify_user(user)
    founded_user = find_user(user.username)
    if founded_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(user.password, founded_user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    
    user_role = founded_user.get("role", "user")  # pyright: ignore[reportOptionalMemberAccess]

    jwt = create_jwt_token(
        data={
            "sub": user.username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(minutes=15),
            "role": user_role,
        },
        secret_key=os.getenv("JWT_SECRET_KEY", "default_secret"),
    )

    return {"access_token": jwt}

@app.get("/protected_resource")
def protected_resource(current_user: dict = Depends(allow_admin_user)):
    
    username = current_user.get("sub", "")
    role = current_user.get("role", "guest")
    
    return {"message": f"Hello, {username}! This is a protected resource. Your role is: {role}."}

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


@app.post("/todos", response_model=TodoResponse)
def create_todo(todo: TodoCreate, current_user: dict = Depends(allow_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
        (todo.title, todo.description, 0)
    )
    conn.commit()
    todo_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": todo_id,
        "title": todo.title,
        "description": todo.description,
        "completed": False
    }


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, current_user: dict = Depends(allow_guest)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Todo not found")
        
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"])
    }

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate, current_user: dict = Depends(allow_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")
        
    cursor.execute(
        "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
        (todo.title, todo.description, int(todo.completed), todo_id)
    )
    conn.commit()
    conn.close()
    
    return {
        "id": todo_id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed
    }

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, current_user: dict = Depends(allow_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")
        
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Todo deleted successfully!"}


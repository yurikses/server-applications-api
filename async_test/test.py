import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from faker import Faker

from app import app, fake_users_db

fake = Faker()

@pytest.fixture(autouse=True)
def clear_db():
    fake_users_db.clear()
    yield

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
class TestAsyncUserEndpoints:
    async def test_create_user_success(self, async_client: AsyncClient):
        """создание пользователя и валидация структуры ответа"""
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "age": fake.random_int(min=18, max=99)
        }
    
        response = await async_client.post("/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User created"
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["age"] == user_data["age"]

    async def test_get_existing_user(self, async_client: AsyncClient):
        """получение существующего пользователя"""
        username = fake.user_name()
        fake_users_db[username] = {"username": username, "email": fake.email(), "age": 25}

        response = await async_client.get(f"/users/{username}")
        
        assert response.status_code == 200
        assert response.json()["username"] == username

    async def test_get_nonexistent_user(self, async_client: AsyncClient):
        """попытка получить несуществующего пользователя"""
        random_name = fake.user_name()
        response = await async_client.get(f"/users/{random_name}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    async def test_delete_existing_user(self, async_client: AsyncClient):
        """удаление существующего пользователя"""
        username = fake.user_name()
        fake_users_db[username] = {"username": username, "email": fake.email(), "age": 30}
        
        response = await async_client.delete(f"/users/{username}")
        
        assert response.status_code == 204
        assert username not in fake_users_db

    async def test_delete_nonexistent_user(self, async_client: AsyncClient):
        """повторное удаление того же пользователя"""
        username = fake.user_name()
        fake_users_db[username] = {"username": username, "email": fake.email(), "age": 30}
        
        await async_client.delete(f"/users/{username}")
        
        response = await async_client.delete(f"/users/{username}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

import pytest
from fastapi.testclient import TestClient
from test_app import app, fake_users_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    fake_users_db.clear()
    yield


class TestUserEndpoints:

    # ТЕСТЫ СОЗДАНИЯ (POST /users)
    def test_create_user_success(self):
        """Проверка успешного создания пользователя"""
        response = client.post("/users", json={"username": "alice", "email": "alice@test.com"})
        assert response.status_code == 201
        assert response.json()["message"] == "User created"
        assert response.json()["user"]["username"] == "alice"

    def test_create_user_duplicate(self):
        """Проверка ошибки при создании существующего пользователя (Крайний случай)"""

        client.post("/users", json={"username": "alice", "email": "alice@test.com"})
        response = client.post("/users", json={"username": "alice", "email": "alice@test.com"})
        assert response.status_code == 400
        assert response.json()["detail"] == "User already exists"

    def test_create_user_invalid_data(self):
        """Проверка ошибки при отправке неверных данных (отсутствует email)"""
        response = client.post("/users", json={"username": "alice"})
        assert response.status_code == 422 

    # ТЕСТЫ ЧТЕНИЯ (GET /users/{username})
    def test_get_user_success(self):
        """Проверка успешного извлечения данных"""
        client.post("/users", json={"username": "bob", "email": "bob@test.com"})
        response = client.get("/users/bob")
        assert response.status_code == 200
        assert response.json()["email"] == "bob@test.com"

    def test_get_user_not_found(self):
        """Проверка извлечения несуществующего пользователя"""
        response = client.get("/users/unknown_user")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    # ТЕСТЫ УДАЛЕНИЯ (DELETE /users/{username})
    def test_delete_user_success(self):
        """Проверка успешного удаления"""
        client.post("/users", json={"username": "charlie", "email": "charlie@test.com"})
        delete_response = client.delete("/users/charlie")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "User deleted successfully"
        
        get_response = client.get("/users/charlie")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self):
        """Проверка удаления несуществующего пользователя"""
        response = client.delete("/users/ghost")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
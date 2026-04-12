# Практическая работа по FastAPI

В данном репозитории реализовано API с использованием FastAPI, встроенной базы данных SQLite, аутентификацией по JWT токену и ролевой моделью доступа (RBAC).

## Как установить зависимости и запустить приложение

1. **Клонируйте репозиторий и перейдите в папку проекта:**
   ```bash
   git clone https://github.com/yurikses/server-applications-api/tree/ThirdPractice
   ```

2. **Установите необходимые зависимости:**
   Убедитесь, что у вас активировано виртуальное окружение, затем выполните:
   ```bash
   pip install -r requirements.txt
   ```


3. **Настройте переменные окружения:**
   Измените файл `.env.example` на `.env` и вставьте следующие значения (можете изменить их по своему усмотрению):
   ```env
   MODE=DEV
   JWT_SECRET_KEY=super_secret_key
   DOCS_USER=admin
   DOCS_PASSWORD=admin
   ```

4. **Запустите сервер для разработки:**
   ```bash
   uvicorn main:app --reload
   ```
   База данных SQLite и необходимые таблицы создадутся автоматически при первом запуске приложения.

---

## Как тестировать ключевые эндпоинты (через curl)

Ниже приведены примеры команд `curl` для тестирования основного функционала в терминале. 

### 1. Регистрация нового пользователя
Эндпоинт ограничен лимитом (1 запрос в минуту).
```bash
curl -X POST "http://127.0.0.1:8000/register" \
     -H "Content-Type: application/json" \
     -d "{\"username\":\"test_user\", \"password\":\"mypassword\"}"
```

### 2. Авторизация (Получение JWT токена)
После успешного логина вы получите JSON с полем `access_token`. Скопируйте этот токен — он понадобится для доступа к защищенным маршрутам.
```bash
curl -X POST "http://127.0.0.1:8000/login" \
     -H "Content-Type: application/json" \
     -d "{\"username\":\"test_user\", \"password\":\"mypassword\"}"
```

### 3. Проверка защищенного ресурса
Замените `ВАШ_ТОКЕН` на реальный токен, полученный на предыдущем шаге.
```bash
curl -X GET "http://127.0.0.1:8000/protected_resource" \
     -H "Authorization: Bearer ВАШ_ТОКЕН"
```

### 4. Создание задачи (Todo)
*Доступно для ролей: **admin**, **user**.*
```bash
curl -X POST "http://127.0.0.1:8000/todos" \
     -H "Authorization: Bearer ВАШ_ТОКЕН" \
     -H "Content-Type: application/json" \
     -d "{\"title\":\"Купить молоко\", \"description\":\"В магазине\"}"
```

### 5. Получение задачи по ID
*Доступно для ролей: **admin**, **user**, **guest**.*
```bash
curl -X GET "http://127.0.0.1:8000/todos/1" \
     -H "Authorization: Bearer ВАШ_ТОКЕН"
```

### 6. Обновление задачи (Todo) по ID
*Доступно для ролей: **admin**, **user**.*
```bash
curl -X PUT "http://127.0.0.1:8000/todos/1" \
     -H "Authorization: Bearer ВАШ_ТОКЕН" \
     -H "Content-Type: application/json" \
     -d "{\"title\":\"Купить хлеб\", \"description\":\"И молоко тоже\", \"completed\":true}"
```

### 7. Удаление задачи по ID
*Доступно ТОЛЬКО для роли: **admin**.*
```bash
curl -X DELETE "http://127.0.0.1:8000/todos/1" \
     -H "Authorization: Bearer ВАШ_ТОКЕН"
```

---

## Документация API
В режиме разработки (`MODE=DEV`) доступна встроенная интерактивная документация:
**http://127.0.0.1:8000/docs**

Доступ к документации защищен базовой аутентификацией. Потребуется ввести логин и пароль, указанные в переменных окружения (`DOCS_USER` / `DOCS_PASSWORD`).
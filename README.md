# TamaDa

Веб-приложение для каталога событий: публичные и личные встречи, запись участников, приглашения по email со ссылкой с токеном. Реализовано на **Django 4.2** с шаблонами (MVT) и **Django REST Framework** + **JWT** для API.

## Технологии

Python 3.10+  
Django 4.2+  
Django REST Framework 3.16+  
djangorestframework-simplejwt 5.5+  
PostgreSQL  

## Требования

- Python 3.10+ (проверено на 3.9+ в типичных окружениях).
- **PostgreSQL** — создайте базу (например `tamada`) и пользователя с правами на неё; параметры подключения задаются в `.env`.

## Установка и запуск

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux / macOS

pip install -r requirements.txt
```

В корне проекта скопируйте шаблон и подставьте свои значения:

```bash
cp .env.example .env   # Linux / macOS
copy .env.example .env   # Windows cmd
```

Затем:

```bash
python manage.py migrate
python manage.py createsuperuser   # по желанию
python manage.py runserver
```

Сайт: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
Админ-панель: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Тесты

```bash
python manage.py test events
```

## API

Префикс: `/api/`. Аутентификация: **JWT** (`Authorization: Bearer <access>`) и сессия для запросов из браузера.

| Метод | Путь | Описание |
|--------|------|----------|
| POST | `/api/auth/register/` | Регистрация, в ответе `access` / `refresh` |
| POST | `/api/auth/token/` | Получение пары токенов (username + password) |
| POST | `/api/auth/token/refresh/` | Обновление access по refresh |
| CRUD | `/api/events/` | События (чтение публичных; свои и записанные — у авторизованных) |
| GET | `/api/events/{id}/registrations/` | Список записей (только организатор) |
| POST / DELETE | `/api/events/{id}/register/` | Запись / отмена записи |
| GET / POST | `/api/events/{id}/invitations/` | Список / создание приглашения по `email` (только организатор) |
| DELETE | `/api/invitations/{id}/` | Отзыв приглашения (организатор события) |
| GET | `/api/me/events/` | События, где пользователь организатор |
| GET | `/api/me/registrations/` | Мои записи на события |

## Структура репозитория

- `config/` — настройки проекта и корневые URL.
- `events/` — модели, представления, формы, API, приглашения, тесты (`events/tests/`).
- `templates/`, `static/` — шаблоны и стили.

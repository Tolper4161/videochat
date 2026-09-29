# VideoChat

Видеочат на Django

## 🚀 Быстрый старт после клонирования

### 1. Клонировать репозиторий

- [ ] `git clone <repo-url> videochat`
- [ ] `cd videochat`

---

### 2. Настроить PostgreSQL

- [ ] Войти в psql: `psql -U postgres`
- [ ] Загрузить дамп videochat_dump.sql
- [ ] Создать пользователя в PostgreSQL:

```sql
ALTER ROLE padmin SET client_encoding TO 'utf8';
ALTER ROLE padmin SET default_transaction_isolation TO 'read committed';
ALTER ROLE padmin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE videochat TO padmin;

\c videochat
GRANT ALL ON SCHEMA public TO padmin;
```

---

### 3. Backend — установка

- [ ] `cd backend`
- [ ] Создать venv:
  - Windows: `python -m venv .venv`
- [ ] Активировать venv:
  - Windows (cmd): `.venv\Scripts\Activate`
- [ ] Убедиться, что в начале строки появилось `(.venv)`
- [ ] Установить зависимости: `pip install -r requirements.txt`

---

### 4. Backend — переменные окружения

- [ ] Переименовать `.env.example` в `.env`
- [ ] Перенести `.env` директорию, где лежит `.env.example` и заполнить:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=videochat
DB_USER=padmin
DB_PASSWORD=<введите пароль от padmin>
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=<сгенерировать ниже>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

- [ ] Сгенерировать `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- [ ] Убедиться, что `.env` **не** попадает в git: `git check-ignore backend/.env` (должен вывести путь)

---

## 🧪 Полезные команды

### Backend

```bash
cd backend
source venv/bin/activate           # активировать окружение

python manage.py runserver         # dev-сервер
python manage.py makemigrations    # создать миграции
python manage.py migrate           # применить миграции
python manage.py createsuperuser   # создать админа
python manage.py shell             # Django shell
python manage.py test              # тесты
python manage.py check             # проверка конфигурации
```

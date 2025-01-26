## Установка

### Требования
- Python 3.10+
- PostgreSQL
- SQLAlchemy
- Pydantic
- Виртуальное окружение (опционально)

### Клонирование репозитория
```
git clone https://github.com/Equialy/java_code_test.git
cd java_code_test
```
- Создать файл .env и .env.docker-compose для использования Docker или локального развертывания. Содержимое по аналогии файла .env.example

### Развертывание через Docker

Для использование Docker-compose выполните следующие шаги находясь в корне проекта:
```
docker compose build
```
```
docker compose up
```

- Запустится база и прогонятся миграции автоматически.

```
Октрыть в браузере по адресу http://localhost:8003/docs
```
### Локальное развертывание
Настройка окружения
1. Создайте виртуальное окружение:
```
python -m venv venv
source venv/bin/activate  # В Windows: venv\Scripts\activate
```

2. Установите зависимости:
```
pip install -r requirements.txt
```
3. Применение миграций базы данных:
```
alembic upgrade head
```
4. Запуск сервера:
```
uvicorn src.main:app --reload
```

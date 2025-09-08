# Простой Dockerfile для локальной разработки
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только необходимые зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем директории
RUN mkdir -p data logs

# Команда запуска
CMD ["python", "bot.py"]

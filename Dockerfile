# Simple build for AntiSpam Bot
FROM python:3.11-slim

# Создание пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Создание директорий
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Установка рабочей директории
WORKDIR /app

# Копирование кода приложения
COPY --chown=appuser:appuser . .

# Переключение на non-root пользователя
USER appuser

# Установка переменных окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Открытие портов
EXPOSE 8000

# Запуск приложения
CMD ["python", "bot.py"]

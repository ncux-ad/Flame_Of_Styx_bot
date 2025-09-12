# 🔧 Руководство по устранению неполадок

## 📋 Обзор

Этот документ содержит описание всех критических ошибок, с которыми мы столкнулись при разработке и настройке AntiSpam Bot, а также их решения.

## 🚨 Критические ошибки и их решения

### 1. **Ошибка: `SyntaxError: illegal target for annotation`**

**Описание:**
```
File "app/auth/authorization.py", line 1
7977609078:AAHEXMbeZQ3asK0vUS60qXSDSgBAvKfNd24"""Enhanced authorization system with proper security checks."""
^^^^^^^^^^
SyntaxError: illegal target for annotation
```

**Причина:** Токен бота случайно попал в начало файла `authorization.py`

**Решение:**
```python
# БЫЛО (неправильно):
7977609078:AAHEXMbeZQ3asK0vUS60qXSDSgBAvKfNd24"""Enhanced authorization system with proper security checks."""

# СТАЛО (правильно):
"""Enhanced authorization system with proper security checks."""
```

**Профилактика:** Всегда проверяйте файлы перед коммитом, используйте линтеры.

---

### 2. **Ошибка: `TypeError: handle_channel_message() missing 1 required positional argument: 'data'`**

**Описание:**
```
TypeError: handle_channel_message() missing 1 required positional argument: 'data'
```

**Причина:** Неправильная сигнатура обработчиков в aiogram 3.x

**Решение:**
```python
# БЫЛО (неправильно):
async def handle_channel_message(message: Message, **kwargs) -> None:

# СТАЛО (правильно):
async def handle_channel_message(message: Message, data: dict = None, **kwargs) -> None:
    if data is None:
        data = kwargs.get("data", {})
```

**Профилактика:** Изучайте документацию aiogram 3.x перед миграцией.

---

### 3. **Ошибка: `TypeError: CallableObject.call() got an unexpected keyword argument 'data'`**

**Описание:**
```
TypeError: CallableObject.call() got an unexpected keyword argument 'data'
```

**Причина:** Неправильная передача данных в middleware

**Решение:**
```python
# В DependencyInjectionMiddleware:
# БЫЛО (неправильно):
return await handler(event, data=data)

# СТАЛО (правильно):
return await handler(event, **data)
```

**Профилактика:** Понимание механизма передачи данных в aiogram 3.x.

---

### 4. **Ошибка: `TypeError: LoggingMiddleware.__call__() got an unexpected keyword argument 'dispatcher'`**

**Описание:**
```
TypeError: LoggingMiddleware.__call__() got an unexpected keyword argument 'dispatcher'
```

**Причина:** Неправильная сигнатура middleware

**Решение:**
```python
# БЫЛО (неправильно):
async def __call__(self, handler, event, data) -> Any:

# СТАЛО (правильно):
async def __call__(self, handler, event, data, **kwargs) -> Any:
```

**Профилактика:** Всегда добавляйте `**kwargs` в сигнатуры middleware.

---

### 5. **Ошибка: `TypeError: LoggingMiddleware.__call__() got multiple values for argument 'handler'`**

**Описание:**
```
TypeError: LoggingMiddleware.__call__() got multiple values for argument 'handler'
```

**Причина:** Конфликт параметров при передаче `**data`

**Решение:**
```python
# В DependencyInjectionMiddleware:
# БЫЛО (неправильно):
return await handler(event, **data)

# СТАЛО (правильно):
handler_data = {k: v for k, v in data.items() if k != 'handler'}
return await handler(event, **handler_data)
```

**Профилактика:** Фильтруйте данные перед передачей в обработчики.

---

### 6. **Ошибка: `TypeError: LoggingMiddleware.__call__() missing 1 required positional argument: 'data'`**

**Описание:**
```
TypeError: LoggingMiddleware.__call__() missing 1 required positional argument: 'data'
```

**Причина:** Неправильная передача данных между middleware

**Решение:**
```python
# В LoggingMiddleware:
# БЫЛО (неправильно):
return await handler(event, **data)

# СТАЛО (правильно):
return await handler(event, data)
```

**Профилактика:** Согласованность в передаче данных между middleware.

---

### 7. **Ошибка: `Profile service not injected properly`**

**Описание:**
```
Profile service not injected properly
Available keys in data: None
```

**Причина:** Сервисы инжектируются в `kwargs`, а не в `data`

**Решение:**
```python
# БЫЛО (неправильно):
profile_service = data.get("profile_service")

# СТАЛО (правильно):
profile_service = kwargs.get("profile_service")
```

**Профилактика:** Понимание механизма DI в aiogram 3.x.

---

### 8. **Ошибка: `ValueError: BOT_TOKEN должен быть в формате 'bot_id:token'`**

**Описание:**
```
ValueError: BOT_TOKEN должен быть в формате 'bot_id:token'
```

**Причина:** Неправильный формат токена

**Решение:**
```bash
# БЫЛО (неправильно):
BOT_TOKEN=AAHEXMbeZQ3asK0vUS60qXSDSgBAvKfNd24

# СТАЛО (правильно):
BOT_TOKEN=7977609078:AAHtedbDkZBvsKTis337DcoDUFswsiEBOwE
```

**Профилактика:** Валидация токенов при конфигурации.

---

### 9. **Ошибка: `TelegramConflictError: terminated by other getUpdates request`**

**Описание:**
```
TelegramConflictError: terminated by other getUpdates request
```

**Причина:** Несколько экземпляров бота запущены одновременно

**Решение:**
```bash
# Остановить все контейнеры
docker-compose down

# Убить все процессы Python
Get-Process python | Stop-Process -Force

# Запустить заново
docker-compose up -d
```

**Профилактика:** Проверка запущенных процессов перед запуском.

---

### 10. **Ошибка: `HTTP Client says - Request timeout error` / `Bad Gateway`**

**Описание:**
```
aiogram.exceptions.TelegramNetworkError: HTTP Client says - Request timeout error
```

**Причина:** Проблемы с сетью или серверами Telegram

**Решение:**
```python
# Добавить retry логику в bot.py
max_retries = 3
for attempt in range(max_retries):
    try:
        await dp.start_polling(bot)
        break
    except TelegramNetworkError as e:
        if attempt < max_retries - 1:
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            await asyncio.sleep(5)
        else:
            raise
```

**Профилактика:** Обработка сетевых ошибок и retry логика.

---

## 🔧 Общие принципы решения проблем

### 1. **Проверка логов**
```bash
# Docker логи
docker logs antispam-bot --tail=50

# Локальные логи
python bot.py 2>&1 | tee bot.log
```

### 2. **Проверка конфигурации**
```python
# Проверка токена
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Проверка переменных окружения
echo $BOT_TOKEN
echo $ADMIN_IDS
```

### 3. **Проверка зависимостей**
```bash
# Активация виртуального окружения
.\venv\Scripts\activate.ps1

# Установка зависимостей
pip install -r requirements.txt
```

### 4. **Проверка Docker**
```bash
# Статус контейнеров
docker ps

# Перезапуск
docker-compose down
docker-compose up -d
```

## 📚 Полезные команды

### Отладка
```bash
# Проверка API Telegram
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Проверка обновлений
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"

# Ping серверов Telegram
ping api.telegram.org
```

### Управление ботом
```bash
# Запуск в Docker
docker-compose up -d

# Остановка
docker-compose down

# Логи в реальном времени
docker logs antispam-bot -f
```

### Управление процессами
```bash
# Поиск процессов Python
Get-Process python

# Остановка всех процессов Python
Get-Process python | Stop-Process -Force
```

## 🎯 Чек-лист перед деплоем

- [ ] Токен бота в правильном формате
- [ ] ADMIN_IDS настроены
- [ ] Все зависимости установлены
- [ ] Middleware зарегистрированы правильно
- [ ] Обработчики имеют правильные сигнатуры
- [ ] Нет синтаксических ошибок
- [ ] Docker контейнер запускается без ошибок
- [ ] API Telegram доступен
- [ ] Логи не содержат критических ошибок

## 📞 Получение помощи

1. **Проверьте логи** - они содержат детальную информацию об ошибках
2. **Изучите этот документ** - большинство проблем уже описаны
3. **Проверьте конфигурацию** - убедитесь, что все настройки корректны
4. **Перезапустите сервисы** - часто помогает решить временные проблемы

---

*Последнее обновление: 12 сентября 2025*

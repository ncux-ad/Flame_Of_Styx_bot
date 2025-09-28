# Redis Rate Limiting

Централизованная система ограничения частоты запросов через Redis для масштабируемости и безопасности.

## 🚀 Возможности

- **Множественные стратегии**: Fixed Window, Sliding Window, Token Bucket
- **Гибкая настройка**: Разные лимиты для пользователей и администраторов
- **Автоматическая блокировка**: Временная блокировка при превышении лимитов
- **Высокая производительность**: Оптимизированные Redis операции
- **Fallback режим**: Автоматический переход на локальный rate limiting при недоступности Redis

## 📋 Стратегии Rate Limiting

### 1. Fixed Window (Фиксированное окно)
- **Принцип**: Счетчик сбрасывается каждую минуту
- **Преимущества**: Простота, низкое потребление памяти
- **Недостатки**: Возможны всплески в начале окна
- **Использование**: Для простых случаев с умеренной нагрузкой

### 2. Sliding Window (Скользящее окно)
- **Принцип**: Использует Redis Sorted Set для точного отслеживания
- **Преимущества**: Точность, плавное ограничение
- **Недостатки**: Больше потребление памяти
- **Использование**: Рекомендуется по умолчанию

### 3. Token Bucket (Ведро токенов)
- **Принцип**: Токены пополняются с фиксированной скоростью
- **Преимущества**: Позволяет кратковременные всплески
- **Недостатки**: Сложность настройки
- **Использование**: Для burst-нагрузки

## ⚙️ Конфигурация

### Переменные окружения

```bash
# Redis настройки
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# Rate limiting настройки
REDIS_USER_LIMIT=10          # Лимит для пользователей
REDIS_ADMIN_LIMIT=100        # Лимит для администраторов
REDIS_INTERVAL=60            # Интервал в секундах
REDIS_STRATEGY=sliding_window # Стратегия (fixed_window, sliding_window, token_bucket)
REDIS_BLOCK_DURATION=300     # Длительность блокировки в секундах
```

### Настройки в коде

```python
from app.middlewares.redis_rate_limit import RedisRateLimitMiddleware

middleware = RedisRateLimitMiddleware(
    user_limit=10,           # Лимит для пользователей
    admin_limit=100,         # Лимит для администраторов
    interval=60,             # Интервал в секундах
    strategy="sliding_window", # Стратегия
    redis_key_prefix="rate_limit", # Префикс ключей
    block_duration=300       # Длительность блокировки
)
```

## 🏗️ Архитектура

### Компоненты

1. **RedisService** (`app/services/redis.py`)
   - Управление соединением с Redis
   - Базовые операции (get, set, incr, etc.)
   - Connection pooling
   - Graceful shutdown

2. **RedisRateLimitMiddleware** (`app/middlewares/redis_rate_limit.py`)
   - Обработка rate limiting
   - Поддержка различных стратегий
   - Механизм блокировки
   - Локальный кэш для оптимизации

3. **Конфигурация** (`app/config.py`)
   - Настройки Redis
   - Параметры rate limiting
   - Валидация конфигурации

### Схема работы

```
Пользователь → Validation → Logging → Redis Rate Limit → DI → Handler
                    ↓
              [Проверка лимитов]
                    ↓
              [Блокировка при превышении]
```

## 🔧 Установка и настройка

### 1. Установка Redis

#### Docker (рекомендуется)
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Windows
```bash
# Через Chocolatey
choco install redis-64

# Или скачать с https://github.com/microsoftarchive/redis/releases
```

### 2. Установка зависимостей

```bash
pip install redis>=5.0.0 aioredis>=2.0.0
```

### 3. Настройка переменных окружения

Создайте файл `.env`:
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
REDIS_USER_LIMIT=10
REDIS_ADMIN_LIMIT=100
REDIS_STRATEGY=sliding_window
```

### 4. Запуск с Docker Compose

```bash
# Запуск с Redis
docker-compose -f docker-compose.redis.yml up -d

# Проверка статуса
docker-compose -f docker-compose.redis.yml ps
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Тест подключения к Redis
python scripts/test_redis_rate_limit.py

# Тест производительности
python -c "
import asyncio
from scripts.test_redis_rate_limit import test_performance
asyncio.run(test_performance())
"
```

### Ручное тестирование

1. **Запустите бота с Redis**:
   ```bash
   REDIS_ENABLED=true python bot.py
   ```

2. **Отправьте много сообщений** быстро:
   ```
   /help
   /help
   /help
   ...
   ```

3. **Проверьте блокировку**:
   - При превышении лимита пользователь получит сообщение о блокировке
   - В логах появится предупреждение о превышении лимита

## 📊 Мониторинг

### Redis команды для мониторинга

```bash
# Подключение к Redis
redis-cli

# Просмотр всех ключей rate limiting
KEYS rate_limit:*

# Просмотр заблокированных пользователей
KEYS rate_limit:blocked:*

# Статистика по памяти
INFO memory

# Мониторинг команд
MONITOR
```

### Логи

Rate limiting события логируются с уровнем WARNING:

```
WARNING:app.middlewares.redis_rate_limit:Rate limit превышен для пользователя 12345 (admin: False, limit: 10)
WARNING:app.middlewares.redis_rate_limit:Пользователь 12345 заблокирован на 300 секунд
```

## 🚨 Устранение неполадок

### Redis недоступен

**Проблема**: `ConnectionError: Error connecting to Redis`

**Решение**:
1. Проверьте, что Redis запущен: `redis-cli ping`
2. Проверьте URL подключения в `REDIS_URL`
3. Проверьте сетевые настройки и файрвол

### Высокое потребление памяти

**Проблема**: Redis использует много памяти

**Решение**:
1. Настройте `maxmemory` в Redis конфигурации
2. Используйте `allkeys-lru` политику
3. Уменьшите `block_duration` для быстрой очистки

### Медленная работа

**Проблема**: Rate limiting замедляет бота

**Решение**:
1. Используйте `sliding_window` стратегию
2. Увеличьте `redis_interval`
3. Настройте connection pooling
4. Используйте Redis на SSD

## 🔒 Безопасность

### Рекомендации

1. **Используйте аутентификацию Redis**:
   ```bash
   REDIS_URL=redis://username:password@localhost:6379/0
   ```

2. **Ограничьте доступ к Redis**:
   ```bash
   # В redis.conf
   bind 127.0.0.1
   requirepass your_strong_password
   ```

3. **Используйте TLS**:
   ```bash
   REDIS_URL=rediss://localhost:6380/0
   ```

4. **Регулярно очищайте старые ключи**:
   ```bash
   # Автоматическая очистка через Redis EXPIRE
   ```

## 📈 Производительность

### Бенчмарки

- **Sliding Window**: ~1000 RPS на одном ядре
- **Fixed Window**: ~2000 RPS на одном ядре  
- **Token Bucket**: ~1500 RPS на одном ядре

### Оптимизация

1. **Используйте pipeline** для множественных операций
2. **Настройте connection pooling**
3. **Используйте Redis Cluster** для высокой нагрузки
4. **Мониторьте производительность** через Redis INFO

## 🔄 Миграция

### С локального на Redis rate limiting

1. **Установите Redis** (см. раздел установки)
2. **Обновите конфигурацию**:
   ```bash
   REDIS_ENABLED=true
   REDIS_URL=redis://localhost:6379/0
   ```
3. **Перезапустите бота**
4. **Проверьте работу** через тесты

### Обратная миграция

1. **Отключите Redis**:
   ```bash
   REDIS_ENABLED=false
   ```
2. **Перезапустите бота**
3. **Бот автоматически переключится** на локальный rate limiting

## 📚 Дополнительные ресурсы

- [Redis Documentation](https://redis.io/documentation)
- [aioredis Documentation](https://aioredis.readthedocs.io/)
- [Rate Limiting Patterns](https://redis.io/docs/manual/patterns/distributed-locks/)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/distributed-locks/)

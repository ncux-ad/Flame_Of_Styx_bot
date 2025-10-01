# 🔧 Dependency Injection в AntiSpam Bot

**📅 Обновлено: Январь 2025**

---

## 🎯 **ПРИНЦИПЫ DI В ПРОЕКТЕ**

### **Встроенный DI Aiogram 3.x - ЛУЧШИЙ ВЫБОР!**

**✅ Почему встроенный DI Aiogram:**
- **Оптимизирован для Aiogram** - работает с middleware
- **Лучшая производительность** - нет overhead от внешних библиотек
- **Простота использования** - меньше кода
- **Стабильность** - нет циклических зависимостей
- **Типизация** - отличная поддержка type hints

**❌ Почему НЕ внешние библиотеки (punq, dependency-injector):**
- **Сложность** - больше boilerplate кода
- **Overhead** - дополнительные зависимости
- **Циклические зависимости** - проблемы с punq
- **Несовместимость** - не оптимизированы для Aiogram

---

## 🏗️ **АРХИТЕКТУРА DI**

### **DIMiddleware - Основной DI контейнер**

```python
class DIMiddleware(BaseMiddleware):
    """Middleware для Dependency Injection в Aiogram 3.x."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    async def __call__(self, handler, event, data):
        # Создаем сервисы один раз и кэшируем
        if not self._initialized:
            await self._initialize_services(data)
            self._initialized = True
        
        # Добавляем все сервисы в data для хендлеров
        data.update(self._services)
        return await handler(event, data)
```

### **Инициализация сервисов**

```python
async def _initialize_services(self, data):
    """Создает все сервисы один раз и кэширует их."""
    bot = data.get('bot')
    db_session = data.get('db_session')
    config = data.get('config')
    
    # Создаем базовые сервисы
    moderation_service = ModerationService(bot, db_session)
    bot_service = BotService(bot, db_session)
    channel_service = ChannelService(bot, db_session, config.native_channel_ids_list)
    
    # Создаем сервисы с зависимостями
    admin_service = AdminService(
        moderation_service=moderation_service,
        bot_service=bot_service,
        channel_service=channel_service,
        # ... остальные зависимости
    )
    
    # Кэшируем все сервисы
    self._services = {
        'moderation_service': moderation_service,
        'bot_service': bot_service,
        'admin_service': admin_service,
        # ... все остальные сервисы
    }
```

---

## 🚀 **ИСПОЛЬЗОВАНИЕ В ХЕНДЛЕРАХ**

### **Автоматическая инжекция**

```python
@router.message(Command("sync_bans"))
async def handle_sync_bans_command(
    message: Message,
    moderation_service: ModerationService,  # Автоматически инжектируется!
    channel_service: ChannelService,        # Автоматически инжектируется!
    admin_id: int,                          # Из конфига
) -> None:
    """Синхронизация банов с Telegram."""
    # Сервисы уже готовы к использованию!
    banned_users = await moderation_service.get_banned_users()
    channels = await channel_service.get_all_channels()
```

### **Порядок параметров**

**Правильный порядок:**
1. **Event объекты** (Message, CallbackQuery, etc.)
2. **Сервисы** (ModerationService, BotService, etc.)
3. **Конфигурация** (admin_id, config, etc.)

```python
# ✅ ПРАВИЛЬНО
async def handle_command(
    message: Message,                    # 1. Event
    moderation_service: ModerationService,  # 2. Сервис
    admin_id: int,                      # 3. Конфиг
) -> None:
    pass

# ❌ НЕПРАВИЛЬНО
async def handle_command(
    admin_id: int,                      # Конфиг перед сервисом
    message: Message,                   # Event после конфига
    moderation_service: ModerationService,
) -> None:
    pass
```

---

## 📋 **СПИСОК ВСЕХ СЕРВИСОВ**

### **Базовые сервисы**
- **`moderation_service`** - ModerationService
- **`bot_service`** - BotService  
- **`channel_service`** - ChannelService
- **`profile_service`** - ProfileService
- **`help_service`** - HelpService
- **`limits_service`** - LimitsService

### **Админские сервисы**
- **`admin_service`** - AdminService
- **`bots_admin_service`** - BotsAdminService
- **`channels_admin_service`** - ChannelsAdminService
- **`suspicious_admin_service`** - SuspiciousAdminService
- **`callbacks_service`** - CallbacksService

### **Специальные сервисы**
- **`link_service`** - LinkService

---

## 🔄 **ЖИЗНЕННЫЙ ЦИКЛ СЕРВИСОВ**

### **1. Инициализация (один раз)**
```python
# При первом сообщении DIMiddleware создает все сервисы
moderation_service = ModerationService(bot, db_session)
bot_service = BotService(bot, db_session)
# ... все остальные сервисы
```

### **2. Кэширование**
```python
# Сервисы сохраняются в self._services
self._services = {
    'moderation_service': moderation_service,
    'bot_service': bot_service,
    # ... все сервисы
}
```

### **3. Инжекция в хендлеры**
```python
# Aiogram автоматически передает сервисы в хендлеры
data.update(self._services)  # Добавляем в data
return await handler(event, data)  # Передаем в хендлер
```

### **4. Использование в хендлерах**
```python
# Хендлеры получают сервисы как параметры
async def handle_command(message: Message, moderation_service: ModerationService):
    # Сервис готов к использованию!
    await moderation_service.ban_user(...)
```

---

## ⚙️ **КОНФИГУРАЦИЯ**

### **Регистрация в bot.py**

```python
# Регистрируем DIMiddleware
dp.message.middleware(DIMiddleware())

# Для других типов апдейтов
dp.callback_query.middleware(DIMiddleware())
dp.my_chat_member.middleware(DIMiddleware())
# ... остальные типы
```

### **Порядок middleware**

```python
# Правильный порядок регистрации
dp.message.middleware(ValidationMiddleware())      # 1. Валидация
dp.message.middleware(LoggingMiddleware())         # 2. Логирование
dp.message.middleware(RateLimitMiddleware())       # 3. Rate limiting
dp.message.middleware(DIMiddleware())              # 4. DI (ПОСЛЕ rate limiting!)
dp.message.middleware(SuspiciousProfileMiddleware()) # 5. Анализ профилей
```

---

## 🐛 **ОТЛАДКА DI**

### **Проверка инициализации**

```python
# В DIMiddleware
logger.info(f"DI services initialized: {list(self._services.keys())}")
```

### **Проверка в хендлерах**

```python
async def handle_command(message: Message, **kwargs):
    logger.info(f"Available services: {list(kwargs.keys())}")
    # Должны быть: moderation_service, bot_service, etc.
```

### **Частые ошибки**

**1. Сервис не найден:**
```
KeyError: 'moderation_service' not found
```
**Решение:** Проверить, что сервис создается в `_initialize_services()`

**2. Неправильный порядок параметров:**
```
TypeError: got multiple values for argument 'message'
```
**Решение:** Следовать правильному порядку: Event → Services → Config

**3. Циклические зависимости:**
```
ImportError: cannot import name 'X' from 'Y'
```
**Решение:** Использовать встроенный DI, избегать внешних библиотек

---

## 📚 **ЛУЧШИЕ ПРАКТИКИ**

### **✅ ДЕЛАТЬ**

1. **Использовать встроенный DI Aiogram** - лучший выбор!
2. **Следовать порядку параметров** - Event → Services → Config
3. **Кэшировать сервисы** - создавать один раз
4. **Логировать инициализацию** - для отладки
5. **Проверять зависимости** - в конструкторах сервисов

### **❌ НЕ ДЕЛАТЬ**

1. **Использовать внешние DI библиотеки** - punq, dependency-injector
2. **Создавать сервисы в хендлерах** - только через DI
3. **Игнорировать порядок параметров** - приводит к ошибкам
4. **Создавать циклические зависимости** - между сервисами
5. **Забывать про типизацию** - всегда указывать типы

---

## 🎯 **ЗАКЛЮЧЕНИЕ**

**Встроенный DI Aiogram 3.x - это ЛУЧШИЙ выбор для Aiogram проектов!**

**Преимущества:**
- ✅ Оптимизирован для Aiogram
- ✅ Лучшая производительность  
- ✅ Простота использования
- ✅ Стабильность
- ✅ Отличная типизация

**Используйте DIMiddleware для всех Aiogram проектов!** 🚀

---

**📝 Примечание:** Этот документ является частью архитектуры AntiSpam Bot и должен обновляться при изменениях в DI системе.

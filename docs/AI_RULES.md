# 🤖 Правила для AI ассистента

**📅 Обновлено: Январь 2025**

---

## 🎯 **ОСНОВНЫЕ ПРИНЦИПЫ**

### **1. Встроенный DI Aiogram 3.x - ЛУЧШИЙ ВЫБОР!**

**✅ ВСЕГДА используйте встроенный DI Aiogram:**
- **DIMiddleware** - основной DI контейнер
- **Автоматическая инжекция** сервисов в хендлеры
- **Кэширование сервисов** - создание один раз
- **Оптимизирован для Aiogram** - лучшая производительность

**❌ НИКОГДА не используйте внешние DI библиотеки:**
- **punq** - НЕ ИСПОЛЬЗУЙТЕ!
- **dependency-injector** - НЕ ИСПОЛЬЗУЙТЕ!
- **Любые другие DI библиотеки** - НЕ ИСПОЛЬЗУЙТЕ!

### **2. Архитектура проекта**

**Структура DI:**
```
app/middlewares/
├── di_middleware.py          # ОСНОВНОЙ DI контейнер
└── dependency_injection.py   # Алиас для совместимости (deprecated)
```

**Порядок middleware:**
```python
dp.message.middleware(ValidationMiddleware())      # 1. Валидация
dp.message.middleware(LoggingMiddleware())         # 2. Логирование  
dp.message.middleware(RateLimitMiddleware())       # 3. Rate limiting
dp.message.middleware(DIMiddleware())              # 4. DI (ПОСЛЕ rate limiting!)
dp.message.middleware(SuspiciousProfileMiddleware()) # 5. Анализ профилей
```

---

## 🔧 **ПРАВИЛА РАЗРАБОТКИ**

### **1. Хендлеры**

**✅ ПРАВИЛЬНО - Встроенный DI:**
```python
@router.message(Command("sync_bans"))
async def handle_sync_bans_command(
    message: Message,                    # 1. Event объект
    moderation_service: ModerationService,  # 2. Сервис (автоматически инжектируется!)
    channel_service: ChannelService,        # 3. Сервис (автоматически инжектируется!)
    admin_id: int,                      # 4. Конфигурация
) -> None:
    """Синхронизация банов с Telegram."""
    # Сервисы уже готовы к использованию!
    banned_users = await moderation_service.get_banned_users()
    channels = await channel_service.get_all_channels()
```

**❌ НЕПРАВИЛЬНО - Внешние DI библиотеки:**
```python
# НЕ ДЕЛАЙТЕ ТАК!
from punq import Container
from dependency_injector import containers

# НЕ ДЕЛАЙТЕ ТАК!
@router.message(Command("sync_bans"))
async def handle_sync_bans_command(message: Message, **kwargs):
    service = kwargs.get("service")  # Устаревший подход
```

### **2. Создание сервисов**

**✅ ПРАВИЛЬНО - В DIMiddleware:**
```python
async def _initialize_services(self, data):
    """Создает все сервисы один раз и кэширует их."""
    bot = data.get('bot')
    db_session = data.get('db_session')
    config = data.get('config')
    
    # Создаем базовые сервисы
    moderation_service = ModerationService(bot, db_session)
    bot_service = BotService(bot, db_session)
    
    # Создаем сервисы с зависимостями
    admin_service = AdminService(
        moderation_service=moderation_service,
        bot_service=bot_service,
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

**❌ НЕПРАВИЛЬНО - В хендлерах:**
```python
# НЕ ДЕЛАЙТЕ ТАК!
async def handle_command(message: Message):
    # Создание сервисов в хендлере - НЕПРАВИЛЬНО!
    moderation_service = ModerationService(bot, db_session)
```

### **3. Порядок параметров в хендлерах**

**✅ ПРАВИЛЬНЫЙ порядок:**
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

## 🚫 **ЧТО НЕ ДЕЛАТЬ**

### **1. Внешние DI библиотеки**
```python
# ❌ НИКОГДА НЕ ИСПОЛЬЗУЙТЕ!
from punq import Container
from dependency_injector import containers
from dependency_injector.wiring import Provide, inject
```

### **2. Создание сервисов в хендлерах**
```python
# ❌ НИКОГДА НЕ ДЕЛАЙТЕ!
async def handle_command(message: Message):
    # Создание сервисов в хендлере - НЕПРАВИЛЬНО!
    service = ModerationService(bot, db_session)
```

### **3. Использование container.resolve() в хендлерах**
```python
# ❌ НИКОГДА НЕ ДЕЛАЙТЕ!
async def handle_command(message: Message):
    # Прямое обращение к контейнеру - НЕПРАВИЛЬНО!
    service = container.container.resolve(ModerationService)
```

### **4. Неправильный порядок параметров**
```python
# ❌ НИКОГДА НЕ ДЕЛАЙТЕ!
async def handle_command(
    admin_id: int,                      # Конфиг перед сервисом
    message: Message,                   # Event после конфига
    moderation_service: ModerationService,
) -> None:
    pass
```

---

## ✅ **ЧТО ДЕЛАТЬ**

### **1. Использовать встроенный DI Aiogram**
```python
# ✅ ВСЕГДА ДЕЛАЙТЕ ТАК!
@router.message(Command("command"))
async def handle_command(
    message: Message,
    moderation_service: ModerationService,  # Автоматически инжектируется!
    admin_id: int,
) -> None:
    # Сервис уже готов к использованию!
    await moderation_service.ban_user(...)
```

### **2. Создавать сервисы в DIMiddleware**
```python
# ✅ ВСЕГДА ДЕЛАЙТЕ ТАК!
async def _initialize_services(self, data):
    # Создаем все сервисы один раз
    moderation_service = ModerationService(bot, db_session)
    # Кэшируем их
    self._services = {'moderation_service': moderation_service}
```

### **3. Следовать правильному порядку параметров**
```python
# ✅ ВСЕГДА ДЕЛАЙТЕ ТАК!
async def handle_command(
    message: Message,                    # 1. Event
    moderation_service: ModerationService,  # 2. Сервис
    admin_id: int,                      # 3. Конфиг
) -> None:
    pass
```

---

## 🎯 **ЗАКЛЮЧЕНИЕ**

**Встроенный DI Aiogram 3.x - это ЛУЧШИЙ выбор для Aiogram проектов!**

**Помните:**
- ✅ Используйте DIMiddleware
- ✅ Сервисы инжектируются автоматически
- ✅ Следуйте правильному порядку параметров
- ❌ НЕ используйте внешние DI библиотеки
- ❌ НЕ создавайте сервисы в хендлерах

**Следуйте этим правилам для стабильной и производительной архитектуры!** 🚀

---

**📝 Примечание:** Эти правила являются частью архитектуры AntiSpam Bot и должны соблюдаться при любых изменениях в коде.

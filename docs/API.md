# 📚 API Документация

## 🏗️ Архитектура API

### Основные компоненты

- **Handlers** - Обработчики команд и сообщений
- **Services** - Бизнес-логика и работа с данными
- **Models** - Модели базы данных
- **Middlewares** - Промежуточное ПО для DI и логирования
- **Filters** - Фильтры для обработчиков

## 🎯 Handlers API

### Admin Handlers

#### `handle_start_command`
**Описание:** Обработчик команды `/start` для администраторов

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

**Пример:**
```python
@admin_router.message(Command("start"))
async def handle_start_command(message: Message, data: dict = None) -> None:
    """Handle /start command for admins."""
    # Implementation
```

#### `handle_status_command`
**Описание:** Обработчик команды `/status` - показывает статистику бота

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

#### `handle_channels_command`
**Описание:** Обработчик команды `/channels` - управление каналами

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

#### `handle_bots_command`
**Описание:** Обработчик команды `/bots` - управление ботами

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

#### `handle_suspicious_command`
**Описание:** Обработчик команды `/suspicious` - подозрительные профили

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

#### `handle_help_command`
**Описание:** Обработчик команды `/help` - справка

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

#### `handle_logs_command`
**Описание:** Обработчик команды `/logs` - просмотр логов

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

### User Handlers

#### `handle_user_message`
**Описание:** Обработчик пользовательских сообщений с антиспам-логикой

**Параметры:**
- `message: Message` - Сообщение от пользователя
- `data: dict = None` - Данные от middleware

**Возвращает:** `None`

**Логика:**
1. Проверка на бота
2. Проверка на канал
3. Анализ ссылок
4. Анализ профиля пользователя

#### `handle_new_member`
**Описание:** Обработчик новых участников чата

**Параметры:**
- `update: ChatMemberUpdated` - Обновление участника

**Возвращает:** `None`

#### `handle_chat_member_update`
**Описание:** Обработчик обновлений участников чата

**Параметры:**
- `update: ChatMemberUpdated` - Обновление участника

**Возвращает:** `None`

## 🔧 Services API

### BotService

#### `get_whitelisted_bots()`
**Описание:** Получить список ботов в whitelist

**Возвращает:** `List[Bot]`

#### `get_all_bots()`
**Описание:** Получить всех ботов

**Возвращает:** `List[Bot]`

#### `add_bot_to_whitelist(bot_id: int)`
**Описание:** Добавить бота в whitelist

**Параметры:**
- `bot_id: int` - ID бота

**Возвращает:** `bool`

#### `remove_bot_from_whitelist(bot_id: int)`
**Описание:** Удалить бота из whitelist

**Параметры:**
- `bot_id: int` - ID бота

**Возвращает:** `bool`

### ChannelService

#### `get_allowed_channels()`
**Описание:** Получить разрешенные каналы

**Возвращает:** `List[Channel]`

#### `get_blocked_channels()`
**Описание:** Получить заблокированные каналы

**Возвращает:** `List[Channel]`

#### `get_pending_channels()`
**Описание:** Получить каналы, ожидающие решения

**Возвращает:** `List[Channel]`

#### `allow_channel(channel_id: int)`
**Описание:** Разрешить канал

**Параметры:**
- `channel_id: int` - ID канала

**Возвращает:** `bool`

#### `block_channel(channel_id: int)`
**Описание:** Заблокировать канал

**Параметры:**
- `channel_id: int` - ID канала

**Возвращает:** `bool`

### LinkService

#### `check_message_for_bot_links(message: Message)`
**Описание:** Проверить сообщение на наличие ссылок на ботов

**Параметры:**
- `message: Message` - Сообщение для проверки

**Возвращает:** `List[str]` - Список найденных ссылок

#### `handle_bot_link_detection(message: Message, links: List[str])`
**Описание:** Обработать обнаружение ссылок на ботов

**Параметры:**
- `message: Message` - Сообщение
- `links: List[str]` - Список ссылок

**Возвращает:** `None`

### ProfileService

#### `analyze_user_profile(user: User, admin_id: int)`
**Описание:** Анализировать профиль пользователя на подозрительность

**Параметры:**
- `user: User` - Пользователь
- `admin_id: int` - ID администратора

**Возвращает:** `Optional[SuspiciousProfile]`

#### `get_suspicious_profiles()`
**Описание:** Получить список подозрительных профилей

**Возвращает:** `List[SuspiciousProfile]`

### ModerationService

#### `moderate_message(message: Message)`
**Описание:** Модерировать сообщение

**Параметры:**
- `message: Message` - Сообщение

**Возвращает:** `bool` - True если сообщение прошло модерацию

#### `ban_user(user_id: int, reason: str)`
**Описание:** Забанить пользователя

**Параметры:**
- `user_id: int` - ID пользователя
- `reason: str` - Причина бана

**Возвращает:** `bool`

## 🗄️ Models API

### Bot Model

```python
class Bot(Base):
    __tablename__ = 'bots'

    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    is_whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Channel Model

```python
class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, unique=True, nullable=False)
    title = Column(String(255))
    username = Column(String(255))
    status = Column(Enum(ChannelStatus), default=ChannelStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Profile Model

```python
class SuspiciousProfile(Base):
    __tablename__ = 'suspicious_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    reason = Column(String(1000))
    admin_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 🔌 Middlewares API

### DependencyInjectionMiddleware

#### `__call__(handler, event, data)`
**Описание:** Внедрение зависимостей в обработчики

**Параметры:**
- `handler: Callable` - Обработчик
- `event: Message | CallbackQuery` - Событие
- `data: Dict[str, Any]` - Данные

**Возвращает:** `Any`

**Внедряемые сервисы:**
- `link_service: LinkService`
- `profile_service: ProfileService`
- `channel_service: ChannelService`
- `bot_service: BotService`
- `moderation_service: ModerationService`
- `db_session: Session`

### LoggingMiddleware

#### `__call__(handler, event, data)`
**Описание:** Логирование событий

**Параметры:**
- `handler: Callable` - Обработчик
- `event: Message | CallbackQuery` - Событие
- `data: Dict[str, Any]` - Данные

**Возвращает:** `Any`

### RateLimitMiddleware

#### `__init__(limit: int, interval: int)`
**Описание:** Инициализация middleware ограничения частоты

**Параметры:**
- `limit: int` - Лимит запросов
- `interval: int` - Интервал в секундах

#### `__call__(handler, event, data)`
**Описание:** Проверка лимита запросов

**Параметры:**
- `handler: Callable` - Обработчик
- `event: Message | CallbackQuery` - Событие
- `data: Dict[str, Any]` - Данные

**Возвращает:** `Any`

## 🔍 Filters API

### IsAdminFilter

#### `__call__(obj: Union[Message, CallbackQuery])`
**Описание:** Проверка, является ли пользователь администратором

**Параметры:**
- `obj: Union[Message, CallbackQuery]` - Объект для проверки

**Возвращает:** `bool`

### IsAdminOrSilentFilter

#### `__call__(obj: Union[Message, CallbackQuery])`
**Описание:** Проверка администратора с тихим игнорированием

**Параметры:**
- `obj: Union[Message, CallbackQuery]` - Объект для проверки

**Возвращает:** `bool`

## ⚙️ Configuration API

### Settings Class

#### `bot_token: str`
**Описание:** Токен Telegram бота

#### `admin_ids: str`
**Описание:** ID администраторов через запятую

#### `admin_ids_list: List[int]`
**Описание:** Список ID администраторов

#### `db_path: str`
**Описание:** Путь к файлу базы данных

#### `validate_token(cls, v)`
**Описание:** Валидация токена бота

#### `validate_admin_ids(cls, v)`
**Описание:** Валидация ID администраторов

#### `validate_db_path(cls, v)`
**Описание:** Валидация пути к базе данных

## 🧪 Примеры использования

### Создание нового обработчика

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("test"))
async def handle_test_command(message: Message, data: dict = None) -> None:
    """Test command handler."""
    # Получение сервиса из DI
    service = data.get('service_name') if data else None

    if not service:
        await message.answer("❌ Сервис недоступен")
        return

    # Использование сервиса
    result = await service.some_method()
    await message.answer(f"Результат: {result}")
```

### Создание нового сервиса

```python
from typing import Optional
from app.database import get_db

class NewService:
    def __init__(self, bot, db_session):
        self.bot = bot
        self.db_session = db_session

    async def process_data(self, data: dict) -> Optional[dict]:
        """Process some data."""
        try:
            # Логика обработки
            result = {"processed": True, "data": data}
            return result
        except Exception as e:
            print(f"Error processing data: {e}")
            return None
```

### Регистрация в DI

```python
# В app/middlewares/dependency_injection.py
from app.services.new_service import NewService

# В методе __call__:
services = {
    'link_service': LinkService(bot, db_session),
    'profile_service': ProfileService(bot, db_session),
    'channel_service': ChannelService(bot, db_session),
    'bot_service': BotService(bot, db_session),
    'moderation_service': ModerationService(bot, db_session),
    'new_service': NewService(bot, db_session),  # Новый сервис
    'db_session': db_session
}
```

## 📞 Поддержка

Если у вас возникли вопросы по API:

1. Изучите [руководство по DI](DI_BEST_PRACTICES.md)
2. Проверьте [руководство для разработчиков](DEVELOPMENT.md)
3. Создайте Issue в репозитории
4. Обратитесь к исходному коду для примеров

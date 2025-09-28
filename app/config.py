import logging
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from app.constants import SUSPICION_THRESHOLD
from app.utils.security import validate_admin_id, validate_bot_token, validate_test_bot_token

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    bot_token: str = ""
    admin_ids: str = "366490333,439304619"
    db_path: str = "db.sqlite3"

    # Native channels (каналы, где бот является администратором)
    native_channel_ids: str = ""

    # Лимиты системы
    max_messages_per_minute: int = Field(default=10, ge=1, le=100, description="Максимум сообщений в минуту")
    max_links_per_message: int = Field(default=3, ge=1, le=10, description="Максимум ссылок в сообщении")
    ban_duration_hours: int = Field(default=24, ge=1, le=168, description="Длительность бана в часах")
    suspicion_threshold: float = Field(default=SUSPICION_THRESHOLD, ge=0.0, le=1.0, description="Порог подозрительности")

    # Настройки антиспама
    check_media_without_caption: bool = True  # Проверять медиа без подписи
    allow_gifs_without_caption: bool = True  # Разрешать GIF без подписи
    allow_photos_without_caption: bool = True  # Разрешать фото без подписи
    allow_videos_without_caption: bool = True  # Разрешать видео без подписи
    max_document_size_suspicious: int = 50000  # Максимальный размер документа для подозрения (байты)
    
    # Настройки уведомлений
    show_limits_on_startup: bool = True  # Показывать лимиты при запуске бота
    
    # Настройки Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="URL подключения к Redis")
    redis_enabled: bool = Field(default=False, description="Включить Redis rate limiting")
    
    # Настройки Redis Rate Limiting
    redis_user_limit: int = Field(default=10, ge=1, le=100, description="Лимит сообщений для пользователей")
    redis_admin_limit: int = Field(default=100, ge=10, le=1000, description="Лимит сообщений для администраторов")
    redis_interval: int = Field(default=60, ge=10, le=3600, description="Интервал rate limiting в секундах")
    redis_strategy: str = Field(default="sliding_window", description="Стратегия rate limiting")
    redis_block_duration: int = Field(default=300, ge=60, le=3600, description="Длительность блокировки в секундах")

    @field_validator("db_path")
    @classmethod
    def validate_db_path(cls, v: str) -> str:
        """Validate database path."""
        if not v:
            raise ValueError("DB_PATH не может быть пустым")

        # Проверяем, что путь заканчивается на .sqlite3 или .db
        if not (v.endswith(".sqlite3") or v.endswith(".db")):
            raise ValueError("DB_PATH должен заканчиваться на .sqlite3 или .db")

        return v

    @field_validator("bot_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Валидация токена бота с использованием утилит безопасности."""
        if not v:
            raise ValueError("BOT_TOKEN не может быть пустым")

        # Проверяем обычный токен или тестовый токен
        if not (validate_bot_token(v) or validate_test_bot_token(v)):
            raise ValueError("BOT_TOKEN некорректный формат")

        logger.info("Токен бота успешно валидирован")
        return v

    @field_validator("admin_ids")
    @classmethod
    def validate_admin_ids(cls, v: str) -> str:
        """Валидация ID администраторов с использованием утилит безопасности."""
        if not v:
            raise ValueError("ADMIN_IDS не может быть пустым")

        if isinstance(v, str):
            # Разбиваем по запятым и убираем пробелы
            ids = [x.strip() for x in v.split(",") if x.strip()]
            if not ids:
                raise ValueError("ADMIN_IDS должен содержать хотя бы один ID")

            for admin_id in ids:
                if not validate_admin_id(admin_id):
                    raise ValueError(f"Некорректный ID администратора: {admin_id}")

        logger.info(f"Валидировано {len(ids)} ID администраторов")
        return v

    @property
    def admin_ids_list(self) -> List[int]:
        """Parse admin_ids string to list of integers."""
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip().isdigit()]

    @property
    def native_channel_ids_list(self) -> List[int]:
        """Parse native_channel_ids string to list of integers."""
        if isinstance(self.native_channel_ids, str) and self.native_channel_ids.strip():
            result = []
            for x in self.native_channel_ids.split(","):
                x = x.strip()
                if x and (x.isdigit() or (x.startswith("-") and x[1:].isdigit())):
                    result.append(int(x))
            return result
        return []

    @field_validator("redis_strategy")
    @classmethod
    def validate_redis_strategy(cls, v: str) -> str:
        """Валидация стратегии Redis rate limiting."""
        valid_strategies = ["fixed_window", "sliding_window", "token_bucket"]
        if v not in valid_strategies:
            raise ValueError(f"redis_strategy должен быть одним из: {', '.join(valid_strategies)}")
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Валидация URL Redis."""
        if not v:
            raise ValueError("redis_url не может быть пустым")
        
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("redis_url должен начинаться с redis:// или rediss://")
        
        return v

    model_config = {"env_file": ".env", "extra": "ignore"}  # Игнорировать дополнительные поля


def load_config() -> Settings:
    """Load and validate configuration."""
    try:
        config = Settings()
        # Дополнительная проверка после создания объекта
        _validate_config(config)
        return config
    except Exception as e:
        raise ValueError(f"Ошибка конфигурации: {e}")


def _validate_config(config: Settings) -> None:
    """Additional validation after config creation."""
    # Проверяем, что admin_ids_list не пустой (только для production)
    if not config.admin_ids_list and not config.bot_token.startswith("test_token"):
        raise ValueError("Список админов пуст. Проверьте ADMIN_IDS.")
    
    # Для тестового режима добавляем тестового админа
    if config.bot_token.startswith("test_token") and not config.admin_ids_list:
        config.admin_ids_list = [123456789]

    # Проверяем, что все admin ID валидны
    for admin_id in config.admin_ids_list:
        if admin_id <= 0:
            raise ValueError(f"ADMIN_ID {admin_id} должен быть положительным числом")

    # Проверяем, что токен не является placeholder (только для production)
    if config.bot_token == "your_telegram_bot_token_here" and not config.bot_token.startswith("test_token"):
        raise ValueError("BOT_TOKEN не настроен. Замените 'your_telegram_bot_token_here' на реальный токен.")

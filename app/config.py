from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    admin_ids: str = "366490333,439304619"
    db_path: str = "db.sqlite3"

    @validator("db_path")
    def validate_db_path(cls, v):
        """Validate database path."""
        if not v:
            raise ValueError("DB_PATH не может быть пустым")

        # Проверяем, что путь заканчивается на .sqlite3 или .db
        if not (v.endswith('.sqlite3') or v.endswith('.db')):
            raise ValueError("DB_PATH должен заканчиваться на .sqlite3 или .db")

        return v

    @validator("bot_token")
    def validate_token(cls, v):
        if not v or len(v) < 20:
            raise ValueError("BOT_TOKEN некорректный или отсутствует")
        # Проверяем формат токена (должен быть в формате 123456789:ABC...)
        if ':' not in v or len(v.split(':')[0]) < 8:
            raise ValueError("BOT_TOKEN должен быть в формате 'bot_id:token'")
        return v

    @validator("admin_ids")
    def validate_admin_ids(cls, v):
        """Validate admin_ids format."""
        if not v:
            raise ValueError("ADMIN_IDS не может быть пустым")

        if isinstance(v, str):
            # Проверяем, что все ID являются числами
            ids = [x.strip() for x in v.split(",") if x.strip()]
            if not ids:
                raise ValueError("ADMIN_IDS должен содержать хотя бы один ID")

            for admin_id in ids:
                if not admin_id.isdigit():
                    raise ValueError(f"ADMIN_ID '{admin_id}' должен быть числом")
                if len(admin_id) < 6:  # Telegram ID обычно длиннее 6 цифр
                    raise ValueError(f"ADMIN_ID '{admin_id}' слишком короткий")

        return v

    @property
    def admin_ids_list(self) -> List[int]:
        """Parse admin_ids string to list of integers."""
        if isinstance(self.admin_ids, str):
            return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip().isdigit()]
        return []

    class Config:
        env_file = ".env"

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
    # Проверяем, что admin_ids_list не пустой
    if not config.admin_ids_list:
        raise ValueError("Список админов пуст. Проверьте ADMIN_IDS.")

    # Проверяем, что все admin ID валидны
    for admin_id in config.admin_ids_list:
        if admin_id <= 0:
            raise ValueError(f"ADMIN_ID {admin_id} должен быть положительным числом")

    # Проверяем, что токен не является placeholder
    if config.bot_token == "your_telegram_bot_token_here":
        raise ValueError("BOT_TOKEN не настроен. Замените 'your_telegram_bot_token_here' на реальный токен.")

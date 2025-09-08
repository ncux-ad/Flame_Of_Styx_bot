from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List

class Settings(BaseSettings):
    bot_token: str
    admin_ids: List[int] = []
    db_path: str = "db.sqlite3"

    @validator("bot_token")
    def validate_token(cls, v):
        if not v or len(v) < 20:
            raise ValueError("BOT_TOKEN некорректный или отсутствует")
        return v

    @validator("admin_ids", pre=True)
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x) for x in v.split(",") if x.strip().isdigit()]
        return v

    class Config:
        env_file = ".env"

def load_config() -> Settings:
    return Settings()

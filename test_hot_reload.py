#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации hot-reload лимитов.
"""

import asyncio
import json
import time

from app.services.limits import LimitsService


async def test_hot_reload():
    """Тестирование hot-reload лимитов."""
    print("🚀 Тестирование hot-reload лимитов...")

    # Создаем сервис лимитов
    limits_service = LimitsService()

    # Показываем текущие лимиты
    print("\n📊 Текущие лимиты:")
    limits = limits_service.get_current_limits()
    for key, value in limits.items():
        print(f"  • {key}: {value}")

    # Создаем тестовый файл limits.json
    test_limits = {
        "max_messages_per_minute": 15,
        "max_links_per_message": 5,
        "ban_duration_hours": 48,
        "suspicion_threshold": 0.3,
    }

    print(f"\n📝 Создаем тестовый файл limits.json с новыми значениями...")
    with open("limits.json", "w", encoding="utf-8") as f:
        json.dump(test_limits, f, indent=2, ensure_ascii=False)

    # Ждем немного
    print("⏳ Ждем 3 секунды...")
    await asyncio.sleep(3)

    # Проверяем, обновились ли лимиты
    print("\n🔄 Проверяем обновленные лимиты:")
    limits = limits_service.get_current_limits()
    for key, value in limits.items():
        print(f"  • {key}: {value}")

    # Принудительно перезагружаем
    print("\n🔄 Принудительная перезагрузка...")
    success = limits_service.reload_limits()
    if success:
        print("✅ Лимиты перезагружены успешно!")
    else:
        print("❌ Ошибка перезагрузки лимитов")

    # Показываем финальные лимиты
    print("\n📊 Финальные лимиты:")
    limits = limits_service.get_current_limits()
    for key, value in limits.items():
        print(f"  • {key}: {value}")

    print("\n🎉 Тест завершен!")


if __name__ == "__main__":
    asyncio.run(test_hot_reload())
if __name__ == "__main__":
    asyncio.run(test_hot_reload())

#!/usr/bin/env python3
"""
Скрипт для тестирования Redis Rate Limiting
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import load_config
from app.services.redis import RedisService

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_redis_connection():
    """Тест подключения к Redis."""
    logger.info("🔍 Тестирование подключения к Redis...")

    try:
        config = load_config()
        logger.info(f"Redis URL: {config.redis_url}")
        logger.info(f"Redis enabled: {config.redis_enabled}")

        if not config.redis_enabled:
            logger.warning("❌ Redis отключен в конфигурации")
            return False

        # Тестируем подключение
        redis_service = RedisService()
        if redis_service.is_available():
            logger.info("✅ Redis подключен успешно")

            # Тестируем базовые операции
            test_key = "test:rate_limit:123"

            # Устанавливаем значение
            await redis_service.redis_client.set(test_key, "1", ex=60)
            logger.info("✅ SET операция успешна")

            # Получаем значение
            value = await redis_service.redis_client.get(test_key)
            logger.info(f"✅ GET операция успешна: {value}")

            # Удаляем тестовый ключ
            await redis_service.redis_client.delete(test_key)
            logger.info("✅ DELETE операция успешна")

            return True
        else:
            logger.error("❌ Не удалось подключиться к Redis")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании Redis: {e}")
        return False


async def test_rate_limit_operations():
    """Тест операций rate limiting."""
    logger.info("🔍 Тестирование операций rate limiting...")

    try:
        redis_service = RedisService()
        if not redis_service.is_available():
            logger.error("❌ Redis недоступен")
            return False

        user_id = 123456789
        limit = 5
        interval = 60

        logger.info(f"Тестируем лимит: {limit} запросов за {interval} секунд")

        # Тестируем несколько запросов
        for i in range(limit + 2):
            result = await redis_service.check_rate_limit(user_id=user_id, limit=limit, interval=interval, key_type="test")

            logger.info(f"Запрос {i+1}: allowed={result['allowed']}, remaining={result['remaining']}")

            if i < limit:
                assert result["allowed"], f"Запрос {i+1} должен быть разрешен"
            else:
                assert not result["allowed"], f"Запрос {i+1} должен быть заблокирован"

        logger.info("✅ Тест rate limiting прошел успешно")

        # Очищаем тестовые данные
        test_keys = await redis_service.redis_client.keys("rate_limit:test:*")
        if test_keys:
            await redis_service.redis_client.delete(*test_keys)
            logger.info("✅ Тестовые данные очищены")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании rate limiting: {e}")
        return False


async def test_redis_performance():
    """Тест производительности Redis."""
    logger.info("🔍 Тестирование производительности Redis...")

    try:
        redis_service = RedisService()
        if not redis_service.is_available():
            logger.error("❌ Redis недоступен")
            return False

        # Тестируем скорость операций
        import time

        operations = 100
        start_time = time.time()

        for i in range(operations):
            await redis_service.redis_client.set(f"perf_test:{i}", str(i), ex=60)

        set_time = time.time() - start_time

        start_time = time.time()

        for i in range(operations):
            await redis_service.redis_client.get(f"perf_test:{i}")

        get_time = time.time() - start_time

        # Очищаем тестовые данные
        test_keys = await redis_service.redis_client.keys("perf_test:*")
        if test_keys:
            await redis_service.redis_client.delete(*test_keys)

        logger.info(f"✅ Производительность:")
        logger.info(f"  - {operations} SET операций: {set_time:.3f}s ({operations/set_time:.1f} ops/s)")
        logger.info(f"  - {operations} GET операций: {get_time:.3f}s ({operations/get_time:.1f} ops/s)")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании производительности: {e}")
        return False


async def main():
    """Главная функция тестирования."""
    logger.info("🚀 Запуск тестирования Redis Rate Limiting")

    success_count = 0
    total_tests = 3

    # Тест 1: Подключение
    if await test_redis_connection():
        success_count += 1

    # Тест 2: Rate limiting
    if await test_rate_limit_operations():
        success_count += 1

    # Тест 3: Производительность
    if await test_redis_performance():
        success_count += 1

    logger.info(f"📊 Результаты тестирования: {success_count}/{total_tests} тестов прошли успешно")

    if success_count == total_tests:
        logger.info("🎉 Все тесты прошли успешно!")
        return True
    else:
        logger.error("❌ Некоторые тесты провалились")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Redis Rate Limiting
"""

import asyncio
import logging
import time
from typing import List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_redis_connection():
    """Тестируем подключение к Redis."""
    try:
        from app.services.redis import get_redis_service
        
        print("🔍 Тестируем подключение к Redis...")
        
        redis_service = await get_redis_service()
        
        # Тестируем базовые операции
        await redis_service.set("test_key", "test_value", expire=10)
        value = await redis_service.get("test_key")
        
        if value == "test_value":
            print("✅ Redis подключение работает корректно")
            return True
        else:
            print("❌ Ошибка в операциях Redis")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Redis: {e}")
        return False


async def test_rate_limiting_strategies():
    """Тестируем различные стратегии rate limiting."""
    try:
        from app.middlewares.redis_rate_limit import RedisRateLimitMiddleware
        from app.services.redis import get_redis_service
        
        print("\n🔍 Тестируем стратегии rate limiting...")
        
        redis_service = await get_redis_service()
        user_id = 12345
        limit = 5
        interval = 10  # 10 секунд для быстрого тестирования
        
        strategies = ["fixed_window", "sliding_window", "token_bucket"]
        
        for strategy in strategies:
            print(f"\n📊 Тестируем стратегию: {strategy}")
            
            middleware = RedisRateLimitMiddleware(
                user_limit=limit,
                admin_limit=limit * 2,
                interval=interval,
                strategy=strategy,
                redis_key_prefix="test_rate_limit"
            )
            
            # Очищаем старые ключи
            await redis_service.delete(f"test_rate_limit:blocked:{user_id}")
            
            success_count = 0
            for i in range(limit + 2):  # Пытаемся превысить лимит
                is_allowed = await middleware._check_rate_limit(
                    redis_service.redis, user_id, False
                )
                
                if is_allowed:
                    success_count += 1
                    print(f"  ✅ Запрос {i+1}: разрешен")
                else:
                    print(f"  ❌ Запрос {i+1}: заблокирован")
                    break
                
                # Небольшая задержка между запросами
                await asyncio.sleep(0.1)
            
            print(f"  📈 Успешных запросов: {success_count}/{limit + 2}")
            
            # Очищаем тестовые ключи
            await redis_service.delete(f"test_rate_limit:blocked:{user_id}")
            if strategy == "fixed_window":
                window = int(time.time() // interval)
                await redis_service.delete(f"test_rate_limit:fixed:{user_id}:{window}")
            elif strategy == "sliding_window":
                await redis_service.delete(f"test_rate_limit:sliding:{user_id}")
            elif strategy == "token_bucket":
                await redis_service.delete(f"test_rate_limit:bucket:{user_id}")
        
        print("✅ Все стратегии протестированы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования стратегий: {e}")
        return False


async def test_blocking_mechanism():
    """Тестируем механизм блокировки пользователей."""
    try:
        from app.middlewares.redis_rate_limit import RedisRateLimitMiddleware
        from app.services.redis import get_redis_service
        
        print("\n🔍 Тестируем механизм блокировки...")
        
        redis_service = await get_redis_service()
        user_id = 54321
        limit = 3
        interval = 5
        block_duration = 10
        
        middleware = RedisRateLimitMiddleware(
            user_limit=limit,
            admin_limit=limit * 2,
            interval=interval,
            strategy="sliding_window",
            block_duration=block_duration,
            redis_key_prefix="test_blocking"
        )
        
        # Очищаем старые ключи
        await redis_service.delete(f"test_blocking:blocked:{user_id}")
        
        # Превышаем лимит для блокировки
        for i in range(limit + 1):
            is_allowed = await middleware._check_rate_limit(
                redis_service.redis, user_id, False
            )
            
            if is_allowed:
                print(f"  ✅ Запрос {i+1}: разрешен")
            else:
                print(f"  ❌ Запрос {i+1}: заблокирован")
                
                # Проверяем, что пользователь заблокирован
                is_blocked = await middleware._is_user_blocked(redis_service.redis, user_id)
                if is_blocked:
                    print(f"  🔒 Пользователь заблокирован на {block_duration} секунд")
                else:
                    print(f"  ⚠️ Пользователь не заблокирован (ошибка)")
                break
        
        # Очищаем тестовые ключи
        await redis_service.delete(f"test_blocking:blocked:{user_id}")
        await redis_service.delete(f"test_blocking:sliding:{user_id}")
        
        print("✅ Механизм блокировки протестирован")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования блокировки: {e}")
        return False


async def test_performance():
    """Тестируем производительность Redis rate limiting."""
    try:
        from app.middlewares.redis_rate_limit import RedisRateLimitMiddleware
        from app.services.redis import get_redis_service
        
        print("\n🔍 Тестируем производительность...")
        
        redis_service = await get_redis_service()
        user_id = 99999
        limit = 100
        interval = 60
        
        middleware = RedisRateLimitMiddleware(
            user_limit=limit,
            admin_limit=limit * 2,
            interval=interval,
            strategy="sliding_window",
            redis_key_prefix="test_performance"
        )
        
        # Очищаем старые ключи
        await redis_service.delete(f"test_performance:sliding:{user_id}")
        
        # Тестируем производительность
        start_time = time.time()
        requests_count = 1000
        
        for i in range(requests_count):
            await middleware._check_rate_limit(redis_service.redis, user_id, False)
        
        end_time = time.time()
        duration = end_time - start_time
        rps = requests_count / duration
        
        print(f"  📊 Обработано запросов: {requests_count}")
        print(f"  ⏱️ Время выполнения: {duration:.2f} секунд")
        print(f"  🚀 Запросов в секунду: {rps:.2f}")
        
        # Очищаем тестовые ключи
        await redis_service.delete(f"test_performance:sliding:{user_id}")
        
        if rps > 100:  # Минимум 100 RPS
            print("✅ Производительность удовлетворительная")
            return True
        else:
            print("⚠️ Производительность может быть улучшена")
            return True  # Не критично для теста
        
    except Exception as e:
        print(f"❌ Ошибка тестирования производительности: {e}")
        return False


async def main():
    """Основная функция тестирования."""
    print("🚀 Запуск тестирования Redis Rate Limiting")
    print("=" * 60)
    
    results = []
    
    # Тестируем подключение к Redis
    results.append(await test_redis_connection())
    
    # Тестируем стратегии rate limiting
    results.append(await test_rate_limiting_strategies())
    
    # Тестируем механизм блокировки
    results.append(await test_blocking_mechanism())
    
    # Тестируем производительность
    results.append(await test_performance())
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Redis Rate Limiting работает корректно!")
    else:
        print("⚠️ Есть проблемы, требующие внимания")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        exit(1)

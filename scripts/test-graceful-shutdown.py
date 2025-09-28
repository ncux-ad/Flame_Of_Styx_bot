#!/usr/bin/env python3
"""
Тестовый скрипт для проверки graceful shutdown
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.graceful_shutdown import GracefulShutdown
from aiogram import Bot, Dispatcher

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestBot:
    """Тестовый бот для проверки graceful shutdown."""
    
    def __init__(self):
        self.is_running = False
        self.shutdown_manager = None
        
    async def start(self):
        """Запускает тестовый бот."""
        logger.info("Starting test bot...")
        
        # Создаем фиктивный бот и dispatcher (без инициализации токена)
        class MockBot:
            async def send_message(self, chat_id, text):
                logger.info(f"Mock send_message to {chat_id}: {text}")
            
            @property
            def session(self):
                return self
            
            async def close(self):
                logger.info("Mock session closed")
        
        bot = MockBot()
        dp = Dispatcher()
        
        # Создаем graceful shutdown manager
        self.shutdown_manager = GracefulShutdown(bot, dp, [123456789])  # Фиктивный admin_id
        
        # Добавляем тестовый callback
        self.shutdown_manager.add_shutdown_callback(self.test_shutdown_callback)
        
        # Настраиваем обработчики сигналов
        self.shutdown_manager.setup_signal_handlers()
        
        self.is_running = True
        logger.info("Test bot started successfully")
        
        # Симулируем работу бота
        try:
            while self.is_running and not self.shutdown_manager.is_shutdown_requested():
                logger.info("Bot is running... (Press Ctrl+C to test graceful shutdown)")
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, testing graceful shutdown...")
            await self.shutdown_manager.graceful_shutdown()
            
    async def test_shutdown_callback(self):
        """Тестовый callback для shutdown."""
        logger.info("Test shutdown callback executed")
        await asyncio.sleep(2)  # Симулируем работу
        logger.info("Test shutdown callback completed")
        
    def stop(self):
        """Останавливает тестовый бот."""
        self.is_running = False
        logger.info("Test bot stopped")


async def main():
    """Основная функция теста."""
    test_bot = TestBot()
    
    try:
        await test_bot.start()
    except Exception as e:
        logger.error(f"Error in test bot: {e}")
    finally:
        test_bot.stop()


if __name__ == "__main__":
    print("🧪 Тестирование graceful shutdown")
    print("📝 Нажмите Ctrl+C для тестирования graceful shutdown")
    print("⏰ Timeout: 30 секунд")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
    
    print("-" * 50)
    print("✅ Тест graceful shutdown завершен")

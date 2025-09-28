#!/usr/bin/env python3
"""
Простой тест graceful shutdown без зависимостей от aiogram
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleGracefulShutdown:
    """Простая реализация graceful shutdown для тестирования."""
    
    def __init__(self, admin_ids):
        self.admin_ids = admin_ids
        self.shutdown_callbacks = []
        self.is_shutting_down = False
        self._shutdown_event = asyncio.Event()
        
    def add_shutdown_callback(self, callback):
        """Добавляет callback для выполнения при shutdown."""
        self.shutdown_callbacks.append(callback)
        
    async def notify_admins(self, message):
        """Уведомляет админов о состоянии бота."""
        for admin_id in self.admin_ids:
            logger.info(f"Notification to admin {admin_id}: {message}")
                
    async def startup_notification(self):
        """Уведомление о запуске бота."""
        message = "🤖 AntiSpam Bot запущен - тестовый режим"
        await self.notify_admins(message)
        logger.info("Startup notification sent to admins")
        
    async def shutdown_notification(self):
        """Уведомление об остановке бота."""
        message = "🛑 AntiSpam Bot остановлен - тестовый режим"
        await self.notify_admins(message)
        logger.info("Shutdown notification sent to admins")
        
    async def execute_shutdown_callbacks(self):
        """Выполняет все зарегистрированные shutdown callbacks."""
        logger.info(f"Executing {len(self.shutdown_callbacks)} shutdown callbacks")
        
        for callback in self.shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                logger.info(f"Shutdown callback executed: {callback.__name__}")
            except Exception as e:
                logger.error(f"Error in shutdown callback {callback.__name__}: {e}")
                
    async def graceful_shutdown(self, timeout=30):
        """Выполняет graceful shutdown с timeout."""
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return
            
        self.is_shutting_down = True
        logger.info("Starting graceful shutdown...")
        
        try:
            # Уведомляем админов
            await self.shutdown_notification()
            
            # Выполняем shutdown callbacks
            await self.execute_shutdown_callbacks()
            
            logger.info("Graceful shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
        finally:
            self._shutdown_event.set()
            
    def setup_signal_handlers(self):
        """Настраивает обработчики сигналов."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.graceful_shutdown())
            
        # Обрабатываем SIGTERM и SIGINT
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Для Windows добавляем SIGBREAK
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, signal_handler)
            
        logger.info("Signal handlers configured for graceful shutdown")
        
    async def wait_for_shutdown(self):
        """Ожидает завершения shutdown."""
        await self._shutdown_event.wait()
        
    def is_shutdown_requested(self):
        """Проверяет, запрошен ли shutdown."""
        return self.is_shutting_down


class TestBot:
    """Тестовый бот для проверки graceful shutdown."""
    
    def __init__(self):
        self.is_running = False
        self.shutdown_manager = None
        
    async def start(self):
        """Запускает тестовый бот."""
        logger.info("Starting test bot...")
        
        # Создаем graceful shutdown manager
        self.shutdown_manager = SimpleGracefulShutdown([123456789])  # Фиктивный admin_id
        
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
    print("🧪 Тестирование graceful shutdown (простая версия)")
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

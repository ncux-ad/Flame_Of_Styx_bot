"""
Graceful shutdown utilities для корректного завершения работы бота
"""

import asyncio
import logging
import signal
import sys
from typing import Optional, List, Callable, Any

from aiogram import Bot, Dispatcher

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Менеджер graceful shutdown для бота."""
    
    def __init__(self, bot: Bot, dispatcher: Dispatcher, admin_ids: List[int]):
        self.bot = bot
        self.dispatcher = dispatcher
        self.admin_ids = admin_ids
        self.shutdown_callbacks: List[Callable] = []
        self.is_shutting_down = False
        self._shutdown_event = asyncio.Event()
        
    def add_shutdown_callback(self, callback: Callable) -> None:
        """Добавляет callback для выполнения при shutdown."""
        self.shutdown_callbacks.append(callback)
        
    async def notify_admins(self, message: str) -> None:
        """Уведомляет админов о состоянии бота."""
        for admin_id in self.admin_ids:
            try:
                await self.bot.send_message(admin_id, message)
                logger.info(f"Notification sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
                
    async def startup_notification(self) -> None:
        """Уведомление о запуске бота."""
        message = (
            "BOT <b>AntiSpam Bot запущен</b>\n\n"
            "OK Бот готов к работе\n"
            "SHIELD Антиспам активен\n"
            "STATS Мониторинг включен"
        )
        await self.notify_admins(message)
        logger.info("Startup notification sent to admins")
        
    async def shutdown_notification(self) -> None:
        """Уведомление об остановке бота."""
        message = (
            "STOP <b>AntiSpam Bot остановлен</b>\n\n"
            "WARNING Бот завершает работу\n"
            "RELOAD Graceful shutdown в процессе\n"
            "TIME Ожидайте завершения..."
        )
        await self.notify_admins(message)
        logger.info("Shutdown notification sent to admins")
        
    async def execute_shutdown_callbacks(self) -> None:
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
                
    async def graceful_shutdown(self, timeout: int = 30) -> None:
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
            
            # Останавливаем dispatcher (если polling запущен)
            logger.info("Stopping dispatcher...")
            try:
                if self.dispatcher._polling:
                    await self.dispatcher.stop_polling()
                else:
                    logger.info("Polling was not started, skipping stop_polling")
            except Exception as e:
                logger.warning(f"Error stopping polling: {e}")
            
            # Закрываем сессию бота
            logger.info("Closing bot session...")
            await self.bot.session.close()
            
            logger.info("Graceful shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
        finally:
            self._shutdown_event.set()
            
    def setup_signal_handlers(self) -> None:
        """Настраивает обработчики сигналов."""
        def signal_handler(signum: int, frame: Any) -> None:
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.graceful_shutdown())
            
        # Обрабатываем SIGTERM и SIGINT
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Для Windows добавляем SIGBREAK
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, signal_handler)
            
        logger.info("Signal handlers configured for graceful shutdown")
        
    async def wait_for_shutdown(self) -> None:
        """Ожидает завершения shutdown."""
        await self._shutdown_event.wait()
        
    def is_shutdown_requested(self) -> bool:
        """Проверяет, запрошен ли shutdown."""
        return self.is_shutting_down


async def create_graceful_shutdown(
    bot: Bot, 
    dispatcher: Dispatcher, 
    admin_ids: List[int]
) -> GracefulShutdown:
    """Создает и настраивает GracefulShutdown."""
    shutdown_manager = GracefulShutdown(bot, dispatcher, admin_ids)
    shutdown_manager.setup_signal_handlers()
    return shutdown_manager

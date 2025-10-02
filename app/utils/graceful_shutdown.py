"""
Graceful shutdown utilities для корректного завершения работы бота
"""

import asyncio
import logging
import signal
import sys
from typing import Any, Callable, List, Optional

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
        message = "🤖 <b>AntiSpam Bot запущен</b>\n\n" "✅ Бот готов к работе\n" "🛡️ Антиспам активен\n" "📊 Мониторинг включен"
        await self.notify_admins(message)
        logger.info("Startup notification sent to admins")

    async def shutdown_notification(self) -> None:
        """Уведомление об остановке бота."""
        message = (
            "🛑 <b>AntiSpam Bot остановлен</b>\n\n"
            "⚠️ Бот завершает работу\n"
            "🔄 Graceful shutdown в процессе\n"
            "⏰ Ожидайте завершения..."
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
                # Проверяем различные способы определения состояния polling
                polling_active = (
                    hasattr(self.dispatcher, "_polling")
                    and self.dispatcher._polling
                    or hasattr(self.dispatcher, "_running")
                    and self.dispatcher._running
                    or hasattr(self.dispatcher, "running")
                    and self.dispatcher.running
                )

                if polling_active:
                    await self.dispatcher.stop_polling()
                    logger.info("Polling stopped successfully")
                else:
                    logger.info("Polling was not started, skipping stop_polling")
            except Exception as e:
                logger.warning(f"Error stopping polling: {e}")

            # Закрываем сессию бота
            logger.info("Closing bot session...")
            await self.bot.session.close()

            # Закрываем соединения с базой данных
            logger.info("Closing database connections...")
            try:
                from app.database import engine

                if engine:
                    await engine.dispose()
                    logger.info("Database engine disposed successfully")
                else:
                    logger.warning("Database engine not found")
            except Exception as e:
                logger.error(f"Error disposing database engine: {e}")

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


async def create_graceful_shutdown(bot: Bot, dispatcher: Dispatcher, admin_ids: List[int]) -> GracefulShutdown:
    """Создает и настраивает GracefulShutdown."""
    shutdown_manager = GracefulShutdown(bot, dispatcher, admin_ids)
    shutdown_manager.setup_signal_handlers()
    return shutdown_manager

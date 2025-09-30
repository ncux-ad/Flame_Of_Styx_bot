"""
Сервис для мониторинга изменений в конфигурационных файлах.
Реализует hot-reload для limits.json и других настроек.
"""

import asyncio
import json
import logging
import subprocess
# import os  # Не используется
# import time  # Не используется
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Сервис для мониторинга изменений в конфигурационных файлах."""

    def __init__(self, config_file: str, on_change_callback: Optional[Callable] = None):
        self.config_file = Path(config_file)
        self.on_change_callback = on_change_callback
        self.last_modified = 0
        self.last_content = ""
        self.is_running = False
        self.watch_task: Optional[asyncio.Task] = None

    async def start_watching(self, interval: float = 1.0) -> None:
        """Запустить мониторинг файла."""
        if self.is_running:
            logger.warning("ConfigWatcher уже запущен")
            return

        self.is_running = True
        self.watch_task = asyncio.create_task(self._watch_loop(interval))
        logger.info(f"ConfigWatcher запущен для файла: {self.config_file}")

    async def stop_watching(self) -> None:
        """Остановить мониторинг файла."""
        if not self.is_running:
            return

        self.is_running = False
        if self.watch_task:
            self.watch_task.cancel()
            try:
                await self.watch_task
            except asyncio.CancelledError:
                pass
        logger.info("ConfigWatcher остановлен")

    async def _watch_loop(self, interval: float) -> None:
        """Основной цикл мониторинга."""
        while self.is_running:
            try:
                await self._check_file_changes()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в ConfigWatcher: {e}")
                await asyncio.sleep(interval)

    async def _check_file_changes(self) -> None:
        """Проверить изменения в файле."""
        if not self.config_file.exists():
            return

        try:
            # Проверяем время модификации
            current_modified = self.config_file.stat().st_mtime
            if current_modified <= self.last_modified:
                return

            # Читаем содержимое файла
            with open(self.config_file, "r", encoding="utf-8") as f:
                current_content = f.read()

            # Проверяем, изменилось ли содержимое
            if current_content == self.last_content:
                self.last_modified = current_modified
                return

            # Файл изменился
            logger.info(f"Обнаружены изменения в файле: {self.config_file}")

            # Обновляем кэш
            self.last_modified = current_modified
            self.last_content = current_content

            # Вызываем callback
            if self.on_change_callback:
                try:
                    await self.on_change_callback(self.config_file, current_content)
                except Exception as e:
                    logger.error(f"Ошибка в callback ConfigWatcher: {e}")

        except Exception as e:
            logger.error(f"Ошибка при проверке файла {self.config_file}: {e}")

    async def force_reload(self) -> bool:
        """Принудительно перезагрузить конфигурацию."""
        if not self.config_file.exists():
            return False

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                content = f.read()

            if self.on_change_callback:
                await self.on_change_callback(self.config_file, content)
                return True
        except Exception as e:
            logger.error(f"Ошибка при принудительной перезагрузке: {e}")

        return False


class LimitsHotReload:
    """Сервис для hot-reload лимитов системы."""

    def __init__(self, limits_service, bot, admin_ids: list):
        self.limits_service = limits_service
        self.bot = bot
        self.admin_ids = admin_ids
        self.watcher = ConfigWatcher("limits.json", self._on_limits_changed)
        self.show_limits_on_startup = True  # Показывать лимиты при запуске

    async def start(self) -> None:
        """Запустить hot-reload для лимитов."""
        await self.watcher.start_watching(interval=2.0)  # Проверяем каждые 2 секунды
        logger.info("Hot-reload для лимитов запущен")

    async def stop(self) -> None:
        """Остановить hot-reload для лимитов."""
        await self.watcher.stop_watching()
        logger.info("Hot-reload для лимитов остановлен")

    async def _on_limits_changed(self, file_path: Path, content: str) -> None:
        """Обработчик изменения файла лимитов."""
        try:
            # Парсим новый контент
            new_limits = json.loads(content)

            # Валидируем новые лимиты
            if not self._validate_limits(new_limits):
                logger.error("Новые лимиты не прошли валидацию")
                return

            # Обновляем лимиты в сервисе
            old_limits = self.limits_service.get_current_limits()

            # Обновляем каждый лимит
            for key, value in new_limits.items():
                self.limits_service.update_limit(key, value)

            # Уведомляем администраторов
            await self._notify_admins_about_reload(old_limits, new_limits)

            logger.info(f"Лимиты успешно обновлены: {new_limits}")

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в limits.json: {e}")
            await self._notify_admins_about_error(f"Ошибка в формате limits.json: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении лимитов: {e}")
            await self._notify_admins_about_error(f"Ошибка обновления лимитов: {e}")

    def _validate_limits(self, limits: Dict[str, Any]) -> bool:
        """Валидация новых лимитов."""
        required_keys = [
            "max_messages_per_minute",
            "max_links_per_message",
            "ban_duration_hours",
            "suspicion_threshold",
        ]

        # Проверяем наличие всех ключей
        if not all(key in limits for key in required_keys):
            logger.error("Отсутствуют обязательные ключи в limits.json")
            return False

        # Проверяем типы и значения
        try:
            if not isinstance(limits["max_messages_per_minute"], int) or limits["max_messages_per_minute"] <= 0:
                return False
            if not isinstance(limits["max_links_per_message"], int) or limits["max_links_per_message"] <= 0:
                return False
            if not isinstance(limits["ban_duration_hours"], int) or limits["ban_duration_hours"] <= 0:
                return False
            if not isinstance(limits["suspicion_threshold"], (int, float)) or not (0 <= limits["suspicion_threshold"] <= 1):
                return False
        except (TypeError, ValueError):
            return False

        return True

    async def _notify_admins_about_reload(self, old_limits: Dict, new_limits: Dict) -> None:
        """Уведомить администраторов об обновлении лимитов."""
        try:
            # Проверяем, это первый запуск или обновление
            is_first_start = not hasattr(self, '_first_notification_sent')
            
            if is_first_start:
                # Первый запуск - полное сообщение
                message = "🤖 <b>AntiSpam Bot запущен</b>\n\n"
                message += "✅ <b>Бот готов к работе</b>\n"
                message += "🛡️ <b>Антиспам активен</b>\n"
                message += "📊 <b>Мониторинг включен</b>\n\n"
                
                # Добавляем информацию о коммите
                try:
                    # Получаем абсолютный путь к проекту
                    import os
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    
                    # Логируем для отладки
                    logger.info(f"Trying to get git commit from directory: {project_root}")
                    
                    result = subprocess.run(
                        ["git", "rev-parse", "--short", "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=project_root
                    )
                    
                    logger.info(f"Git command result: returncode={result.returncode}, stdout='{result.stdout.strip()}', stderr='{result.stderr.strip()}'")
                    
                    if result.returncode == 0:
                        commit_hash = result.stdout.strip()
                        message += f"📝 <b>ID текущего коммита:</b> <code>{commit_hash}</code>\n\n"
                    else:
                        message += f"📝 <b>ID текущего коммита:</b> <code>неизвестно (git error: {result.stderr.strip()})</code>\n\n"
                except Exception as e:
                    logger.error(f"Error getting git commit: {e}")
                    message += f"📝 <b>ID текущего коммита:</b> <code>неизвестно (error: {str(e)})</code>\n\n"
                
                # Добавляем информацию о лимитах (если включено)
                if getattr(self, 'show_limits_on_startup', True):
                    message += "⚙️ <b>Текущие лимиты:</b>\n"
                    for key, value in new_limits.items():
                        message += f"• <b>{key}:</b> {value}\n"
                
                self._first_notification_sent = True
            else:
                # Обновление лимитов
                message = "🔄 <b>Лимиты обновлены автоматически!</b>\n\n"

                # Показываем изменения
                for key, new_value in new_limits.items():
                    old_value = old_limits.get(key, "неизвестно")
                    if old_value != new_value:
                        message += f"• <b>{key}:</b> {old_value} → {new_value}\n"
                    else:
                        message += f"• <b>{key}:</b> {new_value}\n"

                message += "\n✅ Изменения вступили в силу немедленно"

            # Отправляем уведомление всем администраторам
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=message)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")

        except Exception as e:
            logger.error(f"Ошибка при уведомлении администраторов: {e}")

    async def _notify_admins_about_error(self, error_message: str) -> None:
        """Уведомить администраторов об ошибке."""
        try:
            message = f"❌ <b>Ошибка обновления лимитов</b>\n\n{error_message}"

            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=message)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления об ошибке админу {admin_id}: {e}")

        except Exception as e:
            logger.error(f"Ошибка при уведомлении об ошибке: {e}")

    async def force_reload(self) -> bool:
        """Принудительно перезагрузить лимиты."""
        return await self.watcher.force_reload()

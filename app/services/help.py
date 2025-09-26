"""Help service for bot commands and features."""

from dataclasses import dataclass
from typing import Dict, List, Optional

# from app.auth.authorization import require_admin, safe_user_operation


@dataclass
class CommandInfo:
    """Information about a bot command."""

    command: str
    description: str
    usage: str = ""
    examples: Optional[List[str]] = None
    admin_only: bool = False


class HelpService:
    """Service for managing help information."""

    def __init__(self):
        self.commands = self._initialize_commands()

    def _initialize_commands(self) -> Dict[str, CommandInfo]:
        """Initialize all available commands."""
        return {
            # Основные команды
            "start": CommandInfo(
                command="/start",
                description="Главное меню и приветствие",
                usage="/start",
                examples=["/start"],
                admin_only=False,
            ),
            "help": CommandInfo(
                command="/help",
                description="Справка по всем командам",
                usage="/help [категория]",
                examples=["/help", "/help admin", "/help channels"],
                admin_only=False,
            ),
            # Статистика и мониторинг
            "status": CommandInfo(
                command="/status",
                description="Подробная статистика работы бота",
                usage="/status",
                examples=["/status"],
                admin_only=True,
            ),
            "settings": CommandInfo(
                command="/settings",
                description="Настройки бота и конфигурация",
                usage="/settings",
                examples=["/settings"],
                admin_only=True,
            ),
            # Управление каналами
            "channels": CommandInfo(
                command="/channels",
                description="Управление каналами и просмотр списка",
                usage="/channels",
                examples=["/channels"],
                admin_only=True,
            ),
            # Управление ботами
            "bots": CommandInfo(
                command="/bots",
                description="Управление ботами и whitelist",
                usage="/bots",
                examples=["/bots"],
                admin_only=True,
            ),
            # Подозрительные профили
            "suspicious": CommandInfo(
                command="/suspicious",
                description="Просмотр подозрительных профилей",
                usage="/suspicious",
                examples=["/suspicious"],
                admin_only=True,
            ),
            "reset_suspicious": CommandInfo(
                command="/reset_suspicious",
                description="Сброс статусов подозрительных профилей для тестирования",
                usage="/reset_suspicious",
                examples=["/reset_suspicious"],
                admin_only=True,
            ),
            "recalculate_suspicious": CommandInfo(
                command="/recalculate_suspicious",
                description="Пересчет подозрительных профилей с новыми весами",
                usage="/recalculate_suspicious",
                examples=["/recalculate_suspicious"],
                admin_only=True,
            ),
            "cleanup_duplicates": CommandInfo(
                command="/cleanup_duplicates",
                description="Удаление дублирующих подозрительных профилей",
                usage="/cleanup_duplicates",
                examples=["/cleanup_duplicates"],
                admin_only=True,
            ),
            # Модерация и баны
            "unban": CommandInfo(
                command="/unban",
                description="Разблокировать пользователя",
                usage="/unban [номер] или /unban &lt;user_id&gt; [chat_id]",
                examples=["/unban 1", "/unban 123456789", "/unban 123456789 -1001234567890"],
                admin_only=True,
            ),
            "banned": CommandInfo(
                command="/banned",
                description="Список заблокированных пользователей",
                usage="/banned",
                examples=["/banned"],
                admin_only=True,
            ),
            "ban_history": CommandInfo(
                command="/ban_history",
                description="История банов с ID чатов",
                usage="/ban_history",
                examples=["/ban_history"],
                admin_only=True,
            ),
            "sync_bans": CommandInfo(
                command="/sync_bans",
                description="Синхронизация банов с Telegram API",
                usage="/sync_bans [номер] или /sync_bans &lt;chat_id&gt;",
                examples=["/sync_bans 1", "/sync_bans -1001234567890"],
                admin_only=True,
            ),
            # Лимиты и настройки
            "setlimits": CommandInfo(
                command="/setlimits",
                description="Просмотр текущих лимитов системы",
                usage="/setlimits",
                examples=["/setlimits"],
                admin_only=True,
            ),
            "setlimit": CommandInfo(
                command="/setlimit",
                description="Изменение конкретного лимита",
                usage="/setlimit &lt;тип&gt; &lt;значение&gt;",
                examples=["/setlimit messages 15", "/setlimit threshold 0.3", "/setlimit ban 48"],
                admin_only=True,
            ),
            "reload_limits": CommandInfo(
                command="/reload_limits",
                description="Принудительная перезагрузка лимитов из файла",
                usage="/reload_limits",
                examples=["/reload_limits"],
                admin_only=True,
            ),
            # Логи и отладка
            "logs": CommandInfo(
                command="/logs",
                description="Просмотр логов системы",
                usage="/logs [уровень]",
                examples=["/logs", "/logs error", "/logs warning"],
                admin_only=True,
            ),
            # Инструкции
            "instructions": CommandInfo(
                command="/instructions",
                description="Инструкция по настройке бота для админов каналов",
                usage="/instructions",
                examples=["/instructions"],
                admin_only=True,
            ),
        }

    def get_main_help(self, is_admin: bool = False) -> str:
        """Get main help text - only for admins."""
        if not is_admin:
            return "❌ <b>Доступ запрещен</b>\n\nЭтот бот предназначен только для администраторов каналов."

        help_text = (
            "🤖 <b>AntiSpam Bot - Справка</b>\n\n"
            "Этот бот предназначен для автоматической модерации каналов и защиты от спама.\n\n"
        )

        help_text += self._get_admin_commands_structured()

        help_text += (
            "\n📖 <b>Дополнительная информация:</b>\n"
            "• Используйте /help [категория] для подробной справки\n"
            "• Все команды работают в личных сообщениях\n\n"
            "🔗 <b>Полезные ссылки:</b>\n"
            "• GitHub: https://github.com/ncux-ad/Flame_Of_Styx_bot\n"
            "• Документация: /help admin - полная справка\n"
            "• Поддержка: [@ncux-ad](https://github.com/ncux-ad)"
        )

        return help_text

    def get_category_help(self, category: str, user_id: Optional[int] = None) -> str:
        """Get help for specific category."""
        category = category.lower()

        # Simple admin check - assume user is admin if user_id is provided
        # This avoids dependency on config loading
        is_admin = user_id is not None and user_id > 0

        # Debug logging
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"get_category_help: category={category}, user_id={user_id}, is_admin={is_admin}")

        try:
            if category == "admin":
                if not is_admin:
                    return "❌ У вас нет прав администратора для просмотра этой категории."
                return self._get_admin_commands_detailed()

            elif category == "channels":
                return self._get_channels_help()

            elif category == "bots":
                return self._get_bots_help()

            elif category == "moderation":
                return self._get_moderation_help()

            elif category == "suspicious":
                if not is_admin:
                    return "❌ У вас нет прав администратора для просмотра этой категории."
                return self._get_suspicious_help()

            elif category == "bans":
                if not is_admin:
                    return "❌ У вас нет прав администратора для просмотра этой категории."
                return self._get_bans_help()

            elif category == "limits":
                if not is_admin:
                    return "❌ У вас нет прав администратора для просмотра этой категории."
                return self._get_limits_help()

            elif category == "logs":
                if not is_admin:
                    return "❌ У вас нет прав администратора для просмотра этой категории."
                return self._get_logs_help()

            elif category == "user":
                return self._get_user_commands_detailed()

            else:
                return (
                    "❓ <b>Доступные категории справки:</b>\n\n"
                    "• <b>admin</b> - команды администратора\n"
                    "• <b>channels</b> - управление каналами\n"
                    "• <b>bots</b> - управление ботами\n"
                    "• <b>moderation</b> - модерация\n"
                    "• <b>suspicious</b> - подозрительные профили\n"
                    "• <b>bans</b> - модерация и баны\n"
                    "• <b>limits</b> - лимиты и настройки\n"
                    "• <b>logs</b> - логи и отладка\n"
                    "• <b>user</b> - пользовательские команды\n\n"
                    "Используйте: /help [категория]"
                )
        except Exception as e:
            logger.error(f"Error in get_category_help for category {category}: {e}")
            return f"❌ Ошибка получения справки для категории '{category}': {str(e)}"

    def _get_admin_commands(self) -> str:
        """Get admin commands list."""
        commands_text = "👑 <b>Команды администратора:</b>\n"

        # Генерируем список команд динамически из self.commands
        for command_key, command_info in self.commands.items():
            if command_info.admin_only:
                commands_text += f"{command_info.command} - {command_info.description}\n"

        commands_text += "\n"
        return commands_text

    def _get_admin_commands_structured(self) -> str:
        """Get structured admin commands list."""
        commands_text = "👑 <b>Команды администратора:</b>\n\n"

        # Группируем команды по категориям
        categories = {
            "📊 Статистика и мониторинг": ["status", "settings"],
            "📺 Управление каналами": ["channels"],
            "🤖 Управление ботами": ["bots"],
            "🔍 Подозрительные профили": ["suspicious", "reset_suspicious", "recalculate_suspicious", "cleanup_duplicates"],
            "🚫 Модерация и баны": ["unban", "banned", "ban_history", "sync_bans"],
            "⚙️ Лимиты и настройки": ["setlimits", "setlimit", "reload_limits"],
            "📋 Логи и отладка": ["logs"],
        }

        for category_name, command_keys in categories.items():
            commands_text += f"{category_name}:\n"
            for command_key in command_keys:
                if command_key in self.commands:
                    command_info = self.commands[command_key]
                    commands_text += f"• {command_info.command} - {command_info.description}\n"
            commands_text += "\n"

        return commands_text

    def _get_user_commands(self) -> str:
        """Get user commands list."""
        return "👤 <b>Пользовательские команды:</b>\n" "/start - главное меню\n" "/help - справка по командам\n\n"

    def _get_admin_commands_detailed(self) -> str:
        """Get detailed admin commands help."""
        return (
            "👑 <b>Команды администратора</b>\n\n"
            "📊 <b>Статистика и мониторинг:</b>\n"
            "<b>/status</b> - Подробная статистика работы бота\n"
            "• Количество каналов и их статус\n"
            "• Количество ботов в whitelist\n"
            "• Статистика модерации и банов\n"
            "• Общий статус системы\n\n"
            "<b>/settings</b> - Настройки бота и конфигурация\n"
            "• Текущие настройки системы\n"
            "• Статус компонентов\n"
            "• Информация о конфигурации\n\n"
            "📺 <b>Управление каналами:</b>\n"
            "<b>/channels</b> - Управление каналами и просмотр списка\n"
            "• Просмотр всех каналов\n"
            "• Статус каналов (нативные/иностранные)\n"
            "• Количество участников\n"
            "• Username и ID каналов\n\n"
            "🤖 <b>Управление ботами:</b>\n"
            "<b>/bots</b> - Управление ботами и whitelist\n"
            "• Просмотр списка ботов\n"
            "• Статус ботов (whitelist/blacklist)\n"
            "• Управление разрешениями\n\n"
            "🔍 <b>Подозрительные профили:</b>\n"
            "<b>/suspicious</b> - Просмотр подозрительных профилей\n"
            "• Список всех подозрительных аккаунтов\n"
            "• Счет подозрительности\n"
            "• Обнаруженные паттерны\n"
            "• Статус проверки (ожидает/проверен)\n\n"
            "<b>/reset_suspicious</b> - Сброс статусов для тестирования\n"
            "• Сброс статуса 'проверено' на 'ожидает проверки'\n"
            "• Позволяет повторно протестировать профили\n"
            "• Полезно для тестирования системы\n\n"
            "<b>/recalculate_suspicious</b> - Пересчет с новыми весами\n"
            "• Применяет новые веса паттернов\n"
            "• Обновляет счет подозрительности\n"
            "• Используется после изменения алгоритма\n\n"
            "<b>/cleanup_duplicates</b> - Очистка дублирующих профилей\n"
            "• Удаляет дублирующие записи\n"
            "• Оставляет только самый свежий профиль\n"
            "• Исправляет ошибки в базе данных\n\n"
            "🚫 <b>Модерация и баны:</b>\n"
            "<b>/unban</b> - Разблокировать пользователя\n"
            "• /unban [номер] - по номеру из списка\n"
            "• /unban &lt;user_id&gt; [chat_id] - по ID\n"
            "• Показывает последних заблокированных для выбора\n\n"
            "<b>/banned</b> - Список заблокированных пользователей\n"
            "• Последние 10 заблокированных\n"
            "• Информация о пользователе и причине\n"
            "• ID чата где был забанен\n\n"
            "<b>/ban_history</b> - История банов с ID чатов\n"
            "• Последние 10 записей из истории\n"
            "• ID чатов для синхронизации\n"
            "• Статус банов (активен/неактивен)\n\n"
            "<b>/sync_bans</b> - Синхронизация банов с Telegram API\n"
            "• /sync_bans [номер] - по номеру из истории\n"
            "• /sync_bans &lt;chat_id&gt; - по ID чата\n"
            "• Синхронизирует баны с Telegram\n\n"
            "⚙️ <b>Лимиты и настройки:</b>\n"
            "<b>/setlimits</b> - Просмотр текущих лимитов\n"
            "• Все текущие лимиты системы\n"
            "• Значения по умолчанию\n\n"
            "<b>/setlimit</b> - Изменение конкретного лимита\n"
            "• /setlimit messages 15 - сообщений в минуту\n"
            "• /setlimit threshold 0.3 - порог подозрительности\n"
            "• /setlimit ban 48 - время блокировки в часах\n"
            "• /setlimit links 5 - ссылок в сообщении\n\n"
            "<b>/reload_limits</b> - Перезагрузка лимитов из файла\n"
            "• Принудительная перезагрузка\n"
            "• Применение изменений из файла\n"
            "• Показывает обновленные значения\n\n"
            "📋 <b>Логи и отладка:</b>\n"
            "<b>/logs</b> - Просмотр логов системы\n"
            "• /logs - все логи\n"
            "• /logs error - только ошибки\n"
            "• /logs warning - предупреждения и ошибки\n\n"
            "💡 <b>Полезные советы:</b>\n"
            "• Используйте /help [категория] для детальной справки\n"
            "• Все команды работают в личных сообщениях\n"
            "• Кнопки модерации работают в уведомлениях\n"
            "• Система автоматически уведомляет о подозрительной активности\n"
        )

    def _get_channels_help(self) -> str:
        """Get channels management help."""
        return (
            "📺 <b>Управление каналами</b>\n\n"
            "Бот автоматически отслеживает сообщения от каналов и уведомляет администраторов.\n\n"
            "<b>📊 /channels</b>\n"
            "Просмотр всех каналов с разделением на типы:\n"
            "• <b>✅ Нативные каналы</b> - каналы где бот является администратором\n"
            "• <b>🔍 Иностранные каналы</b> - каналы откуда приходят сообщения (бот не админ)\n"
            "• Показывает ID, username, количество участников\n"
            "• Статистика по типам каналов\n\n"
            "<b>🔔 Уведомления:</b>\n"
            "При получении сообщения от нового канала вы получите уведомление с кнопками:\n"
            "• ✅ <b>Разрешить</b> - добавить канал в whitelist\n"
            "• 🚫 <b>Заблокировать</b> - добавить канал в blacklist\n"
            "• 🗑 <b>Удалить сообщение</b> - удалить сообщение\n"
            "• 👁 <b>Просмотр</b> - посмотреть содержимое сообщения\n\n"
            "<b>🎯 Логика работы:</b>\n"
            "• <b>Нативные каналы</b> - бот может модератировать, более мягкие правила\n"
            "• <b>Иностранные каналы</b> - строгие правила антиспама\n"
            "• Автоматическое определение типа канала по правам бота\n"
            "• Сохранение информации о всех каналах в базе данных\n\n"
            "<b>⚙️ Настройки:</b>\n"
            "• Автоматическое разрешение известных каналов\n"
            "• Фильтрация по ключевым словам\n"
            "• Настройка уведомлений"
        )

    def _get_bots_help(self) -> str:
        """Get bots management help."""
        return (
            "🤖 <b>Управление ботами</b>\n\n"
            "Бот автоматически блокирует других ботов, если они не находятся в whitelist.\n\n"
            "<b>🛡️ Защита от ботов:</b>\n"
            "• Автоматическое обнаружение ботов\n"
            "• Блокировка неизвестных ботов\n"
            "• Уведомления о новых ботах\n\n"
            "<b>📋 Whitelist ботов:</b>\n"
            "• Просмотр списка разрешенных ботов\n"
            "• Добавление ботов в whitelist\n"
            "• Удаление ботов из whitelist\n"
            "• Массовое управление\n\n"
            "<b>📊 Статистика:</b>\n"
            "• Общее количество ботов\n"
            "• Боты в whitelist\n"
            "• Заблокированные боты\n"
            "• Активность ботов\n\n"
            "<b>⚙️ Настройки:</b>\n"
            "• Автоматическое добавление в whitelist\n"
            "• Фильтрация по типу бота\n"
            "• Настройка уведомлений"
        )

    def _get_moderation_help(self) -> str:
        """Get moderation help."""
        return (
            "🛡️ <b>Система модерации</b>\n\n"
            "Бот автоматически анализирует сообщения и профили пользователей.\n\n"
            "<b>🔍 Анализ сообщений:</b>\n"
            "• Проверка ссылок на вредоносные сайты\n"
            "• Обнаружение спама и рекламы\n"
            "• Анализ текста на подозрительные паттерны\n"
            "• Проверка медиафайлов\n\n"
            "<b>👤 Анализ профилей:</b>\n"
            "• Проверка возраста аккаунта\n"
            "• Анализ активности пользователя\n"
            "• Обнаружение подозрительных паттернов\n"
            "• Проверка аватара и описания\n\n"
            "<b>⚡ Автоматические действия:</b>\n"
            "• Удаление подозрительных сообщений\n"
            "• Временная блокировка пользователей\n"
            "• Уведомления администраторов\n"
            "• Логирование всех действий\n\n"
            "<b>📊 Статистика модерации:</b>\n"
            "• Количество заблокированных сообщений\n"
            "• Статистика по типам нарушений\n"
            "• Эффективность фильтров\n"
            "• Отчеты по периодам"
        )

    def _get_user_commands_detailed(self) -> str:
        """Get detailed user commands help."""
        return (
            "👤 <b>Пользовательские команды</b>\n\n"
            "<b>🚀 /start</b>\n"
            "Запуск бота и главное меню:\n"
            "• Приветственное сообщение\n"
            "• Список доступных команд\n"
            "• Информация о боте\n\n"
            "<b>❓ /help</b>\n"
            "Справка по командам:\n"
            "• /help - общая справка\n"
            "• /help [категория] - справка по категории\n"
            "• Доступные категории: admin, channels, bots, moderation, suspicious, bans, limits\n\n"
            "<b>ℹ️ Дополнительная информация:</b>\n"
            "• Бот работает в фоновом режиме\n"
            "• Все команды работают в личных сообщениях\n"
            "• Для получения прав администратора обратитесь к разработчику"
        )

    def _get_suspicious_help(self) -> str:
        """Get suspicious profiles help."""
        return (
            "🔍 <b>Подозрительные профили</b>\n\n"
            "Система автоматически анализирует профили пользователей и обнаруживает подозрительные паттерны.\n\n"
            "<b>📊 /suspicious</b>\n"
            "Просмотр всех подозрительных профилей:\n"
            "• Список пользователей с высоким счетом подозрительности\n"
            "• Обнаруженные паттерны (короткое имя, нет username, bot-подобные имена)\n"
            "• Статус проверки (ожидает/проверен/подтвержден)\n"
            "• Связанные каналы и их информация\n\n"
            "<b>🔄 /reset_suspicious</b>\n"
            "Сброс статусов для тестирования:\n"
            "• Сбрасывает все статусы 'проверено' на 'ожидает проверки'\n"
            "• Позволяет повторно протестировать систему\n"
            "• Полезно для отладки и тестирования\n\n"
            "<b>📊 /recalculate_suspicious</b>\n"
            "Пересчет с новыми весами:\n"
            "• Применяет обновленные веса паттернов\n"
            "• Пересчитывает счет подозрительности\n"
            "• Используется после изменения алгоритма анализа\n\n"
            "<b>🧹 /cleanup_duplicates</b>\n"
            "Очистка дублирующих профилей:\n"
            "• Удаляет дублирующие записи для одного пользователя\n"
            "• Оставляет только самый свежий профиль\n"
            "• Исправляет ошибки в базе данных\n\n"
            "<b>🎯 Кнопки модерации:</b>\n"
            "При обнаружении подозрительного профиля админ получает уведомление с кнопками:\n"
            "• 🚫 <b>Забанить</b> - заблокировать пользователя\n"
            "• 👀 <b>Наблюдать</b> - добавить в список наблюдения\n"
            "• ✅ <b>Разрешить</b> - пометить как ложное срабатывание\n\n"
            "<b>📈 Алгоритм анализа:</b>\n"
            "• Проверка длины имени и фамилии\n"
            "• Наличие username и его паттерны\n"
            "• Bot-подобные имена и username\n"
            "• Связанные каналы и их активность\n"
            "• Общий счет подозрительности (0.0 - 1.0)\n"
            "• Порог срабатывания: 0.2"
        )

    def _get_bans_help(self) -> str:
        """Get bans and moderation help."""
        return (
            "🚫 <b>Модерация и баны</b>\n\n"
            "Система управления банами и модерацией пользователей.\n\n"
            "<b>🔓 /unban</b>\n"
            "Разблокировать пользователя:\n"
            "• /unban [номер] - по номеру из списка последних банов\n"
            "• /unban &lt;user_id&gt; [chat_id] - по ID пользователя и чата\n"
            "• Показывает последних 5 заблокированных для выбора\n"
            "• Поддерживает разблокировку в конкретном чате\n\n"
            "<b>📋 /banned</b>\n"
            "Список заблокированных пользователей:\n"
            "• Последние 10 заблокированных пользователей\n"
            "• Информация о пользователе (имя, username, ID)\n"
            "• Причина блокировки\n"
            "• ID чата где был забанен\n"
            "• Дата блокировки\n\n"
            "<b>📊 /ban_history</b>\n"
            "История банов с ID чатов:\n"
            "• Последние 10 записей из истории банов\n"
            "• ID чатов для синхронизации с Telegram\n"
            "• Статус банов (активен/неактивен)\n"
            "• Информация о чатах\n\n"
            "<b>🔄 /sync_bans</b>\n"
            "Синхронизация банов с Telegram API:\n"
            "• /sync_bans [номер] - по номеру из истории\n"
            "• /sync_bans &lt;chat_id&gt; - по ID чата\n"
            "• Синхронизирует локальные баны с Telegram\n"
            "• Показывает результат синхронизации\n\n"
            "<b>⚡ Автоматические действия:</b>\n"
            "• Удаление подозрительных сообщений\n"
            "• Временная блокировка пользователей\n"
            "• Уведомления администраторов\n"
            "• Логирование всех действий модерации\n\n"
            "<b>📈 Статистика модерации:</b>\n"
            "• Количество заблокированных сообщений\n"
            "• Статистика по типам нарушений\n"
            "• Эффективность фильтров\n"
            "• Отчеты по периодам"
        )

    def _get_limits_help(self) -> str:
        """Get limits and settings help."""
        return (
            "⚙️ <b>Лимиты и настройки</b>\n\n"
            "Управление лимитами системы и настройками бота.\n\n"
            "<b>📊 /setlimits</b>\n"
            "Просмотр текущих лимитов:\n"
            "• Все текущие лимиты системы\n"
            "• Значения по умолчанию\n"
            "• Статус лимитов\n\n"
            "<b>🔧 /setlimit</b>\n"
            "Изменение конкретного лимита:\n"
            "• /setlimit messages 15 - максимум сообщений в минуту\n"
            "• /setlimit threshold 0.3 - порог подозрительности\n"
            "• /setlimit ban 48 - время блокировки в часах\n"
            "• /setlimit links 5 - максимум ссылок в сообщении\n"
            "• Изменения применяются немедленно\n\n"
            "<b>🔄 /reload_limits</b>\n"
            "Перезагрузка лимитов из файла:\n"
            "• Принудительная перезагрузка из файла limits.json\n"
            "• Применение изменений из файла\n"
            "• Показывает обновленные значения\n"
            "• Полезно при изменении конфигурации\n\n"
            "<b>📋 Доступные типы лимитов:</b>\n"
            "• <b>messages</b> - максимум сообщений в минуту\n"
            "• <b>links</b> - максимум ссылок в сообщении\n"
            "• <b>ban</b> - время блокировки в часах\n"
            "• <b>threshold</b> - порог подозрительности (0.0-1.0)\n\n"
            "<b>💡 Полезные советы:</b>\n"
            "• Изменения применяются немедленно благодаря hot-reload\n"
            "• Используйте /setlimits для проверки текущих значений\n"
            "• Порог подозрительности влияет на обнаружение подозрительных профилей\n"
            "• Лимиты сообщений помогают предотвратить спам"
        )

    def _get_logs_help(self) -> str:
        """Get logs and debugging help."""
        return (
            "📋 <b>Логи и отладка</b>\n\n"
            "Система логирования и отладки для мониторинга работы бота.\n\n"
            "<b>📊 /logs</b>\n"
            "Просмотр логов системы:\n"
            "• <b>/logs</b> - все логи за последний час (последние 30 записей)\n"
            "• <b>/logs error</b> - только ошибки (ERROR, CRITICAL)\n"
            "• <b>/logs warning</b> - предупреждения и ошибки (WARNING, ERROR, CRITICAL)\n"
            "• <b>/logs all</b> - все логи (аналогично /logs)\n\n"
            "<b>🔍 Уровни логов:</b>\n"
            "• <b>error</b> - только критические ошибки\n"
            "• <b>warning</b> - предупреждения и ошибки\n"
            "• <b>all</b> - все логи (по умолчанию)\n\n"
            "<b>📈 Источники логов:</b>\n"
            "• <b>journalctl</b> - системные логи systemd (основной источник)\n"
            "• <b>Файлы логов</b> - резервный источник если journalctl недоступен\n"
            "• <b>Пути к файлам:</b>\n"
            "  - /var/log/antispam-bot.log\n"
            "  - logs/antispam-bot.log\n"
            "  - antispam-bot.log\n\n"
            "<b>⚙️ Настройки логирования:</b>\n"
            "• Логи сохраняются в systemd journal\n"
            "• Автоматическая ротация логов\n"
            "• Максимум 50 записей для error/warning\n"
            "• Максимум 30 записей для всех логов\n"
            "• Ограничение размера сообщения (3500 символов)\n\n"
            "<b>🔧 Диагностика проблем:</b>\n"
            "• Если journalctl недоступен - используются файлы логов\n"
            "• Проверка PATH в systemd сервисе\n"
            "• Статус сервиса: systemctl status antispam-bot.service\n"
            "• Перезапуск: systemctl restart antispam-bot.service\n\n"
            "<b>💡 Полезные советы:</b>\n"
            "• Используйте /logs error для поиска проблем\n"
            "• /logs warning показывает предупреждения системы\n"
            "• Логи обрезаются если слишком длинные\n"
            "• Все логи содержат временные метки и детали"
        )

    def get_command_info(self, command: str) -> Optional[CommandInfo]:
        """Get information about specific command."""
        return self.commands.get(command.lstrip("/"), None)

    def get_all_commands(self, admin_only: bool = False) -> List[CommandInfo]:
        """Get all commands, optionally filtered by admin status."""
        if admin_only:
            return [cmd for cmd in self.commands.values() if cmd.admin_only]
        return list(self.commands.values())

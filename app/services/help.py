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
            "status": CommandInfo(
                command="/status",
                description="Статистика работы бота",
                usage="/status",
                examples=["/status"],
                admin_only=True,
            ),
            "channels": CommandInfo(
                command="/channels",
                description="Управление каналами",
                usage="/channels",
                examples=["/channels"],
                admin_only=True,
            ),
            "bots": CommandInfo(
                command="/bots",
                description="Управление ботами",
                usage="/bots",
                examples=["/bots"],
                admin_only=True,
            ),
            "suspicious": CommandInfo(
                command="/suspicious",
                description="Просмотр подозрительных профилей",
                usage="/suspicious",
                examples=["/suspicious"],
                admin_only=True,
            ),
            "reset_suspicious": CommandInfo(
                command="/reset_suspicious",
                description="Сброс статусов подозрительных профилей",
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
            "setlimit": CommandInfo(
                command="/setlimit",
                description="Изменение лимитов системы",
                usage="/setlimit <тип> <значение>",
                examples=["/setlimit messages 15", "/setlimit threshold 0.3"],
                admin_only=True,
            ),
            "reload_limits": CommandInfo(
                command="/reload_limits",
                description="Перезагрузка лимитов из файла",
                usage="/reload_limits",
                examples=["/reload_limits"],
                admin_only=True,
            ),
            "settings": CommandInfo(
                command="/settings",
                description="Настройки бота",
                usage="/settings",
                examples=["/settings"],
                admin_only=True,
            ),
            "logs": CommandInfo(
                command="/logs",
                description="Просмотр логов",
                usage="/logs [уровень]",
                examples=["/logs", "/logs error"],
                admin_only=True,
            ),
        }

    def get_main_help(self, is_admin: bool = False) -> str:
        """Get main help text."""
        help_text = (
            "🤖 <b>AntiSpam Bot - Справка</b>\n\n"
            "Этот бот предназначен для автоматической модерации каналов и защиты от спама.\n\n"
        )

        if is_admin:
            help_text += self._get_admin_commands()
        else:
            help_text += self._get_user_commands()

        help_text += (
            "\n📖 <b>Дополнительная информация:</b>\n"
            "• Используйте /help [категория] для подробной справки\n"
            "• Все команды работают в личных сообщениях\n"
            "• Для получения прав администратора обратитесь к разработчику\n\n"
            "🔗 <b>Полезные ссылки:</b>\n"
            "• GitHub: https://github.com/your-repo\n"
            "• Документация: https://docs.example.com\n"
            "• Поддержка: @your_support"
        )

        return help_text

    def get_category_help(self, category: str, user_id: Optional[int] = None) -> str:
        """Get help for specific category."""
        from app.auth.authorization import AuthorizationService

        category = category.lower()

        # Use proper authorization service instead of client-side check
        auth_service = AuthorizationService()
        is_admin = auth_service.is_admin(user_id) if user_id else False

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

        elif category == "user":
            return self._get_user_commands_detailed()

        else:
            return (
                "❓ <b>Доступные категории справки:</b>\n\n"
                "• <b>admin</b> - команды администратора\n"
                "• <b>channels</b> - управление каналами\n"
                "• <b>bots</b> - управление ботами\n"
                "• <b>moderation</b> - модерация\n"
                "• <b>user</b> - пользовательские команды\n\n"
                "Используйте: /help [категория]"
            )

    def _get_admin_commands(self) -> str:
        """Get admin commands list."""
        commands_text = "👑 <b>Команды администратора:</b>\n"

        # Генерируем список команд динамически из self.commands
        for command_key, command_info in self.commands.items():
            if command_info.admin_only:
                commands_text += f"{command_info.command} - {command_info.description}\n"

        commands_text += "\n"
        return commands_text

    def _get_user_commands(self) -> str:
        """Get user commands list."""
        return (
            "👤 <b>Пользовательские команды:</b>\n"
            "/start - главное меню\n"
            "/help - справка по командам\n\n"
        )

    def _get_admin_commands_detailed(self) -> str:
        """Get detailed admin commands help."""
        return (
            "👑 <b>Команды администратора</b>\n\n"
            "<b>📊 /status</b>\n"
            "Показывает статистику работы бота:\n"
            "• Количество каналов (разрешены/заблокированы)\n"
            "• Количество ботов в whitelist\n"
            "• Общий статус системы\n\n"
            "<b>📺 /channels</b>\n"
            "Управление каналами:\n"
            "• Просмотр списка каналов\n"
            "• Добавление/удаление из whitelist\n"
            "• Просмотр статистики по каналам\n\n"
            "<b>🤖 /bots</b>\n"
            "Управление ботами:\n"
            "• Просмотр списка ботов\n"
            "• Управление whitelist ботов\n"
            "• Статистика по ботам\n\n"
            "<b>🔍 /suspicious</b>\n"
            "Подозрительные профили:\n"
            "• Просмотр подозрительных аккаунтов\n"
            "• Анализ поведения пользователей\n"
            "• Управление блокировками\n"
            "• Кнопки модерации (забанить/наблюдать/разрешить)\n\n"
            "<b>🔄 /reset_suspicious</b>\n"
            "Сброс статусов подозрительных профилей:\n"
            "• Сброс статуса 'проверено' на 'ожидает проверки'\n"
            "• Позволяет повторно протестировать профили\n"
            "• Полезно для тестирования системы\n\n"
            "<b>📊 /recalculate_suspicious</b>\n"
            "Пересчет подозрительных профилей:\n"
            "• Применяет новые веса паттернов\n"
            "• Обновляет счет подозрительности\n"
            "• Используется после изменения алгоритма\n\n"
            "<b>🧹 /cleanup_duplicates</b>\n"
            "Очистка дублирующих профилей:\n"
            "• Удаляет дублирующие записи\n"
            "• Оставляет только самый свежий профиль\n"
            "• Исправляет ошибки в базе данных\n\n"
            "<b>⚙️ /settings</b>\n"
            "Настройки бота:\n"
            "• Конфигурация фильтров\n"
            "• Настройка уведомлений\n"
            "• Управление правами\n\n"
            "<b>📋 /logs</b>\n"
            "Просмотр логов:\n"
            "• /logs - все логи\n"
            "• /logs error - только ошибки\n"
            "• /logs warning - предупреждения и ошибки\n"
        )

    def _get_channels_help(self) -> str:
        """Get channels management help."""
        return (
            "📺 <b>Управление каналами</b>\n\n"
            "Бот автоматически отслеживает сообщения от каналов и уведомляет администраторов.\n\n"
            "<b>🔔 Уведомления:</b>\n"
            "При получении сообщения от нового канала вы получите уведомление с кнопками:\n"
            "• ✅ <b>Разрешить</b> - добавить канал в whitelist\n"
            "• 🚫 <b>Заблокировать</b> - добавить канал в blacklist\n"
            "• 🗑 <b>Удалить сообщение</b> - удалить сообщение\n"
            "• 👁 <b>Просмотр</b> - посмотреть содержимое сообщения\n\n"
            "<b>📊 Статистика каналов:</b>\n"
            "• Общее количество каналов\n"
            "• Разрешенные каналы\n"
            "• Заблокированные каналы\n"
            "• Каналы на модерации\n\n"
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
            "• Доступные категории: admin, channels, bots, moderation\n\n"
            "<b>ℹ️ Дополнительная информация:</b>\n"
            "• Бот работает в фоновом режиме\n"
            "• Все команды работают в личных сообщениях\n"
            "• Для получения прав администратора обратитесь к разработчику"
        )

    def get_command_info(self, command: str) -> Optional[CommandInfo]:
        """Get information about specific command."""
        return self.commands.get(command.lstrip("/"), None)

    def get_all_commands(self, admin_only: bool = False) -> List[CommandInfo]:
        """Get all commands, optionally filtered by admin status."""
        if admin_only:
            return [cmd for cmd in self.commands.values() if cmd.admin_only]
        return list(self.commands.values())

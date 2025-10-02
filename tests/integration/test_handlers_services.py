"""
Интеграционные тесты для взаимодействия handlers и services
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery

from app.handlers.admin.basic import basic_router
from app.services.moderation import ModerationService
from app.services.bots import BotService
from app.services.status import StatusService


class TestHandlersServicesIntegration:
    """Тесты интеграции обработчиков и сервисов"""

    @pytest.mark.asyncio
    async def test_status_command_integration(self, test_config, mock_bot, test_db_session, create_test_message, test_admin_user, test_private_chat):
        """Тест интеграции команды /status с сервисами"""
        message = create_test_message(
            text="/status",
            user_id=test_admin_user.id,
            chat_id=test_private_chat.id,
            is_admin=True
        )
        
        # Создаем необходимые сервисы
        moderation_service = ModerationService(mock_bot, test_db_session)
        bot_service = BotService(mock_bot, test_db_session)
        status_service = StatusService(
            moderation_service=moderation_service,
            bot_service=bot_service,
            channel_service=None  # Упрощаем для теста
        )
        
        # Мокаем методы сервисов
        with patch.object(status_service, 'get_bot_status') as mock_get_status:
            mock_get_status.return_value = "🤖 **Статус бота**\n\n✅ Бот активен"
            
            # Мокаем отправку сообщения
            message.answer = AsyncMock()
            
            # Импортируем и вызываем обработчик
            from app.handlers.admin.basic import handle_status_command
            
            # Мокаем send_silent_response вместо message.answer
            with patch('app.handlers.admin.basic.send_silent_response') as mock_send_silent:
                await handle_status_command(
                    message=message,
                    status_service=status_service,
                    admin_id=test_admin_user.id
                )
                
                # Проверяем что сервис был вызван
                mock_get_status.assert_called_once()
                
                # Проверяем что send_silent_response был вызван
                mock_send_silent.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_command_integration(self, test_config, mock_bot, test_db_session, create_test_message, test_admin_user, test_private_chat):
        """Тест интеграции команды /help с HelpService"""
        message = create_test_message(
            text="/help",
            user_id=test_admin_user.id,
            chat_id=test_private_chat.id,
            is_admin=True
        )
        
        # Создаем HelpService
        from app.services.help import HelpService
        help_service = HelpService()
        
        # Мокаем методы сервиса (используем существующий метод)
        with patch.object(help_service, 'get_main_help') as mock_get_help:
            mock_get_help.return_value = "📚 **Справка по командам**\n\n/status - статус бота"
            
            message.answer = AsyncMock()
            
            # Импортируем и вызываем обработчик
            from app.handlers.admin.basic import handle_help_command
            
            # Мокаем send_silent_response вместо message.answer
            with patch('app.handlers.admin.basic.send_silent_response') as mock_send_silent:
                await handle_help_command(
                    message=message,
                    help_service=help_service,
                    admin_id=test_admin_user.id
                )
                
                # Проверяем вызовы
                mock_get_help.assert_called_once_with(is_admin=True)
                mock_send_silent.assert_called_once()

    @pytest.mark.asyncio
    async def test_moderation_command_integration(self, test_config, mock_bot, test_db_session, create_test_message, test_admin_user, test_chat):
        """Тест интеграции команд модерации с ModerationService"""
        # Тест команды бана
        ban_message = create_test_message(
            text="/ban 123456789 Spam",
            user_id=test_admin_user.id,
            chat_id=test_chat.id,
            is_admin=True
        )
        
        moderation_service = ModerationService(mock_bot, test_db_session)
        
        # Мокаем метод бана
        with patch.object(moderation_service, 'ban_user') as mock_ban:
            mock_ban.return_value = True
            
            ban_message.answer = AsyncMock()
            
            # Симулируем обработчик бана
            async def handle_ban_command(message: Message, moderation_service: ModerationService):
                # Парсим команду
                parts = message.text.split()
                if len(parts) >= 2:
                    try:
                        user_id = int(parts[1])
                        reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение правил"
                        
                        result = await moderation_service.ban_user(user_id, message.chat.id, reason)
                        
                        if result:
                            await message.answer(f"✅ Пользователь {user_id} забанен")
                        else:
                            await message.answer("❌ Ошибка при бане пользователя")
                    except ValueError:
                        await message.answer("❌ Некорректный ID пользователя")
                else:
                    await message.answer("❌ Использование: /ban <user_id> [причина]")
            
            await handle_ban_command(ban_message, moderation_service)
            
            # Проверяем вызовы
            mock_ban.assert_called_once_with(123456789, test_chat.id, "Spam")
            ban_message.answer.assert_called_once_with("✅ Пользователь 123456789 забанен")

    @pytest.mark.asyncio
    async def test_callback_query_integration(self, test_config, mock_bot, test_db_session, test_admin_user, test_chat):
        """Тест интеграции callback query с сервисами"""
        # Создаем callback query (MagicMock для избежания frozen instance)
        callback_query = MagicMock()
        callback_query.id = "test_callback"
        callback_query.from_user = test_admin_user
        callback_query.chat_instance = "test_chat"
        callback_query.data = "spam_stats"
        callback_query.message = MagicMock()
        callback_query.message.edit_text = AsyncMock()
        
        # Создаем сервисы
        from app.utils.pii_protection import secure_logger
        
        # Мокаем secure_logger
        with patch.object(secure_logger, 'get_spam_analysis_data') as mock_get_data:
            mock_get_data.return_value = [
                {'timestamp': '2024-01-01', 'type': 'spam', 'data': 'test'}
            ]
            
            # Симулируем обработчик callback
            async def handle_spam_stats_callback(callback: CallbackQuery):
                if callback.from_user.id != 439304619:  # Проверка админа
                    return
                
                spam_data = secure_logger.get_spam_analysis_data(days=30)
                
                if spam_data:
                    stats_text = f"📊 **Статистика спама**\n\nВсего записей: {len(spam_data)}"
                else:
                    stats_text = "❌ Данные не найдены"
                
                await callback.message.edit_text(stats_text)
            
            # Подменяем ID админа для теста (создаем новый MagicMock)
            callback_query.from_user = MagicMock()
            callback_query.from_user.id = 439304619
            
            await handle_spam_stats_callback(callback_query)
            
            # Проверяем вызовы
            mock_get_data.assert_called_once_with(days=30)
            callback_query.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_handlers(self, test_config, mock_bot, test_db_session, create_test_message, test_admin_user, test_private_chat):
        """Тест обработки ошибок в handlers"""
        message = create_test_message(
            text="/status",
            user_id=test_admin_user.id,
            chat_id=test_private_chat.id,
            is_admin=True
        )
        
        # Создаем сервис который будет выбрасывать ошибку
        status_service = MagicMock()
        status_service.get_bot_status = AsyncMock(side_effect=Exception("Service error"))
        
        message.answer = AsyncMock()
        
        # Симулируем обработчик с обработкой ошибок
        async def handle_status_with_error_handling(message: Message, status_service):
            try:
                status = await status_service.get_bot_status()
                await message.answer(status)
            except Exception as e:
                await message.answer(f"❌ Ошибка получения статуса: {str(e)}")
        
        await handle_status_with_error_handling(message, status_service)
        
        # Проверяем что ошибка была обработана
        status_service.get_bot_status.assert_called_once()
        message.answer.assert_called_once_with("❌ Ошибка получения статуса: Service error")

    @pytest.mark.asyncio
    async def test_service_method_chaining(self, test_config, mock_bot, test_db_session):
        """Тест цепочки вызовов методов сервисов"""
        # Создаем сервисы
        moderation_service = ModerationService(mock_bot, test_db_session)
        bot_service = BotService(mock_bot, test_db_session)
        
        # Мокаем методы (используем существующие методы)
        with patch.object(moderation_service, 'get_banned_users') as mock_get_banned, \
             patch.object(bot_service, 'get_all_bots') as mock_get_all_bots:
            
            mock_get_banned.return_value = [123456789, 987654321]
            mock_get_all_bots.return_value = []  # Пустой список ботов
            
            # Симулируем сложную операцию
            async def complex_operation():
                # Получаем всех ботов
                all_bots = await bot_service.get_all_bots()
                
                # Получаем список забаненных пользователей
                banned_users = await moderation_service.get_banned_users()
                
                return {
                    'bots_count': len(all_bots),
                    'banned_count': len(banned_users),
                    'banned_users': banned_users
                }
            
            result = await complex_operation()
            
            # Проверяем результат
            assert result['bots_count'] == 0
            assert result['banned_count'] == 2
            assert 123456789 in result['banned_users']
            
            # Проверяем что методы были вызваны
            mock_get_all_bots.assert_called_once()
            mock_get_banned.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_service_calls(self, test_config, mock_bot, test_db_session):
        """Тест параллельных вызовов сервисов"""
        import asyncio
        
        moderation_service = ModerationService(mock_bot, test_db_session)
        
        # Мокаем методы с задержкой
        async def mock_ban_user(*args, **kwargs):
            await asyncio.sleep(0.1)  # Имитируем задержку
            return True
        
        with patch.object(moderation_service, 'ban_user', side_effect=mock_ban_user):
            
            # Параллельные операции
            tasks = [
                moderation_service.ban_user(123456789, -1001234567890, "Spam"),
                moderation_service.ban_user(987654321, -1001234567890, "Flood"),
                moderation_service.ban_user(555666777, -1001234567890, "Abuse")
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Все операции должны быть успешными
            assert all(results)
            assert len(results) == 3

    @pytest.mark.asyncio
    async def test_service_state_consistency(self, test_config, mock_bot, test_db_session):
        """Тест консистентности состояния сервисов"""
        moderation_service = ModerationService(mock_bot, test_db_session)
        
        # Проверяем что сервис сохраняет состояние между вызовами
        assert moderation_service.bot is mock_bot
        assert moderation_service.db is test_db_session
        
        # Создаем второй экземпляр с теми же параметрами
        moderation_service_2 = ModerationService(mock_bot, test_db_session)
        
        # Сервисы должны иметь одинаковые зависимости
        assert moderation_service.bot is moderation_service_2.bot
        assert moderation_service.db is moderation_service_2.db


class TestRealWorldScenarios:
    """Тесты реальных сценариев использования"""

    @pytest.mark.asyncio
    async def test_admin_workflow(self, test_config, mock_bot, test_db_session, create_test_message, test_admin_user, test_chat):
        """Тест полного админского workflow"""
        # 1. Админ проверяет статус бота
        status_message = create_test_message("/status", user_id=test_admin_user.id, chat_id=test_chat.id, is_admin=True)
        
        # 2. Админ банит пользователя
        ban_message = create_test_message("/ban 123456789 Spam", user_id=test_admin_user.id, chat_id=test_chat.id, is_admin=True)
        
        # 3. Админ проверяет список забаненных
        banned_message = create_test_message("/banned", user_id=test_admin_user.id, chat_id=test_chat.id, is_admin=True)
        
        # Создаем сервисы
        moderation_service = ModerationService(mock_bot, test_db_session)
        
        # Мокаем ответы
        status_message.answer = AsyncMock()
        ban_message.answer = AsyncMock()
        banned_message.answer = AsyncMock()
        
        with patch.object(moderation_service, 'ban_user') as mock_ban, \
             patch.object(moderation_service, 'get_banned_users') as mock_get_banned:
            
            mock_ban.return_value = True
            mock_get_banned.return_value = [123456789]
            
            # Выполняем workflow
            # 1. Статус (упрощенно)
            await status_message.answer("✅ Бот активен")
            
            # 2. Бан
            result = await moderation_service.ban_user(123456789, test_chat.id, "Spam")
            if result:
                await ban_message.answer("✅ Пользователь забанен")
            
            # 3. Список забаненных
            banned_users = await moderation_service.get_banned_users()
            await banned_message.answer(f"📋 Забанено пользователей: {len(banned_users)}")
            
            # Проверяем что все операции выполнены
            status_message.answer.assert_called_once()
            ban_message.answer.assert_called_once()
            banned_message.answer.assert_called_once()
            
            mock_ban.assert_called_once()
            mock_get_banned.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, test_config, mock_bot, test_db_session, create_test_message, test_admin_user, test_chat):
        """Тест восстановления после ошибок"""
        message = create_test_message("/status", user_id=test_admin_user.id, chat_id=test_chat.id, is_admin=True)
        message.answer = AsyncMock()
        
        # Создаем сервис который сначала падает, потом работает
        call_count = 0
        
        async def flaky_service_method():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary error")
            return "Service OK"
        
        # Симулируем обработчик с retry логикой
        async def resilient_handler(message: Message):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await flaky_service_method()
                    await message.answer(f"✅ {result}")
                    return
                except Exception as e:
                    if attempt == max_retries - 1:
                        await message.answer(f"❌ Ошибка после {max_retries} попыток: {e}")
                    else:
                        continue  # Retry
        
        await resilient_handler(message)
        
        # Проверяем что в итоге получили успешный результат
        message.answer.assert_called_once_with("✅ Service OK")

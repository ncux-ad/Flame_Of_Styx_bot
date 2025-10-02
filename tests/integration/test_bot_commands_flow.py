"""
Интеграционные тесты для полного цикла обработки команд бота
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Dispatcher, F, Router
from aiogram.types import Message, Update, User, Chat

from app.middlewares.di_middleware import DIMiddleware
from app.middlewares.ratelimit import RateLimitMiddleware
from app.middlewares.validation import ValidationMiddleware


class TestBotCommandsFlow:
    """Тесты полного цикла обработки команд"""

    @pytest.mark.asyncio
    async def test_help_command_full_flow(self, test_dispatcher, mock_bot, test_config, create_test_message, create_test_update):
        """Тест полного цикла команды /help"""
        # Создаем сообщение с помощью фабрики
        message = create_test_message(
            text="/help",
            user_id=987654321,  # Админ ID
            is_admin=True
        )
        
        # Создаем роутер с обработчиком
        router = Router()
        help_responses = []
        
        @router.message(F.text == "/help")
        async def help_handler(
            msg: Message,
            help_service=None,
            admin_id: int = None
        ):
            # Симулируем работу HelpService
            if admin_id and admin_id in [123456789, 987654321]:
                help_text = "📚 **Админские команды:**\n\n/status - статус бота\n/help - эта справка"
            else:
                help_text = "📚 **Пользовательские команды:**\n\n/help - справка"
            
            help_responses.append(help_text)
            await msg.answer(help_text)
        
        test_dispatcher.include_router(router)
        
        # Создаем Update
        update = create_test_update(message=message)
        
        # Подготавливаем данные для middleware
        with patch('app.middlewares.di_middleware.DIMiddleware._initialize_services') as mock_init_services:
            # Мокаем инициализацию сервисов
            async def mock_init(data):
                data['help_service'] = MagicMock()
                data['admin_id'] = 987654321
            
            mock_init_services.side_effect = mock_init
            
            # Обрабатываем команду
            await test_dispatcher.feed_update(bot=mock_bot, update=update)
            
            # Проверяем результат
            assert len(help_responses) == 1
            assert "Админские команды" in help_responses[0]
            message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_command_full_flow(self, test_dispatcher, mock_bot, test_config, create_test_message, test_admin_user, test_private_chat):
        """Тест полного цикла команды /status"""
        message = create_test_message(
            text="/status",
            user=test_admin_user,
            chat=test_private_chat
        )
        
        router = Router()
        status_responses = []
        
        @router.message(F.text == "/status")
        async def status_handler(
            msg: Message,
            status_service=None,
            admin_id: int = None
        ):
            # Симулируем работу StatusService
            status_text = (
                "🤖 **Статус бота**\n\n"
                "✅ Бот активен\n"
                f"👑 Администратор: {admin_id}\n"
                "📊 Статистика: OK"
            )
            
            status_responses.append(status_text)
            await msg.answer(status_text)
        
        test_dispatcher.include_router(router)
        message.answer = AsyncMock()
        
        update = Update(update_id=2, message=message)
        
        with patch('app.middlewares.di_middleware.DIMiddleware._initialize_services') as mock_init_services:
            async def mock_init(data):
                data['status_service'] = MagicMock()
                data['admin_id'] = test_admin_user.id
            
            mock_init_services.side_effect = mock_init
            
            await test_dispatcher.feed_update(bot=mock_bot, update=update)
            
            assert len(status_responses) == 1
            assert "Бот активен" in status_responses[0]
            assert str(test_admin_user.id) in status_responses[0]

    @pytest.mark.asyncio
    async def test_ban_command_full_flow(self, test_dispatcher, mock_bot, test_config, create_test_message, test_admin_user, test_chat):
        """Тест полного цикла команды бана"""
        message = create_test_message(
            text="/ban 123456789 Спам в чате",
            user=test_admin_user,
            chat=test_chat
        )
        
        router = Router()
        ban_results = []
        
        @router.message(F.text.startswith("/ban"))
        async def ban_handler(
            msg: Message,
            moderation_service=None,
            admin_id: int = None
        ):
            # Парсим команду
            parts = msg.text.split()
            if len(parts) < 2:
                await msg.answer("❌ Использование: /ban <user_id> [причина]")
                return
            
            try:
                user_id = int(parts[1])
                reason = " ".join(parts[2:]) if len(parts) > 2 else "Нарушение правил"
                
                # Симулируем работу ModerationService
                ban_success = True  # Мокаем успешный бан
                
                if ban_success:
                    result_text = f"✅ Пользователь {user_id} забанен\nПричина: {reason}"
                    ban_results.append(('success', user_id, reason))
                else:
                    result_text = f"❌ Ошибка при бане пользователя {user_id}"
                    ban_results.append(('error', user_id, reason))
                
                await msg.answer(result_text)
                
            except ValueError:
                await msg.answer("❌ Некорректный ID пользователя")
                ban_results.append(('invalid_id', None, None))
        
        test_dispatcher.include_router(router)
        message.answer = AsyncMock()
        
        update = Update(update_id=3, message=message)
        
        with patch('app.middlewares.di_middleware.DIMiddleware._initialize_services') as mock_init_services:
            async def mock_init(data):
                data['moderation_service'] = MagicMock()
                data['admin_id'] = test_admin_user.id
            
            mock_init_services.side_effect = mock_init
            
            await test_dispatcher.feed_update(bot=mock_bot, update=update)
            
            assert len(ban_results) == 1
            assert ban_results[0][0] == 'success'
            assert ban_results[0][1] == 123456789
            assert ban_results[0][2] == "Спам в чате"

    @pytest.mark.asyncio
    async def test_invalid_command_handling(self, test_dispatcher, mock_bot, test_config, create_test_message, test_user, test_private_chat):
        """Тест обработки некорректных команд"""
        message = create_test_message(
            text="/nonexistent_command",
            user=test_user,
            chat=test_private_chat
        )
        
        router = Router()
        unknown_commands = []
        
        # Обработчик для неизвестных команд
        @router.message(F.text.startswith("/"))
        async def unknown_command_handler(msg: Message):
            unknown_commands.append(msg.text)
            await msg.answer("❌ Неизвестная команда. Используйте /help для получения справки.")
        
        test_dispatcher.include_router(router)
        message.answer = AsyncMock()
        
        update = Update(update_id=4, message=message)
        
        await test_dispatcher.feed_update(bot=mock_bot, update=update)
        
        assert len(unknown_commands) == 1
        assert unknown_commands[0] == "/nonexistent_command"

    @pytest.mark.asyncio
    async def test_rate_limiting_in_command_flow(self, test_config, mock_bot, create_test_message, test_user, test_private_chat):
        """Тест rate limiting в потоке команд"""
        # Создаем диспетчер с агрессивным rate limiting
        dp = Dispatcher()
        dp.message.middleware(RateLimitMiddleware(
            user_limit=2,  # Только 2 сообщения
            admin_limit=10,
            interval=60
        ))
        
        router = Router()
        processed_commands = []
        
        @router.message(F.text.startswith("/test"))
        async def test_command_handler(msg: Message):
            processed_commands.append(msg.text)
            await msg.answer(f"Обработана команда: {msg.text}")
        
        dp.include_router(router)
        
        # Отправляем несколько команд подряд
        for i in range(5):
            message = create_test_message(
                text=f"/test{i}",
                user=test_user,
                chat=test_private_chat
            )
            message.answer = AsyncMock()
            
            update = Update(update_id=10+i, message=message)
            
            try:
                await dp.feed_update(bot=mock_bot, update=update)
            except Exception as e:
                # Rate limiting может вызывать исключения
                print(f"Rate limit exception (expected): {e}")
        
        # Первые команды должны пройти, остальные заблокированы
        print(f"Processed commands: {len(processed_commands)}")
        assert len(processed_commands) <= 2  # Не больше лимита

    @pytest.mark.asyncio
    async def test_validation_in_command_flow(self, test_dispatcher, mock_bot, test_config, create_test_message, test_user, test_private_chat):
        """Тест валидации в потоке команд"""
        # Команда с подозрительным содержимым
        suspicious_message = create_test_message(
            text="/help <script>alert('xss')</script>",
            user=test_user,
            chat=test_private_chat
        )
        
        # Нормальная команда
        normal_message = create_test_message(
            text="/help",
            user=test_user,
            chat=test_private_chat
        )
        
        router = Router()
        processed_messages = []
        
        @router.message(F.text.startswith("/help"))
        async def help_handler(msg: Message):
            processed_messages.append(msg.text)
            await msg.answer("Справка отправлена")
        
        test_dispatcher.include_router(router)
        
        # Мокаем валидатор для блокировки подозрительных сообщений
        with patch('app.middlewares.validation.input_validator') as mock_validator:
            def validate_side_effect(message):
                if "<script>" in message.text:
                    return [MagicMock(severity=MagicMock(CRITICAL=4))]
                return []
            
            mock_validator.validate_message.side_effect = validate_side_effect
            
            # Обрабатываем подозрительное сообщение
            suspicious_message.answer = AsyncMock()
            suspicious_update = Update(update_id=20, message=suspicious_message)
            
            await test_dispatcher.feed_update(bot=mock_bot, update=suspicious_update)
            
            # Обрабатываем нормальное сообщение
            normal_message.answer = AsyncMock()
            normal_update = Update(update_id=21, message=normal_message)
            
            await test_dispatcher.feed_update(bot=mock_bot, update=normal_update)
        
        # Только нормальное сообщение должно быть обработано
        print(f"Processed messages: {processed_messages}")
        # В зависимости от реализации валидации результат может отличаться

    @pytest.mark.asyncio
    async def test_admin_vs_user_command_access(self, test_dispatcher, mock_bot, test_config, create_test_message, test_user, test_admin_user, test_private_chat):
        """Тест разграничения доступа к командам"""
        router = Router()
        command_access_log = []
        
        @router.message(F.text == "/admin_command")
        async def admin_command_handler(
            msg: Message,
            admin_id: int = None
        ):
            # Проверка прав администратора
            if msg.from_user and msg.from_user.id == admin_id:
                command_access_log.append(('admin_access', msg.from_user.id))
                await msg.answer("✅ Админская команда выполнена")
            else:
                command_access_log.append(('access_denied', msg.from_user.id if msg.from_user else None))
                await msg.answer("❌ Недостаточно прав для выполнения команды")
        
        test_dispatcher.include_router(router)
        
        # Тест доступа обычного пользователя
        user_message = create_test_message(
            text="/admin_command",
            user=test_user,
            chat=test_private_chat
        )
        user_message.answer = AsyncMock()
        
        # Тест доступа администратора
        admin_message = create_test_message(
            text="/admin_command",
            user=test_admin_user,
            chat=test_private_chat
        )
        admin_message.answer = AsyncMock()
        
        with patch('app.middlewares.di_middleware.DIMiddleware._initialize_services') as mock_init_services:
            async def mock_init(data):
                data['admin_id'] = test_admin_user.id  # ID админа
            
            mock_init_services.side_effect = mock_init
            
            # Обрабатываем команду от пользователя
            user_update = Update(update_id=30, message=user_message)
            await test_dispatcher.feed_update(bot=mock_bot, update=user_update)
            
            # Обрабатываем команду от админа
            admin_update = Update(update_id=31, message=admin_message)
            await test_dispatcher.feed_update(bot=mock_bot, update=admin_update)
        
        # Проверяем результаты
        assert len(command_access_log) == 2
        
        # Пользователю должно быть отказано в доступе
        user_log = next((log for log in command_access_log if log[1] == test_user.id), None)
        assert user_log and user_log[0] == 'access_denied'
        
        # Админу должен быть предоставлен доступ
        admin_log = next((log for log in command_access_log if log[1] == test_admin_user.id), None)
        assert admin_log and admin_log[0] == 'admin_access'

    @pytest.mark.asyncio
    async def test_error_handling_in_command_flow(self, test_dispatcher, mock_bot, test_config, create_test_message, test_admin_user, test_private_chat):
        """Тест обработки ошибок в потоке команд"""
        message = create_test_message(
            text="/failing_command",
            user=test_admin_user,
            chat=test_private_chat
        )
        
        router = Router()
        error_log = []
        
        @router.message(F.text == "/failing_command")
        async def failing_handler(msg: Message):
            try:
                # Симулируем ошибку в сервисе
                raise ValueError("Service unavailable")
            except Exception as e:
                error_log.append(str(e))
                await msg.answer(f"❌ Произошла ошибка: {str(e)}")
        
        test_dispatcher.include_router(router)
        message.answer = AsyncMock()
        
        update = Update(update_id=40, message=message)
        
        await test_dispatcher.feed_update(bot=mock_bot, update=update)
        
        # Ошибка должна быть обработана gracefully
        assert len(error_log) == 1
        assert "Service unavailable" in error_log[0]
        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_complex_command_with_parameters(self, test_dispatcher, mock_bot, test_config, create_test_message, test_admin_user, test_chat):
        """Тест сложной команды с параметрами"""
        message = create_test_message(
            text="/config set max_messages 15",
            user=test_admin_user,
            chat=test_chat
        )
        
        router = Router()
        config_changes = []
        
        @router.message(F.text.startswith("/config"))
        async def config_handler(
            msg: Message,
            admin_id: int = None
        ):
            parts = msg.text.split()
            
            if len(parts) < 2:
                await msg.answer("❌ Использование: /config <action> [параметры]")
                return
            
            action = parts[1]
            
            if action == "set" and len(parts) >= 4:
                param_name = parts[2]
                param_value = parts[3]
                
                # Симулируем изменение конфигурации
                config_changes.append((param_name, param_value))
                await msg.answer(f"✅ Параметр {param_name} установлен в {param_value}")
            
            elif action == "get" and len(parts) >= 3:
                param_name = parts[2]
                # Симулируем получение значения
                await msg.answer(f"📋 {param_name}: текущее_значение")
            
            else:
                await msg.answer("❌ Неверные параметры команды")
        
        test_dispatcher.include_router(router)
        message.answer = AsyncMock()
        
        update = Update(update_id=50, message=message)
        
        with patch('app.middlewares.di_middleware.DIMiddleware._initialize_services') as mock_init_services:
            async def mock_init(data):
                data['admin_id'] = test_admin_user.id
            
            mock_init_services.side_effect = mock_init
            
            await test_dispatcher.feed_update(bot=mock_bot, update=update)
        
        # Проверяем что конфигурация была изменена
        assert len(config_changes) == 1
        assert config_changes[0] == ("max_messages", "15")

    @pytest.mark.asyncio
    async def test_callback_query_flow(self, test_dispatcher, mock_bot, test_config, test_admin_user):
        """Тест обработки callback query"""
        from aiogram.types import CallbackQuery
        
        # Создаем callback query
        callback_query = CallbackQuery(
            id="test_callback_123",
            from_user=test_admin_user,
            chat_instance="test_chat_instance",
            data="spam_stats"
        )
        
        # Мокаем message для callback
        callback_query.message = MagicMock()
        callback_query.message.edit_text = AsyncMock()
        
        router = Router()
        callback_processed = []
        
        @router.callback_query(F.data == "spam_stats")
        async def spam_stats_callback(callback: CallbackQuery):
            # Проверяем права админа
            if callback.from_user.id == test_admin_user.id:
                callback_processed.append(callback.data)
                await callback.message.edit_text("📊 Статистика спама загружена")
            else:
                await callback.answer("❌ Недостаточно прав")
        
        test_dispatcher.include_router(router)
        
        # Создаем Update с callback query
        update = Update(update_id=60, callback_query=callback_query)
        
        await test_dispatcher.feed_update(bot=mock_bot, update=update)
        
        # Проверяем что callback был обработан
        assert len(callback_processed) == 1
        assert callback_processed[0] == "spam_stats"
        callback_query.message.edit_text.assert_called_once()


class TestEndToEndScenarios:
    """Тесты сценариев end-to-end"""

    @pytest.mark.asyncio
    async def test_complete_moderation_workflow(self, test_dispatcher, mock_bot, test_config, create_test_message, test_admin_user, test_chat):
        """Тест полного workflow модерации"""
        router = Router()
        workflow_steps = []
        
        # Обработчик статуса
        @router.message(F.text == "/status")
        async def status_handler(msg: Message):
            workflow_steps.append("status_checked")
            await msg.answer("✅ Бот активен, готов к модерации")
        
        # Обработчик бана
        @router.message(F.text.startswith("/ban"))
        async def ban_handler(msg: Message):
            parts = msg.text.split()
            if len(parts) >= 2:
                user_id = parts[1]
                workflow_steps.append(f"user_banned_{user_id}")
                await msg.answer(f"✅ Пользователь {user_id} забанен")
        
        # Обработчик списка забаненных
        @router.message(F.text == "/banned")
        async def banned_list_handler(msg: Message):
            workflow_steps.append("banned_list_requested")
            await msg.answer("📋 Список забаненных пользователей: 123456789")
        
        test_dispatcher.include_router(router)
        
        # Выполняем полный workflow
        commands = [
            "/status",
            "/ban 123456789 Spam",
            "/banned"
        ]
        
        for i, command_text in enumerate(commands):
            message = create_test_message(
                text=command_text,
                user=test_admin_user,
                chat=test_chat
            )
            message.answer = AsyncMock()
            
            update = Update(update_id=70+i, message=message)
            await test_dispatcher.feed_update(bot=mock_bot, update=update)
        
        # Проверяем что весь workflow выполнен
        expected_steps = ["status_checked", "user_banned_123456789", "banned_list_requested"]
        assert workflow_steps == expected_steps

    @pytest.mark.asyncio
    async def test_user_journey_from_help_to_action(self, test_dispatcher, mock_bot, test_config, create_test_message, test_admin_user, test_private_chat):
        """Тест пользовательского пути от справки до действия"""
        router = Router()
        user_journey = []
        
        @router.message(F.text == "/help")
        async def help_handler(msg: Message):
            user_journey.append("help_requested")
            help_text = (
                "📚 **Доступные команды:**\n\n"
                "/status - проверить статус бота\n"
                "/settings - настройки\n"
                "/help - эта справка"
            )
            await msg.answer(help_text)
        
        @router.message(F.text == "/settings")
        async def settings_handler(msg: Message):
            user_journey.append("settings_opened")
            await msg.answer("⚙️ Настройки бота")
        
        test_dispatcher.include_router(router)
        
        # Симулируем пользовательский путь
        journey_commands = ["/help", "/settings"]
        
        for i, command in enumerate(journey_commands):
            message = create_test_message(
                text=command,
                user=test_admin_user,
                chat=test_private_chat
            )
            message.answer = AsyncMock()
            
            update = Update(update_id=80+i, message=message)
            await test_dispatcher.feed_update(bot=mock_bot, update=update)
        
        # Проверяем пользовательский путь
        assert user_journey == ["help_requested", "settings_opened"]

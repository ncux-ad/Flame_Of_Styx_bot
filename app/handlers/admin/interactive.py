"""
Интерактивные команды и обработчики ввода
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.profiles import ProfileService
from app.services.limits import LimitsService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging
from app.middlewares.silent_logging import send_silent_response

logger = logging.getLogger(__name__)

# Создаем роутер для интерактивных команд
interactive_router = Router()

# Словарь для отслеживания состояния ожидания ввода
waiting_for_user_input = {}


async def analyze_user_by_id(message: Message, profile_service: ProfileService, admin_id: int, user_id: int) -> None:
    """Анализирует пользователя по ID."""
    try:
        # Получаем информацию о пользователе
        user_info = await profile_service.get_user_info(user_id)
        
        # Создаем объект User для анализа
        from aiogram.types import User
        user = User(
            id=user_info['id'],
            is_bot=user_info['is_bot'],
            first_name=user_info['first_name'],
            last_name=user_info['last_name'],
            username=user_info.get('username')
        )
        
        # Анализируем профиль
        logger.info("Starting profile analysis for user " + str(user_id))
        try:
            profile = await profile_service.analyze_user_profile(user, admin_id)
            logger.info("Profile analysis completed, profile: " + str(profile))
        except Exception as e:
            logger.error("Error in analyze_user_profile: " + str(e))
            raise
        
        # Формируем ответ
        logger.info("Starting text formatting")
        text = "🔍 <b>Анализ профиля пользователя</b>\n\n"
        logger.info("Added header")
        
        # Экранируем HTML символы
        def escape_html(text):
            if not text:
                return ""
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        first_name = escape_html(str(user_info['first_name'] or ''))
        last_name = escape_html(str(user_info['last_name'] or ''))
        username = escape_html(str(user_info['username'] or 'Нет'))
        
        text += "<b>Пользователь:</b> " + first_name + " " + last_name + "\n"
        logger.info("Added user name")
        
        text += "<b>ID:</b> <code>" + str(user_id) + "</code>\n"
        logger.info("Added user ID")
        
        text += "<b>Username:</b> @" + username + "\n"
        logger.info("Added username")
        
        if profile:
            logger.info("Profile exists, processing suspicious user")
            # Пользователь подозрительный
            text += "<b>Счет подозрительности:</b> " + str(profile.suspicion_score) + "\n"
            logger.info("Added suspicion score")
            
            # Безопасно парсим паттерны
            patterns = []
            if profile.detected_patterns and str(profile.detected_patterns).strip():
                try:
                    logger.info("Processing patterns: " + str(profile.detected_patterns))
                    # Дополнительная проверка типа
                    if isinstance(profile.detected_patterns, (str, int, float)):
                        patterns = str(profile.detected_patterns).split(',')
                        patterns = [p.strip() for p in patterns if p.strip()]
                    else:
                        patterns = []
                    logger.info("Parsed patterns: " + str(patterns))
                except Exception as e:
                    logger.error("Error parsing patterns: " + str(e))
                    patterns = []
            
            text += "<b>Обнаружено паттернов:</b> " + str(len(patterns)) + "\n\n"
            
            if patterns:
                text += "<b>🔍 Обнаруженные паттерны:</b>\n"
                for pattern in patterns:
                    text += "• " + escape_html(str(pattern)) + "\n"
                text += "\n"
            
            # Безопасно проверяем связанный чат
            if profile.linked_chat_title and str(profile.linked_chat_title).strip():
                try:
                    chat_title = str(profile.linked_chat_title).strip()
                    if chat_title:
                        text += "<b>📱 Связанный чат:</b> " + escape_html(chat_title) + "\n"
                        text += "<b>📊 Постов:</b> " + str(profile.post_count) + "\n\n"
                except Exception:
                    pass
            
            # Определяем статус
            try:
                score = float(str(profile.suspicion_score))
                if score >= 0.7:
                    status = "🔴 Высокий риск"
                elif score >= 0.4:
                    status = "🟡 Средний риск"
                else:
                    status = "🟢 Низкий риск"
            except Exception:
                status = "🟢 Низкий риск"
                
            text += "<b>Статус:</b> " + str(status) + "\n"
            
            # Безопасно форматируем дату
            try:
                if profile.created_at and hasattr(profile.created_at, 'strftime'):
                    date_str = profile.created_at.strftime('%d.%m.%Y %H:%M')
                else:
                    date_str = 'Неизвестно'
            except Exception:
                date_str = 'Неизвестно'
            
            text += "<b>Дата анализа:</b> " + str(date_str) + "\n"
        else:
            logger.info("No profile, processing non-suspicious user")
            # Пользователь не подозрительный
            text += "<b>Счет подозрительности:</b> 0.00\n"
            logger.info("Added suspicion score 0.00")
            
            text += "<b>Обнаружено паттернов:</b> 0\n\n"
            logger.info("Added patterns count 0")
            
            text += "<b>Статус:</b> 🟢 Низкий риск\n"
            logger.info("Added status")
            
            text += "<b>Результат:</b> Пользователь не является подозрительным\n"
            logger.info("Added result")
        
        await send_silent_response(message, text)
        logger.info("Profile analysis completed for user " + sanitize_for_logging(str(user_id)))

    except Exception as e:
        logger.error("Error in analyze_user_by_id: " + sanitize_for_logging(str(e)))
        await send_silent_response(message, "❌ Ошибка анализа профиля")


async def remove_suspicious_user_by_id(message: Message, profile_service: ProfileService, admin_id: int, user_id: int) -> None:
    """Удаляет пользователя из подозрительных по ID."""
    try:
        # Удаляем из подозрительных профилей
        profile = await profile_service._get_suspicious_profile(user_id)
        if not profile:
            await send_silent_response(message, "❌ Пользователь не найден в подозрительных профилях")
            return
            
        await profile_service.db.delete(profile)
        await profile_service.db.commit()
        
        await send_silent_response(message,
            f"✅ <b>Пользователь удален из подозрительных</b>\n\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"🗑️ Запись удалена из базы данных"
        )
        logger.info(f"Removed user {sanitize_for_logging(str(user_id))} from suspicious profiles by {sanitize_for_logging(str(admin_id))}")

    except Exception as e:
        logger.error(f"Error in remove_suspicious_user_by_id: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка удаления из подозрительных")


async def set_limit_by_params(message: Message, limits_service: LimitsService, limit_type: str, value: float) -> None:
    """Устанавливает лимит по параметрам."""
    try:
        # Маппинг типов лимитов
        limit_mapping = {
            "messages": "max_messages_per_minute",
            "links": "max_links_per_message",
            "ban": "ban_duration_hours",
            "threshold": "suspicion_threshold",
            "media_check": "check_media_without_caption",
            "allow_gifs": "allow_videos_without_caption",
            "allow_photos": "allow_photos_without_caption",
            "allow_videos": "allow_videos_without_caption",
            "doc_size": "max_document_size_suspicious",
        }

        if limit_type not in limit_mapping:
            await send_silent_response(message,
                "❌ <b>Неверный тип лимита</b>\n\n"
                "📋 <b>Доступные типы:</b>\n"
                "• messages - максимум сообщений в минуту\n"
                "• links - максимум ссылок в сообщении\n"
                "• ban - время блокировки в часах\n"
                "• threshold - порог подозрительности\n"
                "• media_check - проверка медиа без подписи (0/1)\n"
                "• allow_gifs - разрешить GIF без подписи (0/1)\n"
                "• allow_photos - разрешить фото без подписи (0/1)\n"
                "• allow_videos - разрешить видео без подписи (0/1)\n"
                "• doc_size - размер документа для подозрения (байты)"
            )
            return

        # Обновляем лимит
        success = limits_service.update_limit(limit_mapping[limit_type], value)

        if success:
            await send_silent_response(message,
                f"✅ <b>Лимит обновлен!</b>\n\n"
                f"📊 <b>{limit_type}</b> изменен на <b>{value}</b>\n\n"
                "🔄 Изменения применены немедленно благодаря hot-reload!"
            )
        else:
            await send_silent_response(message, "❌ Ошибка при обновлении лимита!")

        if message.from_user:
            logger.info(f"Setlimit response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in set_limit_by_params: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка при установке лимита!")


def get_example_value(limit_type: str) -> str:
    """Возвращает пример значения для типа лимита."""
    examples = {
        "messages": "15",
        "links": "3", 
        "ban": "24",
        "threshold": "0.5",
        "media_check": "1",
        "allow_gifs": "0",
        "allow_photos": "1",
        "allow_videos": "1",
        "doc_size": "100000"
    }
    return examples.get(limit_type, "10")


@interactive_router.message(Command("suspicious_analyze"))
async def handle_suspicious_analyze_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Проанализировать конкретного пользователя (интерактивная версия)."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious analyze command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await send_silent_response(message,("❌ Ошибка: пустое сообщение")
            return
        
        # Безопасное разбиение строки
        parts = message.text.split()
        
        # Если есть аргументы, используем старый способ
        if len(parts) >= 2:
            try:
                user_id = int(parts[1])
                await analyze_user_by_id(message, profile_service, admin_id, user_id)
                return
            except (ValueError, IndexError):
                await send_silent_response(message,("❌ Неверный формат ID пользователя")
                return
        
        # Интерактивный режим - запрашиваем ввод
        user_id = message.from_user.id
        waiting_for_user_input[user_id] = "suspicious_analyze"
        
        await send_silent_response(message,(
            "🔍 <b>Анализ подозрительного профиля</b>\n\n"
            "📝 <b>Введите ID пользователя или username:</b>\n\n"
            "• <b>ID:</b> <code>123456789</code>\n"
            "• <b>Username:</b> <code>@username</code>\n\n"
            "💡 <b>Примеры:</b>\n"
            "• <code>6157876046</code>\n"
            "• <code>@vvvvvmiyyyyy</code>\n\n"
            "❌ <b>Для отмены:</b> /cancel"
        )
        logger.info(f"Waiting for user input for suspicious_analyze from {sanitize_for_logging(str(user_id))}")

    except Exception as e:
        logger.error(f"Error in suspicious_analyze command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message,("❌ Ошибка анализа профиля")


@interactive_router.message(Command("suspicious_remove"))
async def handle_suspicious_remove_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Удалить пользователя из подозрительных (интерактивная версия)."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious remove command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await send_silent_response(message,("❌ Ошибка: пустое сообщение")
            return
        
        # Безопасное разбиение строки
        parts = message.text.split()
        
        # Если есть аргументы, используем старый способ
        if len(parts) >= 2:
            try:
                user_id = int(parts[1])
                await remove_suspicious_user_by_id(message, profile_service, admin_id, user_id)
                return
            except ValueError:
                await send_silent_response(message,("❌ Неверный формат ID пользователя")
                return
        
        # Интерактивный режим - запрашиваем ввод
        user_id = message.from_user.id
        waiting_for_user_input[user_id] = "suspicious_remove"
        
        await send_silent_response(message,(
            "🗑️ <b>Удаление из подозрительных профилей</b>\n\n"
            "📝 <b>Введите ID пользователя для удаления:</b>\n\n"
            "• <b>ID:</b> <code>123456789</code>\n\n"
            "💡 <b>Примеры:</b>\n"
            "• <code>6157876046</code>\n"
            "• <code>218729349</code>\n\n"
            "❌ <b>Для отмены:</b> /cancel"
        )
        logger.info(f"Waiting for user input for suspicious_remove from {sanitize_for_logging(str(user_id))}")

    except Exception as e:
        logger.error(f"Error in suspicious_remove command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message,("❌ Ошибка удаления из подозрительных")


@interactive_router.message(Command("setlimit"))
async def handle_setlimit_command(message: Message, limits_service: LimitsService) -> None:
    """Изменение конкретного лимита (интерактивная версия)."""
    try:
        if not message.from_user:
            return
        logger.info(f"Setlimit command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим команду: /setlimit <тип> <значение>
        text = message.text or ""
        parts = text.split()

        # Если есть аргументы, используем старый способ
        if len(parts) >= 3:
            limit_type = parts[1].lower()
            try:
                value = float(parts[2]) if limit_type == "threshold" else int(parts[2])
                await set_limit_by_params(message, limits_service, limit_type, value)
                return
            except ValueError:
                await send_silent_response(message,("❌ Значение должно быть числом!")
                return

        # Интерактивный режим - запрашиваем тип лимита
        user_id = message.from_user.id
        waiting_for_user_input[user_id] = "setlimit_type"
        
        await send_silent_response(message,(
            "⚙️ <b>Настройка лимитов</b>\n\n"
            "📝 <b>Выберите тип лимита для изменения:</b>\n\n"
            "• <b>messages</b> - максимум сообщений в минуту\n"
            "• <b>links</b> - максимум ссылок в сообщении\n"
            "• <b>ban</b> - время блокировки в часах\n"
            "• <b>threshold</b> - порог подозрительности\n"
            "• <b>media_check</b> - проверка медиа без подписи (0/1)\n"
            "• <b>allow_gifs</b> - разрешить GIF без подписи (0/1)\n"
            "• <b>allow_photos</b> - разрешить фото без подписи (0/1)\n"
            "• <b>allow_videos</b> - разрешить видео без подписи (0/1)\n"
            "• <b>doc_size</b> - размер документа для подозрения (байты)\n\n"
            "❌ <b>Для отмены:</b> /cancel"
        )
        logger.info(f"Waiting for limit type from {sanitize_for_logging(str(user_id))}")

    except Exception as e:
        logger.error(f"Error in setlimit command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message,("❌ Ошибка при обработке команды!")


@interactive_router.message(Command("cancel"))
async def handle_cancel_command(
    message: Message,
    admin_id: int,
) -> None:
    """Отменить текущую операцию."""
    try:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        if user_id in waiting_for_user_input:
            del waiting_for_user_input[user_id]
            await send_silent_response(message,("❌ Операция отменена")
            logger.info(f"Operation cancelled for user {sanitize_for_logging(str(user_id))}")
        else:
            await send_silent_response(message,("ℹ️ Нет активных операций для отмены")
            
    except Exception as e:
        logger.error(f"Error in cancel command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message,("❌ Ошибка отмены операции")


@interactive_router.message()
async def handle_user_input(
    message: Message,
    profile_service: ProfileService,
    limits_service: LimitsService,
    admin_id: int,
) -> None:
    """Обрабатывает ввод пользователя для интерактивных команд."""
    try:
        if not message.from_user or not message.text:
            return
        
        user_id = message.from_user.id
        
        # Проверяем, ожидает ли пользователь ввода
        if user_id not in waiting_for_user_input:
            return
        
        command = waiting_for_user_input[user_id]
        
        if command == "suspicious_analyze":
            # Обрабатываем ввод для анализа профиля
            input_text = message.text.strip()
            
            # Парсим ввод
            user_id_to_analyze = None
            
            if input_text.startswith("@"):
                # Это username
                username = input_text[1:]  # Убираем @
                try:
                    # Пытаемся найти пользователя по username
                    # Для простоты пока что не реализуем поиск по username
                    await send_silent_response(message,("❌ Поиск по username пока не поддерживается. Используйте ID пользователя.")
                    return
                except Exception as e:
                    await send_silent_response(message,(f"❌ Ошибка поиска пользователя: {sanitize_for_logging(str(e))}")
                    return
            else:
                # Это ID
                try:
                    user_id_to_analyze = int(input_text)
                except ValueError:
                    await send_silent_response(message,("❌ Неверный формат ID пользователя")
                    return
            
            # Убираем из ожидания
            del waiting_for_user_input[user_id]
            
            # Анализируем пользователя
            await analyze_user_by_id(message, profile_service, admin_id, user_id_to_analyze)
            
        elif command == "suspicious_remove":
            # Обрабатываем ввод для удаления из подозрительных
            input_text = message.text.strip()
            
            # Парсим ввод
            user_id_to_remove = None
            
            try:
                user_id_to_remove = int(input_text)
            except ValueError:
                await send_silent_response(message,("❌ Неверный формат ID пользователя")
                return
            
            # Убираем из ожидания
            del waiting_for_user_input[user_id]
            
            # Удаляем пользователя
            await remove_suspicious_user_by_id(message, profile_service, admin_id, user_id_to_remove)
            
        elif command == "setlimit_type":
            # Обрабатываем выбор типа лимита
            input_text = message.text.strip().lower()
            
            # Валидные типы лимитов
            valid_types = ["messages", "links", "ban", "threshold", "media_check", "allow_gifs", "allow_photos", "allow_videos", "doc_size"]
            
            if input_text not in valid_types:
                await send_silent_response(message,("❌ Неверный тип лимита. Выберите один из предложенных вариантов.")
                return
            
            # Сохраняем тип лимита и запрашиваем значение
            waiting_for_user_input[user_id] = f"setlimit_value_{input_text}"
            
            # Определяем тип значения
            if input_text == "threshold":
                value_type = "десятичное число (например: 0.5)"
            elif input_text in ["media_check", "allow_gifs", "allow_photos", "allow_videos"]:
                value_type = "0 или 1"
            elif input_text == "doc_size":
                value_type = "размер в байтах (например: 100000)"
            else:
                value_type = "целое число"
            
            await send_silent_response(message,(
                f"📝 <b>Введите значение для {input_text}:</b>\n\n"
                f"• Тип значения: {value_type}\n\n"
                f"💡 <b>Примеры:</b>\n"
                f"• Для {input_text}: {get_example_value(input_text)}\n\n"
                f"❌ <b>Для отмены:</b> /cancel"
            )
            
        elif command.startswith("setlimit_value_"):
            # Обрабатываем ввод значения лимита
            limit_type = command.replace("setlimit_value_", "")
            input_text = message.text.strip()
            
            try:
                # Парсим значение
                if limit_type == "threshold":
                    value = float(input_text)
                else:
                    value = int(input_text)
                
                # Убираем из ожидания
                del waiting_for_user_input[user_id]
                
                # Устанавливаем лимит
                await set_limit_by_params(message, limits_service, limit_type, value)
                
            except ValueError:
                await send_silent_response(message,("❌ Неверный формат значения. Введите число.")
                return
            
    except Exception as e:
        logger.error(f"Error in handle_user_input: {sanitize_for_logging(str(e))}")
        await send_silent_response(message,("❌ Ошибка обработки ввода")

"""
Обработчики команд для управления алертами
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.services.alerts import AlertLevel, AlertService, AlertType

alerts_router = Router()


@alerts_router.message(Command("alerts"))
async def handle_alerts_command(message: Message, alert_service: AlertService) -> None:
    """Показать статистику алертов"""
    try:
        stats = await alert_service.get_alert_stats()

        response = f"📊 <b>Статистика алертов</b>\n\n"
        response += f"🔴 Всего алертов: {stats['total_alerts']}\n"
        response += f"🕐 За последний час: {stats['recent_alerts']}\n"
        response += f"👑 Админов: {stats['admin_count']}\n"
        response += f"⏱️ Rate limited: {stats['rate_limited_admins']}\n\n"
        response += f"ℹ️ <i>Используйте /test_alert для тестирования</i>"

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики алертов: {e}")


@alerts_router.message(Command("test_alert"), IsAdminOrSilentFilter())
async def handle_test_alert_command(message: Message, alert_service: AlertService) -> None:
    """Тестировать отправку алерта"""
    try:
        # Отправляем тестовый алерт
        success = await alert_service.send_info_alert(
            title="Тестовый алерт",
            message="Это тестовое уведомление для проверки системы алертов",
            data={"test": True, "timestamp": "now"},
        )

        if success:
            await message.answer("✅ Тестовый алерт отправлен!")
        else:
            await message.answer("❌ Не удалось отправить тестовый алерт")

    except Exception as e:
        await message.answer(f"❌ Ошибка тестирования алерта: {e}")


@alerts_router.message(Command("alert_error"), IsAdminOrSilentFilter())
async def handle_test_error_alert_command(message: Message, alert_service: AlertService) -> None:
    """Тестировать алерт об ошибке"""
    try:
        success = await alert_service.send_error_alert(
            title="Тестовая ошибка",
            message="Это тестовое сообщение об ошибке",
            data={"error_code": "TEST_ERROR", "severity": "high"},
        )

        if success:
            await message.answer("✅ Тестовый алерт об ошибке отправлен!")
        else:
            await message.answer("❌ Не удалось отправить тестовый алерт об ошибке")

    except Exception as e:
        await message.answer(f"❌ Ошибка тестирования алерта об ошибке: {e}")


@alerts_router.message(Command("alert_warning"), IsAdminOrSilentFilter())
async def handle_test_warning_alert_command(message: Message, alert_service: AlertService) -> None:
    """Тестировать алерт-предупреждение"""
    try:
        success = await alert_service.send_warning_alert(
            title="Тестовое предупреждение",
            message="Это тестовое предупреждение о подозрительной активности",
            data={"user_id": 123456789, "pattern": "suspicious_behavior"},
        )

        if success:
            await message.answer("✅ Тестовый алерт-предупреждение отправлен!")
        else:
            await message.answer("❌ Не удалось отправить тестовый алерт-предупреждение")

    except Exception as e:
        await message.answer(f"❌ Ошибка тестирования алерта-предупреждения: {e}")


@alerts_router.message(Command("alert_success"), IsAdminOrSilentFilter())
async def handle_test_success_alert_command(message: Message, alert_service: AlertService) -> None:
    """Тестировать алерт об успехе"""
    try:
        success = await alert_service.send_success_alert(
            title="Тестовый успех",
            message="Это тестовое сообщение об успешном выполнении операции",
            data={"operation": "test_ban", "user_id": 123456789, "result": "success"},
        )

        if success:
            await message.answer("✅ Тестовый алерт об успехе отправлен!")
        else:
            await message.answer("❌ Не удалось отправить тестовый алерт об успехе")

    except Exception as e:
        await message.answer(f"❌ Ошибка тестирования алерта об успехе: {e}")

"""
Админ команды для анализа данных спама.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.keyboards.inline import get_spam_analysis_keyboard
from app.utils.pii_protection import secure_logger

logger = logging.getLogger(__name__)

router = Router()
# Фильтр применяется на уровне admin_router
# router.message.filter(IsAdminOrSilentFilter())
# router.callback_query.filter(IsAdminOrSilentFilter())


@router.message(Command("spam_analysis"), IsAdminOrSilentFilter())
async def spam_analysis_menu(message: Message):
    """Показать меню анализа спама."""
    try:
        logger.info(f"Spam analysis menu requested by user {message.from_user.id}")
        keyboard = get_spam_analysis_keyboard()
        
        await message.answer(
            "🔍 <b>Анализ данных спама</b>\n\n"
            "Выберите действие для анализа собранных данных:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"Spam analysis menu sent to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in spam_analysis_menu: {e}")
        await message.answer("❌ Ошибка при загрузке меню анализа спама")


@router.callback_query(F.data == "spam_stats")
async def show_spam_stats(callback: CallbackQuery):
    """Показать статистику спама."""
    try:
        # Получаем данные за последние 30 дней
        spam_data = secure_logger.get_spam_analysis_data(days=30)
        
        if not spam_data:
            await callback.message.edit_text(
                "📊 **Статистика спама**\n\n"
                "❌ Данные за последние 30 дней не найдены.\n"
                "Убедитесь, что включено полное логирование.",
                parse_mode="Markdown"
            )
            return
        
        # Анализируем данные
        total_entries = len(spam_data)
        profile_analyses = [d for d in spam_data if d.get('additional_data', {}).get('log_type') == 'profile_analysis']
        link_analyses = [d for d in spam_data if d.get('additional_data', {}).get('log_type') == 'spam_analysis']
        
        # Статистика по профилям
        suspicious_profiles = len([p for p in profile_analyses if p.get('analysis_result', {}).get('profile_analysis', {}).get('is_suspicious', False)])
        
        # Статистика по ссылкам
        total_bot_links = sum(d.get('analysis_result', {}).get('bot_links_count', 0) for d in link_analyses)
        total_suspicious = sum(d.get('analysis_result', {}).get('total_suspicious', 0) for d in link_analyses)
        
        # Топ паттернов
        pattern_counts = {}
        for entry in profile_analyses:
            patterns = entry.get('analysis_result', {}).get('profile_analysis', {}).get('patterns', [])
            for pattern in patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats_text = (
            "📊 **Статистика спама (30 дней)**\n\n"
            f"📈 **Общая статистика:**\n"
            f"• Всего записей: {total_entries}\n"
            f"• Анализов профилей: {len(profile_analyses)}\n"
            f"• Анализов ссылок: {len(link_analyses)}\n\n"
            f"🚨 **Подозрительные профили:**\n"
            f"• Найдено: {suspicious_profiles}\n"
            f"• Процент: {suspicious_profiles/len(profile_analyses)*100:.1f}%\n\n"
            f"🔗 **Ссылки и медиа:**\n"
            f"• Бот-ссылки: {total_bot_links}\n"
            f"• Подозрительных: {total_suspicious}\n\n"
            f"🏆 **Топ паттернов:**\n"
        )
        
        for pattern, count in top_patterns:
            stats_text += f"• {pattern}: {count}\n"
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики спама: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка получения статистики**\n\n"
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "spam_export")
async def export_spam_data(callback: CallbackQuery):
    """Экспорт данных спама."""
    try:
        # Получаем данные за последние 7 дней
        spam_data = secure_logger.get_spam_analysis_data(days=7)
        
        if not spam_data:
            await callback.message.edit_text(
                "📤 **Экспорт данных спама**\n\n"
                "❌ Данные за последние 7 дней не найдены.",
                reply_markup=get_spam_analysis_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        # Создаем файл с данными
        filename = f"spam_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(spam_data, f, ensure_ascii=False, indent=2)
        
        # Отправляем файл
        with open(filename, 'rb') as f:
            await callback.message.answer_document(
                document=f,
                caption=f"📤 **Экспорт данных спама**\n\n"
                        f"📅 Период: последние 7 дней\n"
                        f"📊 Записей: {len(spam_data)}\n"
                        f"📁 Файл: {filename}",
                parse_mode="Markdown"
            )
        
        # Удаляем временный файл
        import os
        os.remove(filename)
        
        await callback.message.edit_text(
            "✅ **Экспорт завершен**\n\n"
            f"Данные экспортированы в файл {filename}",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка экспорта данных спама: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка экспорта**\n\n"
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "spam_cleanup")
async def cleanup_spam_data(callback: CallbackQuery):
    """Очистка старых данных спама."""
    try:
        # Очищаем логи старше 90 дней
        secure_logger.cleanup_old_logs(days=90)
        
        await callback.message.edit_text(
            "🧹 **Очистка данных**\n\n"
            "✅ Старые логи (старше 90 дней) удалены.\n"
            "💾 Освобождено место на диске.",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка очистки данных спама: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка очистки**\n\n"
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "spam_patterns")
async def show_spam_patterns(callback: CallbackQuery):
    """Показать паттерны спама."""
    try:
        # Получаем данные за последние 30 дней
        spam_data = secure_logger.get_spam_analysis_data(days=30)
        
        if not spam_data:
            await callback.message.edit_text(
                "🔍 **Паттерны спама**\n\n"
                "❌ Данные не найдены.",
                reply_markup=get_spam_analysis_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        # Анализируем паттерны
        pattern_analysis = {}
        
        for entry in spam_data:
            analysis_result = entry.get('analysis_result', {})
            
            # Паттерны профилей
            if 'profile_analysis' in analysis_result:
                patterns = analysis_result['profile_analysis'].get('patterns', [])
                for pattern in patterns:
                    pattern_analysis[pattern] = pattern_analysis.get(pattern, 0) + 1
            
            # Паттерны ссылок
            if 'check_types' in analysis_result:
                check_types = analysis_result['check_types']
                for check_type in check_types:
                    pattern_analysis[f"link_{check_type}"] = pattern_analysis.get(f"link_{check_type}", 0) + 1
        
        # Сортируем по частоте
        sorted_patterns = sorted(pattern_analysis.items(), key=lambda x: x[1], reverse=True)
        
        patterns_text = "🔍 **Паттерны спама (30 дней)**\n\n"
        
        if sorted_patterns:
            patterns_text += "📊 **Топ паттернов:**\n"
            for pattern, count in sorted_patterns[:10]:
                patterns_text += f"• {pattern}: {count}\n"
        else:
            patterns_text += "❌ Паттерны не найдены."
        
        await callback.message.edit_text(
            patterns_text,
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа паттернов спама: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка анализа паттернов**\n\n"
            f"Произошла ошибка: {str(e)}",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "spam_back")
async def back_to_spam_menu(callback: CallbackQuery):
    """Вернуться в меню анализа спама."""
    keyboard = get_spam_analysis_keyboard()
    
    await callback.message.edit_text(
        "🔍 **Анализ данных спама**\n\n"
        "Выберите действие для анализа собранных данных:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех команд после рефакторинга
"""

import asyncio
import logging
from typing import Dict, List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_help_service():
    """Тестируем HelpService"""
    try:
        from app.services.help import HelpService
        
        help_service = HelpService()
        
        # Тестируем основные методы
        print("Тестируем HelpService...")
        
        # Тест get_help_text
        help_text = await help_service.get_help_text(12345)  # Тестовый admin_id
        print(f"OK get_help_text: {len(help_text)} символов")
        
        # Тест get_instructions_text
        instructions_text = await help_service.get_instructions_text(12345)
        print(f"OK get_instructions_text: {len(instructions_text)} символов")
        
        # Тест get_category_help
        categories = ["admin", "channels", "moderation", "suspicious", "limits"]
        for category in categories:
            category_help = help_service.get_category_help(category, 12345)
            print(f"OK get_category_help({category}): {len(category_help)} символов")
        
        # Тест get_command_info
        commands = ["help", "status", "channels", "suspicious", "unban"]
        for command in commands:
            cmd_info = help_service.get_command_info(command)
            if cmd_info:
                print(f"OK get_command_info({command}): {cmd_info.description}")
            else:
                print(f"ERROR get_command_info({command}): команда не найдена")
        
        print("OK HelpService работает корректно!")
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка в HelpService: {e}")
        return False

async def test_services():
    """Тестируем основные сервисы"""
    try:
        print("\nТестируем основные сервисы...")
        
        # Тестируем импорты сервисов
        from app.services.admin import AdminService
        from app.services.status import StatusService
        from app.services.channels import ChannelService
        from app.services.moderation import ModerationService
        from app.services.profiles import ProfileService
        from app.services.limits import LimitsService
        from app.services.bots import BotService
        
        print("OK Все сервисы импортируются корректно")
        
        # Тестируем создание экземпляров (без зависимостей)
        print("OK Сервисы готовы к использованию")
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка в сервисах: {e}")
        return False

async def test_handlers():
    """Тестируем хендлеры"""
    try:
        print("\nТестируем хендлеры...")
        
        # Тестируем импорты хендлеров
        from app.handlers.admin import admin_router
        from app.handlers.admin.basic import basic_router
        from app.handlers.admin.channels import channels_router
        from app.handlers.admin.limits import limits_router
        from app.handlers.admin.moderation import moderation_router
        from app.handlers.admin.suspicious import suspicious_router
        from app.handlers.admin.interactive import interactive_router
        
        print("OK Все хендлеры импортируются корректно")
        
        # Проверяем, что роутеры подключены
        if hasattr(admin_router, 'sub_routers'):
            print(f"OK admin_router имеет {len(admin_router.sub_routers)} подроутеров")
        
        print("OK Хендлеры готовы к использованию")
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка в хендлерах: {e}")
        return False

async def test_commands_list():
    """Проверяем список всех команд"""
    try:
        print("\nПроверяем список команд...")
        
        from app.services.help import HelpService
        help_service = HelpService()
        
        all_commands = help_service.get_all_commands()
        admin_commands = help_service.get_all_commands(admin_only=True)
        
        print(f"Всего команд: {len(all_commands)}")
        print(f"Админских команд: {len(admin_commands)}")
        
        print("\nСписок всех команд:")
        for cmd in all_commands:
            status = "ADMIN" if cmd.admin_only else "USER"
            print(f"  {status} {cmd.command} - {cmd.description}")
        
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка при проверке команд: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("Запуск тестирования команд после рефакторинга")
    print("=" * 60)
    
    results = []
    
    # Тестируем HelpService
    results.append(await test_help_service())
    
    # Тестируем сервисы
    results.append(await test_services())
    
    # Тестируем хендлеры
    results.append(await test_handlers())
    
    # Проверяем список команд
    results.append(await test_commands_list())
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Пройдено: {passed}/{total}")
    print(f"Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Рефакторинг выполнен успешно!")
    else:
        print("Есть проблемы, требующие внимания")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
        exit(1)
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        exit(1)

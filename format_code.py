#!/usr/bin/env python3
"""
Скрипт для форматирования кода проекта.
Использует black и isort для автоматического форматирования.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """Запустить команду и вернуть результат."""
    print(f"🔄 {description}...")
    try:
        # Используем python -m для запуска black и isort
        if command[0] in ["black", "isort"]:
            command = ["python", "-m"] + command

        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка:")
        print(e.stdout)
        print(e.stderr)
        return False


def main():
    """Основная функция форматирования."""
    print("🚀 Запуск форматирования кода...")

    # Определяем директории для форматирования
    directories = ["app", "tests", "bot.py"]

    # Форматирование с помощью black
    black_success = True
    for directory in directories:
        if Path(directory).exists():
            if not run_command(["black", directory], f"Форматирование {directory} с помощью black"):
                black_success = False

    # Форматирование с помощью isort
    isort_success = True
    for directory in directories:
        if Path(directory).exists():
            if not run_command(
                ["isort", "--profile", "black", directory],
                f"Сортировка импортов в {directory} с помощью isort",
            ):
                isort_success = False

    # Результат
    if black_success and isort_success:
        print("\n🎉 Форматирование завершено успешно!")
        print("💡 Теперь можно делать коммит с подробным описанием")
        return 0
    else:
        print("\n❌ Форматирование завершено с ошибками")
        return 1


if __name__ == "__main__":
    sys.exit(main())

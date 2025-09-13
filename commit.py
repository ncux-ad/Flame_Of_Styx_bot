#!/usr/bin/env python3
"""
Скрипт для удобного создания коммитов с подробными описаниями.
Сначала форматирует код, затем создает коммит.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str, check: bool = True) -> bool:
    """Запустить команду и вернуть результат."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            return True
        else:
            print(f"⚠️ {description} - предупреждение:")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка:")
        print(e.stdout)
        print(e.stderr)
        return False


def format_code():
    """Форматирование кода перед коммитом."""
    print("🚀 Форматирование кода...")

    # Определяем директории для форматирования
    directories = ["app", "tests", "bot.py"]

    # Форматирование с помощью black
    for directory in directories:
        if Path(directory).exists():
            run_command(
                ["black", directory],
                f"Форматирование {directory} с помощью black"
            )

    # Форматирование с помощью isort
    for directory in directories:
        if Path(directory).exists():
            run_command(
                ["isort", "--profile", "black", directory],
                f"Сортировка импортов в {directory} с помощью isort"
            )


def get_commit_message():
    """Получить сообщение коммита от пользователя."""
    print("\n📝 Введите сообщение коммита:")
    print("💡 Рекомендуемый формат:")
    print("   feat: добавить новую функцию")
    print("   fix: исправить ошибку")
    print("   docs: обновить документацию")
    print("   refactor: рефакторинг кода")
    print("   style: форматирование кода")
    print("   test: добавить тесты")
    print("   chore: обновить зависимости")
    print()

    message = input("Сообщение: ").strip()
    if not message:
        print("❌ Сообщение коммита не может быть пустым!")
        return None

    # Спросить о подробном описании
    print("\n📋 Хотите добавить подробное описание? (y/n): ", end="")
    if input().lower().startswith('y'):
        print("Введите подробное описание (завершите пустой строкой):")
        description_lines = []
        while True:
            line = input()
            if not line.strip():
                break
            description_lines.append(line)

        if description_lines:
            message += "\n\n" + "\n".join(description_lines)

    return message


def main():
    """Основная функция."""
    if len(sys.argv) > 1:
        # Если передано сообщение как аргумент
        message = " ".join(sys.argv[1:])
    else:
        # Форматируем код
        format_code()

        # Получаем сообщение от пользователя
        message = get_commit_message()
        if not message:
            return 1

    # Проверяем статус git
    print("\n🔍 Проверка статуса git...")
    if not run_command(["git", "status", "--porcelain"], "Проверка изменений", check=False):
        print("❌ Ошибка при проверке статуса git")
        return 1

    # Добавляем все изменения
    print("\n📦 Добавление изменений...")
    if not run_command(["git", "add", "."], "Добавление файлов в индекс"):
        return 1

    # Создаем коммит
    print(f"\n💾 Создание коммита: {message.split(chr(10))[0]}")
    if not run_command(["git", "commit", "-m", message], "Создание коммита"):
        return 1

    print("\n🎉 Коммит создан успешно!")
    print("💡 Для отправки в репозиторий используйте: git push")

    return 0


if __name__ == "__main__":
    sys.exit(main())

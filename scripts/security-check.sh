#!/bin/bash
# Скрипт для проверки безопасности проекта

set -e

echo "🔒 Запуск проверки безопасности..."

# Проверяем bandit
echo "📋 Запуск bandit (статический анализ безопасности)..."
bandit -r app/ -f json -o security-report.json -ll || true

# Проверяем safety
echo "📋 Запуск safety (проверка уязвимостей в зависимостях)..."
safety check --ignore 77745,77744,76752,77680,78162 --json > safety-report.json

echo "✅ Проверка безопасности завершена!"
echo "📊 Отчеты сохранены:"
echo "  - security-report.json (bandit)"
echo "  - safety-report.json (safety)"

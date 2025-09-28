# Скрипт для проверки безопасности проекта (PowerShell)

Write-Host "🔒 Запуск проверки безопасности..." -ForegroundColor Cyan

# Проверяем bandit
Write-Host "📋 Запуск bandit (статический анализ безопасности)..." -ForegroundColor Yellow
bandit -r app/ -f json -o security-report.json

# Проверяем safety
Write-Host "📋 Запуск safety (проверка уязвимостей в зависимостях)..." -ForegroundColor Yellow
safety check --ignore 77745,77744,76752,77680,78162 --json > safety-report.json

Write-Host "✅ Проверка безопасности завершена!" -ForegroundColor Green
Write-Host "📊 Отчеты сохранены:" -ForegroundColor Green
Write-Host "  - security-report.json (bandit)" -ForegroundColor White
Write-Host "  - safety-report.json (safety)" -ForegroundColor White

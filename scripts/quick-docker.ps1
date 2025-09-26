# 🚀 Быстрый запуск AntiSpam Bot в Docker (PowerShell)
# Простой скрипт для быстрого старта

Write-Host "🐳 Быстрый запуск AntiSpam Bot в Docker..." -ForegroundColor Blue

# Проверка Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker не установлен!" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose не установлен!" -ForegroundColor Red
    exit 1
}

# Проверка .env
if (-not (Test-Path .env)) {
    Write-Host "⚠️  .env файл не найден, создаю из примера..." -ForegroundColor Yellow
    Copy-Item env.example .env
    Write-Host "📝 Отредактируйте .env файл с вашими настройками!" -ForegroundColor Yellow
    Write-Host "   BOT_TOKEN=your_telegram_bot_token_here"
    Write-Host "   ADMIN_IDS=123456789,987654321"
    exit 1
}

# Сборка и запуск
Write-Host "🔨 Сборка Docker образа..." -ForegroundColor Green
docker-compose build

Write-Host "🚀 Запуск бота..." -ForegroundColor Green
docker-compose up -d antispam-bot

Write-Host "✅ Бот запущен!" -ForegroundColor Green
Write-Host "📋 Для просмотра логов: docker-compose logs -f antispam-bot" -ForegroundColor Cyan
Write-Host "🛑 Для остановки: docker-compose down" -ForegroundColor Cyan
Write-Host "🔧 Для входа в контейнер: docker-compose exec antispam-bot /bin/bash" -ForegroundColor Cyan

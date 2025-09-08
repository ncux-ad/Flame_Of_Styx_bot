# Скрипт для инициализации Git репозитория (PowerShell)
# Использование: .\scripts\init-git.ps1

Write-Host "🚀 Инициализация Git репозитория для AntiSpam Bot" -ForegroundColor Green

# Проверяем наличие Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git не установлен" -ForegroundColor Red
    exit 1
}

# Инициализируем Git репозиторий (если не инициализирован)
if (-not (Test-Path ".git")) {
    Write-Host "📁 Инициализация Git репозитория..." -ForegroundColor Yellow
    git init
}

# Добавляем remote origin (если не добавлен)
$remotes = git remote
if (-not $remotes -contains "origin") {
    Write-Host "🔗 Добавьте remote origin:" -ForegroundColor Yellow
    Write-Host "   git remote add origin https://github.com/your-username/antispam-bot.git" -ForegroundColor Cyan
    Write-Host "   git branch -M main" -ForegroundColor Cyan
}

# Добавляем все файлы
Write-Host "📝 Добавление файлов в Git..." -ForegroundColor Yellow
git add .

# Создаем первый коммит
Write-Host "💾 Создание первого коммита..." -ForegroundColor Yellow
git commit -m "🎉 Initial commit: AntiSpam Bot project setup

- ✅ Базовая архитектура aiogram 3.x
- ✅ Модели базы данных (SQLAlchemy)
- ✅ Сервисы для модерации и управления
- ✅ Обработчики и middleware
- ✅ DevOps инфраструктура (Docker, systemd)
- ✅ CI/CD с GitHub Actions
- ✅ Тестирование и линтеры
- ✅ Полная документация

Готово для разработки! 🚀"

# Создаем ветку develop
Write-Host "🌿 Создание ветки develop..." -ForegroundColor Yellow
git checkout -b develop

Write-Host "✅ Git репозиторий инициализирован!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Добавьте remote origin:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/your-username/antispam-bot.git" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Отправьте код на GitHub:" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host "   git push -u origin develop" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Настройте .env файл:" -ForegroundColor White
Write-Host "   Copy-Item env.example .env" -ForegroundColor Cyan
Write-Host "   # Отредактируйте .env файл" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Запустите локально:" -ForegroundColor White
Write-Host "   docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Или установите зависимости:" -ForegroundColor White
Write-Host "   pip install -e `"[dev]`"" -ForegroundColor Cyan
Write-Host "   python bot.py" -ForegroundColor Cyan

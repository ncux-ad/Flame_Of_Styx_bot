# Скрипт для настройки среды разработки (PowerShell)
# Использование: .\scripts\setup-dev.ps1

Write-Host "🛠️ Настройка среды разработки для AntiSpam Bot" -ForegroundColor Green

# Проверяем наличие Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python не установлен" -ForegroundColor Red
    exit 1
}

# Проверяем версию Python
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pythonVersion -lt [version]"3.11") {
    Write-Host "❌ Требуется Python 3.11+, установлен $pythonVersion" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python $pythonVersion найден" -ForegroundColor Green

# Создаем виртуальное окружение
if (-not (Test-Path "venv")) {
    Write-Host "🐍 Создание виртуального окружения..." -ForegroundColor Yellow
    python -m venv venv
}

# Активируем виртуальное окружение
Write-Host "🔌 Активация виртуального окружения..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Обновляем pip
Write-Host "📦 Обновление pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Устанавливаем зависимости
Write-Host "📚 Установка зависимостей..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Устанавливаем pre-commit
Write-Host "🔧 Настройка pre-commit..." -ForegroundColor Yellow
pre-commit install

# Создаем .env файл
if (-not (Test-Path ".env")) {
    Write-Host "⚙️ Создание .env файла..." -ForegroundColor Yellow
    Copy-Item env.example .env
    Write-Host "⚠️  Не забудьте настроить .env файл!" -ForegroundColor Yellow
}

# Создаем необходимые директории
Write-Host "📁 Создание директорий..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data", "logs" | Out-Null

Write-Host "✅ Среда разработки настроена!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Настройте .env файл:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Активируйте виртуальное окружение:" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Запустите тесты:" -ForegroundColor White
Write-Host "   pytest" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Запустите линтеры:" -ForegroundColor White
Write-Host "   black ." -ForegroundColor Cyan
Write-Host "   ruff check ." -ForegroundColor Cyan
Write-Host "   mypy app/" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Запустите бота:" -ForegroundColor White
Write-Host "   python bot.py" -ForegroundColor Cyan

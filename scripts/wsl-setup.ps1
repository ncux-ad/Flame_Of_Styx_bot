# PowerShell скрипт для настройки WSL
# Использование: .\scripts\wsl-setup.ps1

Write-Host "🐧 Настройка WSL для AntiSpam Bot" -ForegroundColor Green

# Проверяем права администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Запустите PowerShell от имени администратора" -ForegroundColor Red
    exit 1
}

# Проверяем WSL
Write-Host "🔍 Проверка WSL..." -ForegroundColor Yellow
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    Write-Host "✅ WSL уже установлен" -ForegroundColor Green
} else {
    Write-Host "📦 Установка WSL..." -ForegroundColor Yellow
    wsl --install -d Ubuntu-20.04
    Write-Host "⚠️  Перезагрузите компьютер после установки WSL" -ForegroundColor Yellow
    exit 0
}

# Проверяем Ubuntu
Write-Host "🔍 Проверка Ubuntu..." -ForegroundColor Yellow
$ubuntuInstalled = wsl -l -v | Select-String "Ubuntu"
if ($ubuntuInstalled) {
    Write-Host "✅ Ubuntu установлен" -ForegroundColor Green
} else {
    Write-Host "📦 Установка Ubuntu..." -ForegroundColor Yellow
    wsl --install -d Ubuntu-20.04
}

# Запускаем настройку в WSL
Write-Host "🚀 Запуск настройки в WSL..." -ForegroundColor Yellow
wsl -d Ubuntu-20.04 -e bash -c "cd /mnt/c/Soft/Bots/ad_anti_spam_bot_full && chmod +x scripts/setup-wsl.sh && ./scripts/setup-wsl.sh"

Write-Host "✅ WSL настроен для AntiSpam Bot!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Откройте WSL терминал: wsl" -ForegroundColor White
Write-Host "2. Перейдите в папку проекта: cd /mnt/c/Soft/Bots/ad_anti_spam_bot_full" -ForegroundColor White
Write-Host "3. Настройте .env файл: nano .env" -ForegroundColor White
Write-Host "4. Запустите бота: ./scripts/wsl-dev.sh" -ForegroundColor White

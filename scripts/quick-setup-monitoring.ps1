# Быстрая установка мониторинга на сервере (PowerShell)

param(
    [switch]$Help
)

# Функции для красивого вывода
function Write-Header {
    Write-Host "🚀 Quick Monitoring Setup for AntiSpam Bot" -ForegroundColor Blue
    Write-Host "==========================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️ $Message" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "🔧 $Message" -ForegroundColor Magenta
}

if ($Help) {
    Write-Host "Использование: .\quick-setup-monitoring.ps1"
    Write-Host ""
    Write-Host "Этот скрипт устанавливает мониторинг (Netdata + Uptime Kuma) для AntiSpam Bot"
    Write-Host ""
    Write-Host "Требования:"
    Write-Host "  - Docker и Docker Compose установлены"
    Write-Host "  - PowerShell 5.1 или выше"
    Write-Host "  - Права администратора для systemd"
    Write-Host ""
    exit 0
}

Write-Header

# Проверяем, что мы на сервере
if ($env:USER -eq "root") {
    Write-Error "Не запускайте скрипт от root! Используйте обычного пользователя."
    exit 1
}

# Проверяем Docker
try {
    $dockerVersion = docker --version 2>$null
    if (-not $dockerVersion) {
        throw "Docker не найден"
    }
    Write-Success "Docker найден: $dockerVersion"
} catch {
    Write-Error "Docker не установлен. Установите Docker сначала:"
    Write-Host "   curl -fsSL https://get.docker.com -o get-docker.sh"
    Write-Host "   sudo sh get-docker.sh"
    Write-Host "   sudo usermod -aG docker $env:USER"
    exit 1
}

# Проверяем Docker Compose
try {
    $composeVersion = docker-compose --version 2>$null
    if (-not $composeVersion) {
        throw "Docker Compose не найден"
    }
    Write-Success "Docker Compose найден: $composeVersion"
} catch {
    Write-Error "Docker Compose не установлен. Установите Docker Compose сначала."
    exit 1
}

# Проверяем, что мы в правильной директории
if (-not (Test-Path "bot.py")) {
    Write-Error "Запустите скрипт из корневой директории проекта!"
    exit 1
}

# Проверяем права на Docker
try {
    docker ps | Out-Null
    Write-Success "Права на Docker проверены"
} catch {
    Write-Error "Нет прав на Docker. Добавьте пользователя в группу docker:"
    Write-Host "   sudo usermod -aG docker $env:USER"
    Write-Host "   newgrp docker"
    exit 1
}

Write-Success "Проверки пройдены"

# Останавливаем бота
Write-Step "Останавливаем бота..."
try {
    $botStatus = systemctl is-active antispam-bot 2>$null
    if ($botStatus -eq "active") {
        sudo systemctl stop antispam-bot
        Write-Success "Бот остановлен"
    } else {
        Write-Info "Бот не был запущен"
    }
} catch {
    Write-Info "Бот не был запущен"
}

# Обновляем код
Write-Step "Обновляем код..."
try {
    git pull origin master
    Write-Success "Код обновлен"
} catch {
    Write-Error "Не удалось обновить код"
    exit 1
}

# Устанавливаем мониторинг
Write-Step "Устанавливаем мониторинг..."
if (Test-Path "scripts/setup-monitoring.ps1") {
    & ".\scripts\setup-monitoring.ps1"
} else {
    Write-Error "Скрипт setup-monitoring.ps1 не найден"
    exit 1
}

# Создаем systemd сервис
Write-Step "Настраиваем автозапуск..."
$serviceContent = @"
[Unit]
Description=Monitoring Services (Netdata + Uptime Kuma)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(Get-Location)/monitoring
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
"@

try {
    $serviceContent | sudo tee /etc/systemd/system/monitoring.service > $null
    sudo systemctl daemon-reload
    sudo systemctl enable monitoring.service
    sudo systemctl start monitoring.service
    Write-Success "Мониторинг настроен и запущен"
} catch {
    Write-Error "Не удалось настроить systemd сервис"
    exit 1
}

# Запускаем бота
Write-Step "Запускаем бота..."
try {
    sudo systemctl start antispam-bot
    Start-Sleep -Seconds 3
    Write-Success "Бот запущен"
} catch {
    Write-Error "Не удалось запустить бота"
}

# Проверяем статус
Write-Step "Проверяем статус..."
Write-Host ""
Write-Host "=== СТАТУС СЕРВИСОВ ===" -ForegroundColor Blue

try {
    sudo systemctl status antispam-bot --no-pager -l
} catch {
    Write-Error "Не удалось получить статус бота"
}

Write-Host ""
try {
    sudo systemctl status monitoring --no-pager -l
} catch {
    Write-Error "Не удалось получить статус мониторинга"
}

Write-Host ""

# Проверяем порты
Write-Host "=== ПРОВЕРКА ПОРТОВ ===" -ForegroundColor Blue
$serverIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne "127.0.0.1"} | Select-Object -First 1).IPAddress

try {
    $netdataPort = Get-NetTCPConnection -LocalPort 19999 -ErrorAction SilentlyContinue
    if ($netdataPort) {
        Write-Success "Netdata: http://${serverIP}:19999"
    } else {
        Write-Error "Netdata не запущен"
    }
} catch {
    Write-Error "Netdata не запущен"
}

try {
    $uptimePort = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
    if ($uptimePort) {
        Write-Success "Uptime Kuma: http://${serverIP}:3001"
    } else {
        Write-Error "Uptime Kuma не запущен"
    }
} catch {
    Write-Error "Uptime Kuma не запущен"
}

Write-Host ""
Write-Host "🎉 УСТАНОВКА ЗАВЕРШЕНА!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Доступ к мониторингу:" -ForegroundColor Cyan
Write-Host "  • Netdata: http://${serverIP}:19999" -ForegroundColor Green
Write-Host "  • Uptime Kuma: http://${serverIP}:3001" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Управление:" -ForegroundColor Cyan
Write-Host "  • Статус: sudo systemctl status monitoring" -ForegroundColor Yellow
Write-Host "  • Логи: cd monitoring && docker-compose logs -f" -ForegroundColor Yellow
Write-Host "  • Остановить: sudo systemctl stop monitoring" -ForegroundColor Yellow
Write-Host "  • Запустить: sudo systemctl start monitoring" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Следующие шаги:" -ForegroundColor Cyan
Write-Host "  1. Откройте Netdata и настройте алерты" -ForegroundColor Magenta
Write-Host "  2. Откройте Uptime Kuma и добавьте мониторинг бота" -ForegroundColor Magenta
Write-Host "  3. Настройте уведомления" -ForegroundColor Magenta
Write-Host ""
Write-Host "💡 Для SSH туннеля (рекомендуется):" -ForegroundColor Yellow
Write-Host "  ssh -L 19999:localhost:19999 -L 3001:localhost:3001 $env:USER@${serverIP}" -ForegroundColor Yellow
Write-Host "  Затем откройте http://localhost:19999 и http://localhost:3001" -ForegroundColor Yellow
Write-Host ""

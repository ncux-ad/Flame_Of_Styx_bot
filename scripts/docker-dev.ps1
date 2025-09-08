# 🐳 Docker Development Script для AntiSpam Bot (PowerShell)
# Быстрый запуск и управление Docker контейнерами

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Функции для вывода сообщений
function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Green
}

function Write-Warn($message) {
    Write-Host "[WARN] $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

# Проверка наличия Docker
function Test-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker не установлен!"
        exit 1
    }

    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose не установлен!"
        exit 1
    }
}

# Проверка .env файла
function Test-EnvFile {
    if (-not (Test-Path .env)) {
        Write-Warn ".env файл не найден, создаю из примера..."
        Copy-Item env.example .env
        Write-Warn "Отредактируйте .env файл с вашими настройками!"
        exit 1
    }
}

# Функция помощи
function Show-Help {
    Write-Host "🐳 Docker Development Script для AntiSpam Bot" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Использование: .\scripts\docker-dev.ps1 [команда]"
    Write-Host ""
    Write-Host "Команды:"
    Write-Host "  start     - Запустить бота в Docker"
    Write-Host "  stop      - Остановить бота"
    Write-Host "  restart   - Перезапустить бота"
    Write-Host "  build     - Собрать Docker образ"
    Write-Host "  logs      - Показать логи бота"
    Write-Host "  shell     - Войти в контейнер"
    Write-Host "  clean     - Очистить Docker ресурсы"
    Write-Host "  status    - Показать статус контейнеров"
    Write-Host "  help      - Показать эту справку"
    Write-Host ""
    Write-Host "Примеры:"
    Write-Host "  .\scripts\docker-dev.ps1 start          # Запустить бота"
    Write-Host "  .\scripts\docker-dev.ps1 logs -f        # Смотреть логи в реальном времени"
    Write-Host "  .\scripts\docker-dev.ps1 shell          # Войти в контейнер для отладки"
}

# Запуск бота
function Start-Bot {
    Write-Info "Запуск AntiSpam Bot в Docker..."
    docker-compose up -d antispam-bot
    Write-Info "Бот запущен! Используйте '.\scripts\docker-dev.ps1 logs' для просмотра логов"
}

# Остановка бота
function Stop-Bot {
    Write-Info "Остановка AntiSpam Bot..."
    docker-compose down
    Write-Info "Бот остановлен"
}

# Перезапуск бота
function Restart-Bot {
    Write-Info "Перезапуск AntiSpam Bot..."
    docker-compose restart antispam-bot
    Write-Info "Бот перезапущен"
}

# Сборка образа
function Build-Image {
    Write-Info "Сборка Docker образа..."
    docker-compose build --no-cache
    Write-Info "Образ собран"
}

# Просмотр логов
function Show-Logs {
    docker-compose logs @args
}

# Вход в контейнер
function Enter-Shell {
    Write-Info "Вход в контейнер AntiSpam Bot..."
    docker-compose exec antispam-bot /bin/bash
}

# Очистка Docker ресурсов
function Clear-DockerCache {
    Write-Info "Очистка Docker ресурсов..."
    docker-compose down -v
    docker system prune -f
    Write-Info "Очистка завершена"
}

# Статус контейнеров
function Show-Status {
    Write-Info "Статус контейнеров:"
    docker-compose ps
}

# Основная логика
function Main {
    Test-Docker
    Test-EnvFile

    switch ($Command.ToLower()) {
        "start" {
            Start-Bot
        }
        "stop" {
            Stop-Bot
        }
        "restart" {
            Restart-Bot
        }
        "build" {
            Build-Image
        }
        "logs" {
            Show-Logs @args
        }
        "shell" {
            Enter-Shell
        }
        "clean" {
            Clear-DockerCache
        }
        "status" {
            Show-Status
        }
        "help" {
            Show-Help
        }
        default {
            Write-Error "Неизвестная команда: $Command"
            Show-Help
            exit 1
        }
    }
}

# Запуск
Main

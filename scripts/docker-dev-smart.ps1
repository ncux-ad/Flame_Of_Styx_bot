# 🐳 Умный Docker Development Script для AntiSpam Bot (PowerShell)
# Пересобирает образ только при изменении зависимостей

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

# Проверка изменений в requirements.txt
function Test-RequirementsChanged {
    if (-not (Test-Path .docker-requirements-hash)) {
        return $true  # Файл не существует, нужно пересобрать
    }

    $currentHash = (Get-FileHash requirements.txt -Algorithm MD5).Hash
    $storedHash = Get-Content .docker-requirements-hash

    return $currentHash -ne $storedHash
}

# Обновление хеша requirements.txt
function Update-RequirementsHash {
    $hash = (Get-FileHash requirements.txt -Algorithm MD5).Hash
    $hash | Out-File -FilePath .docker-requirements-hash -Encoding ASCII
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

# Умная сборка образа
function Start-SmartBuild {
    if (Test-RequirementsChanged) {
        Write-Info "Обнаружены изменения в requirements.txt, пересобираю образ..."
        docker-compose build --no-cache
        Update-RequirementsHash
        Write-Info "Образ пересобран и хеш обновлен"
    } else {
        Write-Info "Зависимости не изменились, использую существующий образ"
    }
}

# Запуск бота
function Start-Bot {
    Write-Info "Запуск AntiSpam Bot в Docker..."
    Start-SmartBuild
    docker-compose up -d antispam-bot
    Write-Info "Бот запущен! Используйте '.\scripts\docker-dev-smart.ps1 logs' для просмотра логов"
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

# Принудительная пересборка
function Start-ForceBuild {
    Write-Info "Принудительная пересборка образа..."
    docker-compose build --no-cache
    Update-RequirementsHash
    Write-Info "Образ пересобран"
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
function Clear-Docker {
    Write-Info "Очистка Docker ресурсов..."
    docker-compose down -v
    docker system prune -f
    if (Test-Path .docker-requirements-hash) {
        Remove-Item .docker-requirements-hash
    }
    Write-Info "Очистка завершена"
}

# Статус контейнеров
function Show-Status {
    Write-Info "Статус контейнеров:"
    docker-compose ps
}

# Функция помощи
function Show-Help {
    Write-Host "🐳 Умный Docker Development Script для AntiSpam Bot" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Использование: .\scripts\docker-dev-smart.ps1 [команда]"
    Write-Host ""
    Write-Host "Команды:"
    Write-Host "  start     - Запустить бота (умная сборка)"
    Write-Host "  stop      - Остановить бота"
    Write-Host "  restart   - Перезапустить бота"
    Write-Host "  build     - Принудительная пересборка"
    Write-Host "  logs      - Показать логи бота"
    Write-Host "  shell     - Войти в контейнер"
    Write-Host "  clean     - Очистить Docker ресурсы"
    Write-Host "  status    - Показать статус контейнеров"
    Write-Host "  help      - Показать эту справку"
    Write-Host ""
    Write-Host "Особенности:"
    Write-Host "  - Образ пересобирается только при изменении requirements.txt"
    Write-Host "  - Код монтируется как volume для hot reload"
    Write-Host "  - Быстрый запуск при неизменных зависимостях"
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
            Start-ForceBuild
        }
        "logs" {
            Show-Logs @args
        }
        "shell" {
            Enter-Shell
        }
        "clean" {
            Clear-Docker
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

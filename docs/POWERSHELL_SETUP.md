# 🔧 Настройка PowerShell 7

## 📋 Что такое PowerShell 7?

PowerShell 7 - это кроссплатформенная версия PowerShell, которая работает на Windows, macOS и Linux. Она основана на .NET Core и предоставляет улучшенную производительность и функциональность по сравнению с Windows PowerShell 5.1.

## 🚀 Установка PowerShell 7

### Windows

#### Способ 1: Через Microsoft Store (рекомендуется)
1. Откройте Microsoft Store
2. Найдите "PowerShell"
3. Установите "PowerShell" (официальное приложение Microsoft)

#### Способ 2: Через winget
```powershell
winget install Microsoft.PowerShell
```

#### Способ 3: Через Chocolatey
```powershell
choco install powershell-core
```

#### Способ 4: Ручная установка
1. Перейдите на [GitHub PowerShell](https://github.com/PowerShell/PowerShell/releases)
2. Скачайте последнюю версию для Windows
3. Запустите установщик

### macOS

#### Через Homebrew
```bash
brew install --cask powershell
```

### Linux

#### Ubuntu/Debian
```bash
# Обновление списка пакетов
sudo apt-get update

# Установка зависимостей
sudo apt-get install -y wget apt-transport-https software-properties-common

# Добавление репозитория Microsoft
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb

# Установка PowerShell
sudo apt-get update
sudo apt-get install -y powershell
```

## ✅ Проверка установки

После установки проверьте версию:

```powershell
pwsh --version
```

Ожидаемый вывод:
```
PowerShell 7.4.0
```

## ⚙️ Настройка VS Code для PowerShell 7

### 1. Обновление settings.json

Файл `.vscode/settings.json` уже настроен для PowerShell 7:

```json
{
    "terminal.integrated.defaultProfile.windows": "PowerShell 7",
    "terminal.integrated.profiles.windows": {
        "PowerShell 7": {
            "path": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
            "icon": "terminal-powershell",
            "args": ["-NoLogo"]
        }
    }
}
```

### 2. Доступные задачи

В `.vscode/tasks.json` добавлены специальные задачи для PowerShell 7:

- **PowerShell 7: Run Bot** - Запуск бота через PowerShell 7
- **PowerShell 7: Docker Commands** - Docker команды через PowerShell 7

### 3. Конфигурации отладки

В `.vscode/launch.json` добавлена конфигурация:

- **PowerShell 7: Bot** - Отладка бота с PowerShell 7

## 🎯 Преимущества PowerShell 7

### Производительность
- **Быстрее** - основан на .NET Core
- **Меньше памяти** - оптимизирован для современных систем
- **Параллелизм** - лучше работает с асинхронными операциями

### Функциональность
- **Кроссплатформенность** - работает везде
- **Современный синтаксис** - улучшенные возможности
- **Лучшая интеграция** - с современными инструментами

### Для разработки
- **Docker интеграция** - лучшая поддержка Docker команд
- **Git интеграция** - улучшенная работа с Git
- **JSON поддержка** - встроенная работа с JSON

## 🔧 Настройка профиля PowerShell 7

### Создание профиля

```powershell
# Проверка существования профиля
Test-Path $PROFILE

# Создание профиля (если не существует)
New-Item -ItemType File -Path $PROFILE -Force

# Редактирование профиля
notepad $PROFILE
```

### Полезные настройки профиля

```powershell
# Установка алиасов
Set-Alias -Name ll -Value Get-ChildItem
Set-Alias -Name grep -Value Select-String

# Настройка автодополнения
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView

# Цветовая схема
Set-PSReadLineOption -Colors @{
    Command = 'Yellow'
    Parameter = 'Green'
    Operator = 'Magenta'
    Variable = 'Cyan'
    String = 'Blue'
}

# Функции для разработки
function Start-Bot {
    python bot.py
}

function Start-Docker {
    docker-compose up --build -d
}

function Stop-Docker {
    docker-compose down
}

function Show-Logs {
    docker logs antispam-bot -f
}
```

## 🐳 Работа с Docker в PowerShell 7

### Основные команды

```powershell
# Запуск контейнера
docker-compose up --build -d

# Остановка контейнера
docker-compose down

# Просмотр логов
docker logs antispam-bot -f

# Подключение к контейнеру
docker exec -it antispam-bot pwsh

# Просмотр статуса
docker-compose ps
```

### Полезные функции

```powershell
# Функция для быстрого перезапуска
function Restart-Bot {
    Write-Host "Останавливаю контейнер..." -ForegroundColor Yellow
    docker-compose down

    Write-Host "Пересобираю и запускаю..." -ForegroundColor Yellow
    docker-compose up --build -d

    Write-Host "Показываю логи..." -ForegroundColor Green
    docker logs antispam-bot -f
}

# Функция для очистки Docker
function Clean-Docker {
    Write-Host "Останавливаю все контейнеры..." -ForegroundColor Yellow
    docker stop $(docker ps -aq)

    Write-Host "Удаляю все контейнеры..." -ForegroundColor Yellow
    docker rm $(docker ps -aq)

    Write-Host "Удаляю неиспользуемые образы..." -ForegroundColor Yellow
    docker image prune -f

    Write-Host "Готово!" -ForegroundColor Green
}
```

## 🧪 Тестирование в PowerShell 7

### Запуск тестов

```powershell
# Все тесты
python -m pytest

# С покрытием
python -m pytest --cov=app

# Конкретный тест
python -m pytest tests/test_handlers.py::test_start_command

# С подробным выводом
python -m pytest -v
```

### Полезные функции для тестирования

```powershell
function Test-All {
    Write-Host "Запускаю все тесты..." -ForegroundColor Yellow
    python -m pytest --cov=app --cov-report=html
    Write-Host "Отчет о покрытии создан в htmlcov/" -ForegroundColor Green
}

function Test-Fast {
    Write-Host "Быстрые тесты..." -ForegroundColor Yellow
    python -m pytest tests/ -v --tb=short
}
```

## 🔍 Отладка в PowerShell 7

### VS Code интеграция

1. **Установите расширение PowerShell** для VS Code
2. **Настройте отладку** через `.vscode/launch.json`
3. **Используйте точки останова** в коде

### Командная строка

```powershell
# Запуск с отладкой
python -m pdb bot.py

# Запуск с профилированием
python -m cProfile bot.py
```

## 📚 Дополнительные ресурсы

### Официальная документация
- **[PowerShell 7 Documentation](https://docs.microsoft.com/en-us/powershell/)**
- **[PowerShell 7 Release Notes](https://docs.microsoft.com/en-us/powershell/scripting/whats-new/what-s-new-in-powershell-70)**
- **[PowerShell 7 Migration Guide](https://docs.microsoft.com/en-us/powershell/scripting/whats-new/migrating-from-windows-powershell-51-to-powershell-7)**

### Полезные модули
- **[PSReadLine](https://github.com/PowerShell/PSReadLine)** - Улучшенная командная строка
- **[PowerShellGet](https://docs.microsoft.com/en-us/powershell/scripting/gallery/overview)** - Менеджер пакетов
- **[PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer)** - Анализатор кода

### Сообщества
- **[PowerShell GitHub](https://github.com/PowerShell/PowerShell)**
- **[PowerShell Reddit](https://www.reddit.com/r/PowerShell/)**
- **[PowerShell Discord](https://discord.gg/powershell)**

## 🎯 Рекомендации для проекта

### 1. Используйте PowerShell 7 для:
- Запуска Docker команд
- Управления контейнерами
- Запуска тестов
- Отладки приложения

### 2. Настройте профиль с:
- Алиасами для частых команд
- Функциями для Docker
- Функциями для тестирования
- Цветовой схемой

### 3. Интегрируйте с VS Code:
- Используйте PowerShell 7 как терминал по умолчанию
- Настройте задачи для PowerShell 7
- Используйте отладку через PowerShell 7

---

**PowerShell 7 значительно улучшит ваш опыт разработки с Docker и Python!** 🚀

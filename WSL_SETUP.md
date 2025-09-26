# WSL Setup для AntiSpam Bot

Этот документ поможет настроить WSL (Windows Subsystem for Linux) для разработки AntiSpam Bot.

## 🚀 Быстрая настройка

### 1. Установка WSL

#### Автоматическая настройка (PowerShell)

```powershell
# В PowerShell от имени администратора
.\scripts\wsl-setup.ps1
```

#### Ручная настройка

```powershell
# В PowerShell от имени администратора
wsl --install
# или для конкретного дистрибутива
wsl --install -d Ubuntu-20.04
```

### 2. Настройка проекта в WSL

```bash
# В WSL терминале
cd /mnt/c/Soft/Bots/ad_anti_spam_bot_full

# Настройка WSL
chmod +x scripts/setup-wsl.sh
./scripts/setup-wsl.sh
```

### 3. Настройка .env файла

```bash
# Отредактируйте .env файл
nano .env
```

**Обязательно настройте:**
- `BOT_TOKEN` - токен вашего Telegram бота
- `ADMIN_IDS` - ID администраторов (через запятую)

## 🛠️ Разработка

### Запуск бота

```bash
# Прямой запуск
./scripts/wsl-dev.sh

# Или через Docker
./scripts/wsl-docker.sh up
```

### Полезные команды

```bash
# Активация виртуального окружения
source venv/bin/activate

# Линтеры
black .
ruff check .
mypy app/

# Тесты
pytest -v

# Pre-commit
pre-commit run --all-files

# Docker команды
./scripts/wsl-docker.sh help
```

## 🐳 Docker в WSL

### Основные команды

```bash
# Запуск
./scripts/wsl-docker.sh up

# Просмотр логов
./scripts/wsl-docker.sh logs

# Подключение к контейнеру
./scripts/wsl-docker.sh shell

# Остановка
./scripts/wsl-docker.sh down

# Очистка
./scripts/wsl-docker.sh clean
```

### Режим разработки

```bash
# Запуск с hot reload
./scripts/wsl-docker.sh dev
```

## 🔧 Настройка VS Code

### 1. Установка расширений

- WSL
- Python
- Docker
- GitLens
- Prettier
- ESLint

### 2. Настройка workspace

Создайте `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.blackEnabled": true,
    "python.linting.ruffEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "files.eol": "\n",
    "files.insertFinalNewline": true,
    "files.trimTrailingWhitespace": true
}
```

### 3. Настройка терминала

```json
{
    "terminal.integrated.defaultProfile.windows": "Ubuntu (WSL)",
    "terminal.integrated.profiles.windows": {
        "Ubuntu (WSL)": {
            "path": "wsl.exe",
            "args": ["-d", "Ubuntu-20.04"]
        }
    }
}
```

## 🐧 Системные требования

### WSL2
- Windows 10 версия 2004 и выше
- Windows 11
- Поддержка виртуализации

### Ubuntu 20.04 LTS
- Python 3.11+
- Git
- Docker (опционально)

## 🔍 Решение проблем

### Проблема с правами доступа

```bash
# Исправление прав доступа
chmod +x scripts/*.sh
```

### Проблема с Docker

```bash
# Проверка Docker
docker --version
docker-compose --version

# Перезапуск Docker Desktop
# В Windows: перезапустите Docker Desktop
```

### Проблема с Python

```bash
# Переустановка Python
sudo apt remove python3.11
sudo apt install python3.11 python3.11-venv python3.11-dev
```

### Проблема с Git

```bash
# Настройка Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config core.filemode false
```

## 📚 Дополнительные ресурсы

- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Docker Desktop WSL2](https://docs.docker.com/desktop/windows/wsl/)
- [VS Code WSL](https://code.visualstudio.com/docs/remote/wsl)
- [Python в WSL](https://docs.microsoft.com/en-us/windows/python/web-frameworks)

## 🎯 Следующие шаги

1. Настройте WSL и проект
2. Создайте Telegram бота через @BotFather
3. Настройте .env файл
4. Запустите бота: `./scripts/wsl-dev.sh`
5. Начните разработку!

---

**Примечание:** Этот проект оптимизирован для работы в WSL2 с Ubuntu 20.04 LTS.

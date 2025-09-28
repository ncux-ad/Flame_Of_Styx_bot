# Git Secrets Configuration

## 🔐 Обзор

Git Secrets - это инструмент для предотвращения случайного коммита секретов (токенов, паролей, ключей) в Git репозиторий.

## 📋 Установка

### Linux/macOS
```bash
# Ubuntu/Debian
sudo apt-get install git-secrets

# macOS
brew install git-secrets

# CentOS/RHEL
sudo yum install git-secrets

# Fedora
sudo dnf install git-secrets
```

### Windows
```powershell
# Через Chocolatey
choco install git-secrets

# Или используйте WSL
wsl --install
```

### Автоматическая установка
```bash
# Linux/macOS
make git-secrets

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/install-git-secrets.ps1
```

## ⚙️ Конфигурация

### 1. Инициализация
```bash
git secrets --install
```

### 2. Добавление паттернов
```bash
# Из файла .gitsecrets
git secrets --add 'pattern'

# Разрешенные паттерны (для тестов)
git secrets --add --allowed 'test_token_*'
```

### 3. Проверка конфигурации
```bash
git secrets --scan
```

## 🔍 Использование

### Сканирование файлов
```bash
# Текущие файлы
git secrets --scan

# Конкретный файл
git secrets --scan <file>

# История коммитов
git secrets --scan-history
```

### Make команды
```bash
# Установка Git Secrets
make git-secrets

# Сканирование секретов
make scan-secrets

# Сканирование истории
make scan-history
```

## 📝 Паттерны секретов

### Telegram Bot Tokens
```
[0-9]{8,10}:[A-Za-z0-9_-]{35}
```

### API Keys
```
api[_-]?key[_-]?[A-Za-z0-9]{20,}
secret[_-]?key[_-]?[A-Za-z0-9]{20,}
```

### Database URLs
```
postgresql://[^:]+:[^@]+@[^/]+/[^/]+
mysql://[^:]+:[^@]+@[^/]+/[^/]+
```

### JWT Tokens
```
eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*
```

### Private Keys
```
-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----
```

## ✅ Разрешенные паттерны

Для тестовых файлов и документации разрешены:
- `test_token_*` - тестовые токены
- `test_*` - тестовые значения
- `dummy_*` - заглушки
- `example_*` - примеры
- `your_*` - плейсхолдеры

## 🚨 GitHub Actions

Git Secrets автоматически запускается в GitHub Actions:
- При каждом push и pull request
- Еженедельно по расписанию
- Сканирует текущие файлы и историю коммитов

## 🔧 Pre-commit Hook

Автоматически устанавливается pre-commit hook:
```bash
#!/bin/bash
if ! git secrets --scan; then
    echo "❌ Git Secrets scan failed!"
    exit 1
fi
```

## 📊 Отчеты

GitHub Actions генерирует отчеты:
- `secrets-report.md` - детальный отчет
- Артефакт `git-secrets-report` - для скачивания

## 🛠️ Troubleshooting

### Ошибка "secrets were detected"
1. Проверьте, что секрет не является тестовым значением
2. Добавьте паттерн в разрешенные: `git secrets --add --allowed 'pattern'`
3. Удалите секрет из файла

### Ошибка "git-secrets: command not found"
1. Установите Git Secrets: `make git-secrets`
2. Проверьте PATH: `which git-secrets`

### Ложные срабатывания
1. Добавьте паттерн в разрешенные
2. Обновите `.gitsecrets` файл
3. Перезапустите конфигурацию

## 📚 Полезные ссылки

- [Git Secrets GitHub](https://github.com/awslabs/git-secrets)
- [Документация AWS](https://docs.aws.amazon.com/codecommit/latest/userguide/git-secrets.html)
- [Best Practices](https://github.com/awslabs/git-secrets#git-secrets)

## 🔒 Безопасность

Git Secrets помогает предотвратить:
- Утечку API ключей
- Коммит паролей
- Публикацию токенов
- Разглашение приватных ключей

**Помните:** Git Secrets - это дополнительная защита, но не замена хорошим практикам безопасности!

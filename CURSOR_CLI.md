# 🤖 Cursor CLI для Flame of Styx Bot

## 📋 Обзор

Cursor CLI установлен и настроен для работы с проектом Flame of Styx Bot через WSL Ubuntu. Это позволяет использовать мощные возможности Cursor AI для анализа кода, исправления багов и улучшения проекта.

## 🚀 Быстрый старт

### 1. Проверка установки
```powershell
.\cursor-cli.ps1 version
```

### 2. Вход в Cursor
```powershell
.\cursor-cli.ps1 login
```

### 3. Проверка статуса
```powershell
.\cursor-cli.ps1 status
```

## 📚 Доступные команды

### Основные команды
- `.\cursor-cli.ps1 help` - Показать справку
- `.\cursor-cli.ps1 version` - Версия Cursor CLI
- `.\cursor-cli.ps1 status` - Статус аутентификации
- `.\cursor-cli.ps1 login` - Войти в Cursor
- `.\cursor-cli.ps1 logout` - Выйти из Cursor

### Работа с AI
- `.\cursor-cli.ps1 agent "ваш запрос"` - Запустить Cursor Agent
- `.\cursor-cli.ps1 chat` - Создать новый чат
- `.\cursor-cli.ps1 resume [chatId]` - Продолжить чат

### Анализ проекта
- `.\cursor-cli.ps1 analyze app/handlers/admin.py` - Анализировать файл
- `.\cursor-cli.ps1 review` - Провести code review
- `.\cursor-cli.ps1 fix "описание проблемы"` - Исправить проблемы

### Обновление
- `.\cursor-cli.ps1 update` - Обновить Cursor CLI

## 💡 Примеры использования

### Анализ кода
```powershell
# Анализ конкретного файла
.\cursor-cli.ps1 analyze app/services/profiles.py

# Общий code review
.\cursor-cli.ps1 review
```

### Исправление проблем
```powershell
# Исправить ошибки типизации
.\cursor-cli.ps1 fix "Исправить ошибки типизации в проекте"

# Улучшить производительность
.\cursor-cli.ps1 fix "Оптимизировать производительность антиспам логики"
```

### Работа с AI
```powershell
# Задать вопрос о проекте
.\cursor-cli.ps1 agent "Как улучшить архитектуру проекта?"

# Получить помощь с конкретной задачей
.\cursor-cli.ps1 agent "Помоги написать тесты для ProfileService"
```

## 🔧 Технические детали

### Установка
Cursor CLI установлен в WSL Ubuntu по пути:
```
~/.local/share/cursor-agent/versions/2025.09.18-7ae6800/cursor-agent
```

### Симлинк
Создан симлинк в `~/.local/bin/cursor-agent` для удобного доступа.

### PowerShell интеграция
Создана функция `cursor-agent` в PowerShell профиле для прямого вызова.

### Вспомогательный скрипт
`cursor-cli.ps1` предоставляет удобные команды для работы с проектом.

## 🚨 Устранение проблем

### Проблема: "command not found"
```powershell
# Проверьте, что WSL запущен
wsl --list --verbose

# Перезапустите WSL
wsl --shutdown
wsl -d Ubuntu
```

### Проблема: "authentication required"
```powershell
# Войдите в Cursor
.\cursor-cli.ps1 login
```

### Проблема: "proxy configuration detected"
Это предупреждение WSL о прокси, но не влияет на работу Cursor CLI.

## 📖 Дополнительные ресурсы

- [Официальная документация Cursor](https://cursor.com/docs)
- [Cursor CLI GitHub](https://github.com/getcursor/cursor)
- [WSL документация](https://docs.microsoft.com/en-us/windows/wsl/)

## 🎯 Рекомендации по использованию

1. **Регулярно обновляйте** Cursor CLI: `.\cursor-cli.ps1 update`
2. **Используйте code review** перед коммитами: `.\cursor-cli.ps1 review`
3. **Анализируйте файлы** перед рефакторингом: `.\cursor-cli.ps1 analyze [файл]`
4. **Задавайте конкретные вопросы** для лучших результатов
5. **Сохраняйте контекст** в чатах для продолжения работы

---

*Создано: 2025-09-28*  
*Версия Cursor CLI: 2025.09.18-7ae6800*
